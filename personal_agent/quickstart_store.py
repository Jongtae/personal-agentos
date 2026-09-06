"""Private, single-owner persistence for the quickstart."""
from contextlib import contextmanager
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import uuid


class QuickStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.private = self.root/'private'
        self.private.mkdir(exist_ok=True, mode=0o700)
        self.private.chmod(0o700)
        self.path = self.private/'quickstart.db'
        self.bootstrap = self.private/'bootstrap'
        self.secret_path = self.private/'connections.json'
        self.secret_lock = threading.RLock()
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS auth(id INTEGER PRIMARY KEY CHECK(id=1), salt TEXT, password TEXT);
            CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY, expires REAL);
            CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, channel TEXT, created REAL);
            CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, request_key TEXT UNIQUE, message TEXT, channel TEXT, chat_id INTEGER, status TEXT, response TEXT, error TEXT, delivery TEXT, provider TEXT, model TEXT, created REAL);
            CREATE TABLE IF NOT EXISTS tool_events(id INTEGER PRIMARY KEY AUTOINCREMENT, job_id TEXT, tool TEXT, status TEXT, detail TEXT, created REAL);
            CREATE TABLE IF NOT EXISTS notes(id TEXT PRIMARY KEY, content TEXT, created REAL);
            ''')
        self.path.chmod(0o600)
        if not self.claimed() and not self.bootstrap.exists():
            self.write_private(self.bootstrap, secrets.token_urlsafe(32))

    @contextmanager
    def db(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def write_private(path, content):
        tmp = path.with_name(path.name+'.tmp-'+secrets.token_hex(6))
        fd = os.open(tmp, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp, path)
        finally:
            if tmp.exists(): tmp.unlink()

    def claimed(self):
        with self.db() as db:
            return db.execute('SELECT 1 FROM auth').fetchone() is not None

    def claim(self, code, password, local_access=False):
        if not isinstance(password, str) or not 12 <= len(password) <= 256:
            raise ValueError('사용할 비밀번호를 12~256자로 입력하세요.')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM auth').fetchone():
                raise ValueError('이미 초기 설정이 완료되었습니다. 로그인하세요.')
            if not self.bootstrap.exists() or not hmac.compare_digest(str(code), self.bootstrap.read_text()):
                raise ValueError('초기 설정 링크가 올바르지 않습니다. 실행한 터미널에서 다시 여세요.')
            salt = secrets.token_hex(16)
            digest = hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
            db.execute('INSERT INTO auth VALUES (1,?,?)',(salt,digest))
            db.execute('INSERT INTO config VALUES (?,?)',('local_access',json.dumps(local_access)))
        self.bootstrap.unlink(missing_ok=True)

    def login(self, password):
        if not isinstance(password,str) or len(password)>256: return None
        with self.db() as db:
            row = db.execute('SELECT * FROM auth').fetchone()
            if not row: return None
            digest = hashlib.scrypt(password.encode(),salt=bytes.fromhex(row['salt']),n=16384,r=8,p=1).hex()
            if not hmac.compare_digest(digest,row['password']): return None
            token = secrets.token_urlsafe(32)
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES (?,?)',(hashlib.sha256(token.encode()).hexdigest(),time.time()+86400))
            return token

    def local_session(self):
        token=secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE expires<?',(time.time(),))
            db.execute('INSERT INTO sessions VALUES (?,?)',(hashlib.sha256(token.encode()).hexdigest(),time.time()+86400))
        return token

    def session(self, token):
        with self.db() as db:
            return db.execute('SELECT 1 FROM sessions WHERE token=? AND expires>?',(hashlib.sha256(token.encode()).hexdigest(),time.time())).fetchone() is not None

    def logout(self, token):
        with self.db() as db:
            db.execute('DELETE FROM sessions WHERE token=?',(hashlib.sha256(token.encode()).hexdigest(),))

    def config(self, key, default=None):
        with self.db() as db:
            row = db.execute('SELECT value FROM config WHERE key=?',(key,)).fetchone()
            return json.loads(row['value']) if row else default

    def put(self, key, value):
        with self.db() as db:
            db.execute('INSERT INTO config VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,json.dumps(value)))

    def secret(self, key, value=None):
        with self.secret_lock:
            values = json.loads(self.secret_path.read_text()) if self.secret_path.exists() else {}
            if value is not None:
                values[key] = value
                self.write_private(self.secret_path, json.dumps(values))
            return values.get(key,'')

    def enqueue(self, message, request_key, channel='web', chat_id=None, db=None):
        if not isinstance(message,str) or not message.strip() or len(message)>12000:
            raise ValueError('메시지는 1~12,000자로 입력하세요.')
        if not isinstance(request_key,str) or not 1<=len(request_key)<=160:
            raise ValueError('요청 식별자가 필요합니다.')
        if db is None:
            with self.db() as conn:
                conn.execute('BEGIN IMMEDIATE')
                return self.enqueue(message,request_key,channel,chat_id,conn)
        old=db.execute('SELECT * FROM jobs WHERE request_key=?',(request_key,)).fetchone()
        if old:
            if old['message']!=message or old['channel']!=channel or old['chat_id']!=chat_id:
                raise ValueError('같은 요청 식별자를 다른 메시지에 사용할 수 없습니다.')
            return old['id']
        if db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued','running')").fetchone()[0]>=100:
            raise ValueError('대기 중인 작업이 많습니다. 잠시 후 다시 시도하세요.')
        task_id=str(uuid.uuid4())
        db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',(task_id,request_key,message,channel,chat_id,'queued',None,None,'none',None,None,time.time()))
        return task_id

    def recover(self):
        with self.db() as db:
            db.execute("UPDATE jobs SET status='interrupted',error='실행 중 재시작되었습니다. 자동으로 재호출하지 않습니다.' WHERE status='running'")
            db.execute("UPDATE jobs SET delivery='unknown' WHERE delivery='sending'")

    def history(self):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM (SELECT * FROM messages ORDER BY id DESC LIMIT 100) ORDER BY id')]

    def jobs(self):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 40')]

    def notes(self):
        with self.db() as db:
            return [dict(r) for r in db.execute('SELECT * FROM notes ORDER BY created DESC LIMIT 50')]

    def recent_tool_events(self):
        with self.db() as db:
            return [dict(r) for r in db.execute("SELECT id,job_id,tool,status,created FROM tool_events WHERE tool!='model' ORDER BY id DESC LIMIT 30")]
