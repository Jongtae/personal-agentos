"""Exercise the installed Homebrew executable using disposable owner data."""
import json, secrets, socket, subprocess, tempfile, time
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, Request
from http.cookiejar import CookieJar

with tempfile.TemporaryDirectory() as tmp:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    client=build_opener(HTTPCookieProcessor(CookieJar()))
    def req(path,body=None):
        r=Request(url+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        with client.open(r,timeout=3) as response:return json.load(response)
    def start():
        p=subprocess.Popen(['agentos','start','--no-browser','--data',tmp,'--port',str(port)],stdout=subprocess.DEVNULL)
        for _ in range(100):
            try:
                if req('/healthz')['ok']:return p
            except OSError:pass
            time.sleep(.1)
        p.terminate();raise RuntimeError('server did not start')
    p=start()
    try:
        req('/api/claim',{'code':(Path(tmp)/'private/bootstrap').read_text(),'password':secrets.token_urlsafe(24)})
        req('/api/chat',{'message':'/note Installed Homebrew verification','request_key':'installed-proof'})
        for _ in range(50):
            state=req('/api/state')
            if state['notes']:break
            time.sleep(.1)
        assert state['notes'][0]['content']=='Installed Homebrew verification'
        second=subprocess.run(['agentos','start','--no-browser','--data',tmp,'--port',str(port+1)],capture_output=True,timeout=10)
        assert second.returncode==1
        p.terminate();p.wait(timeout=10);p=start()
        assert req('/api/state')['notes'][0]['content']=='Installed Homebrew verification'
        print(json.dumps({'installed_cli':True,'http_setup':True,'authenticated_note':True,'restart_persistence':True,'single_instance':True}))
    finally:p.terminate();p.wait(timeout=10)
