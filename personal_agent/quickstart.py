"""Launch a local personal agent and its browser setup, using only Python."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import secrets
import threading
import time
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from .quickstart_store import QuickStore
from .quickstart_service import AgentService
from .providers import ProviderError

WEB=Path(__file__).parent/'web'


def make_handler(service):
    store=service.store
    attempts=[]
    attempts_lock=threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(15)

        def log_message(self,*args):pass

        def reply(self,status,body,content_type='application/json; charset=utf-8',cookie=None):
            data=json.dumps(body,ensure_ascii=False).encode() if content_type.startswith('application/json') else body
            self.send_response(status)
            self.send_header('Content-Type',content_type)
            self.send_header('Content-Length',str(len(data)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            if cookie:self.send_header('Set-Cookie',cookie)
            self.end_headers()
            self.wfile.write(data)

        def token(self):
            cookie=SimpleCookie()
            try:cookie.load(self.headers.get('Cookie',''))
            except Exception:return ''
            return cookie['agentos_session'].value if 'agentos_session' in cookie else ''

        def auth(self):
            if store.session(self.token()):return True
            self.reply(401,{'error':'로그인이 필요합니다.'})
            return False

        def local_setup(self):
            return self.server.server_address[0] in ('127.0.0.1', '::1') and self.client_address[0] in ('127.0.0.1', '::1')

        def valid_host(self):
            if self.server.server_address[0] not in ('127.0.0.1', '::1'):return True
            allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}',f'[::1]:{self.server.server_port}'}
            if self.headers.get('Host') in allowed:return True
            self.reply(403,{'error':'로컬 주소로 AgentOS를 열어 주세요.'})
            return False

        def do_GET(self):
            if not self.valid_host():return
            path=urlsplit(self.path).path
            if path=='/healthz':return self.reply(200 if service.healthy() else 503,{'ok':service.healthy()})
            if path in ('/','/app.js','/style.css'):
                filename={'/':'index.html','/app.js':'app.js','/style.css':'style.css'}[path]
                mime={'/':'text/html; charset=utf-8','/app.js':'text/javascript; charset=utf-8','/style.css':'text/css; charset=utf-8'}[path]
                return self.reply(200,(WEB/filename).read_bytes(),mime)
            if path=='/api/status':
                return self.reply(200,{'claimed':store.claimed(),'authenticated':store.session(self.token()),'local_access':self.local_setup() and store.config('local_access',False)})
            if not self.auth():return
            if path=='/api/state':return self.reply(200,{'settings':service.settings(),'messages':store.history(),'jobs':store.jobs(),'notes':store.notes(),'healthy':service.healthy()})
            self.reply(404,{'error':'경로를 찾을 수 없습니다.'})

        def do_POST(self):
            if not self.valid_host():return
            origin=self.headers.get('Origin')
            if origin and (urlsplit(origin).netloc!=self.headers.get('Host') or urlsplit(origin).scheme not in ('http','https')):
                return self.reply(403,{'error':'다른 사이트에서의 요청은 허용하지 않습니다.'})
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':
                return self.reply(415,{'error':'JSON 요청이 필요합니다.'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536:raise ValueError('요청 크기가 올바르지 않습니다.')
                body=json.loads(self.rfile.read(length))
                if not isinstance(body,dict):raise ValueError('JSON 객체가 필요합니다.')
                path=urlsplit(self.path).path
                if path=='/api/local-login':
                    if not self.local_setup() or not store.config('local_access',False):
                        return self.reply(403,{'error':'이 환경에서는 로그인이 필요합니다.'})
                    token=store.local_session()
                    return self.reply(200,{'ok':True},cookie=f'agentos_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400')
                if path in ('/api/claim','/api/login'):
                    with attempts_lock:
                        attempts[:]=[t for t in attempts if t>time.time()-60]
                        if len(attempts)>=10:return self.reply(429,{'error':'로그인 시도가 많습니다. 1분 뒤 다시 시도하세요.'})
                        attempts.append(time.time())
                    if path=='/api/claim':
                        code=body.get('code','')
                        if self.local_setup() and store.bootstrap.exists():code=store.bootstrap.read_text()
                        password=body.get('password','')
                        local_access=not password and self.local_setup()
                        if local_access:password=secrets.token_urlsafe(32)
                        store.claim(code,password,local_access=local_access)
                        body['password']=password
                    token=store.login(body.get('password',''))
                    if not token:return self.reply(401,{'error':'비밀번호가 올바르지 않습니다.'})
                    secure='; Secure' if os.environ.get('AGENTOS_SECURE_COOKIE')=='1' else ''
                    return self.reply(200,{'ok':True},cookie=f'agentos_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400{secure}')
                if not self.auth():return
                if path=='/api/logout':
                    store.logout(self.token())
                    return self.reply(200,{'ok':True},cookie='agentos_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
                if path=='/api/model':return self.reply(200,service.save_model(body))
                if path=='/api/model/test':return self.reply(200,service.test_model())
                if path=='/api/telegram':return self.reply(200,service.connect_telegram(body))
                if path=='/api/telegram/pair':return self.reply(200,service.pair_telegram())
                if path=='/api/telegram/disconnect':return self.reply(200,service.disconnect_telegram())
                if path=='/api/chat':return self.reply(202,{'id':store.enqueue(body.get('message'),body.get('request_key'))})
                self.reply(404,{'error':'경로를 찾을 수 없습니다.'})
            except (ValueError,UnicodeDecodeError) as exc:self.reply(400,{'error':str(exc)})
            except ProviderError as exc:self.reply(502,{'error':str(exc)})
            except Exception:self.reply(500,{'error':'처리 중 오류가 발생했습니다. 저장소와 서버 상태를 확인하세요.'})
    return Handler


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',nargs='?',choices=['start'],default='start')
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8787)
    parser.add_argument('--data',default=os.environ.get('AGENTOS_DATA',str(Path.home()/'.local/share/agentos')))
    parser.add_argument('--no-browser',action='store_true')
    args=parser.parse_args()
    os.umask(0o077)
    store=QuickStore(args.data)
    instance_lock=(store.private/'instance.lock').open('a')
    try:fcntl.flock(instance_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:parser.exit(1,'이 데이터 폴더의 AgentOS가 이미 실행 중입니다.\n')
    service=AgentService(store)
    try:server=ThreadingHTTPServer((args.host,args.port),make_handler(service))
    except OSError as exc:parser.exit(1,f'시작할 수 없습니다: {exc}\n다른 포트는 --port로 지정하세요.\n')
    service.start()
    url=f'http://127.0.0.1:{server.server_port}/'
    if not store.claimed():url+='#setup='+store.bootstrap.read_text()
    store.write_private(store.private/'setup-link.txt',url)
    print(f'AgentOS: http://127.0.0.1:{server.server_port}/',flush=True)
    if not store.claimed():print(f'초기 설정 링크: {store.private / "setup-link.txt"} (개인 파일)',flush=True)
    if not args.no_browser:threading.Timer(.6,lambda:webbrowser.open(url)).start()
    def shutdown(signum,frame):
        service.stop.set()
        threading.Thread(target=server.shutdown,daemon=True).start()
    signal.signal(signal.SIGINT,shutdown)
    signal.signal(signal.SIGTERM,shutdown)
    try:server.serve_forever()
    finally:
        service.stop.set()
        server.server_close()
        for thread in service.threads:thread.join(timeout=2)


if __name__=='__main__':main()
