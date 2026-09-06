import json
import tempfile
import threading
import time
import unittest
from http.cookiejar import CookieJar
from http.server import ThreadingHTTPServer
from urllib.request import Request, build_opener, HTTPCookieProcessor
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs
from personal_agent.quickstart_store import QuickStore
from personal_agent.quickstart_service import AgentService
from personal_agent.quickstart import make_handler
from personal_agent.providers import ModelAdapter, ProviderError


class QuickstartTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=QuickStore(self.temp.name)
        self.calls=[]
        def transport(url,body,headers=None,timeout=60):
            self.calls.append((url,body,headers))
            if url.endswith('/api/chat'):return {'message':{'content':'Ollama response'}}
            if url.endswith('/chat/completions'):return {'choices':[{'message':{'content':'Compatible response'}}]}
            if url.endswith('/v1/messages'):return {'content':[{'type':'text','text':'Anthropic response'}]}
            if url.endswith('/getMe'):return {'ok':True,'result':{'username':'test_bot'}}
            if url.endswith('/getWebhookInfo'):return {'ok':True,'result':{'url':''}}
            if url.endswith('/getUpdates'):return {'ok':True,'result':[]}
            if url.endswith('/sendMessage'):return {'ok':True,'result':{'message_id':1}}
            raise AssertionError(url)
        self.transport=transport
        self.service=AgentService(self.store,ModelAdapter(transport),transport)

    def tearDown(self):self.temp.cleanup()

    def model(self,provider='ollama',endpoint='http://127.0.0.1:11434',key=''):
        self.service.save_model({'provider':provider,'endpoint':endpoint,'model':'test-model','api_key':key})

    def test_claim_session_restart_and_redaction(self):
        self.store.claim(self.store.bootstrap.read_text(),'a-long-test-password')
        self.assertFalse(self.store.bootstrap.exists())
        token=self.store.login('a-long-test-password')
        self.assertTrue(QuickStore(self.temp.name).session(token))
        self.assertIsNone(self.store.login('wrong'))
        self.model(key='private-api-key')
        self.assertNotIn('private-api-key',json.dumps(self.service.settings()))
        self.store.logout(token)
        self.assertFalse(self.store.session(token))

    def test_initial_claim_requires_local_code_and_is_single_use(self):
        code=self.store.bootstrap.read_text()
        with self.assertRaises(ValueError):self.store.claim('bad','long-test-password')
        self.store.claim(code,'long-test-password')
        with self.assertRaises(ValueError):self.store.claim(code,'different-password')

    def test_model_switch_preserves_history_but_not_keys_to_new_hosts(self):
        self.model(key='private-key')
        self.store.enqueue('hello','first')
        self.service.run_one()
        self.model('compatible','https://example.test/v1')
        self.assertEqual(self.store.secret('model_key'),'')
        self.store.enqueue('continue','second')
        self.service.run_one()
        self.assertEqual(len(self.store.history()),4)
        sent=self.calls[-1][1]['messages']
        self.assertIn('Ollama response',[m['content'] for m in sent])
        self.assertEqual(self.store.jobs()[0]['provider'],'compatible')

    def test_all_model_protocols(self):
        for provider,endpoint in [('ollama','http://localhost:11434'),('compatible','https://example.test/v1'),('anthropic','https://api.anthropic.com')]:
            self.model(provider,endpoint,'test-key')
            self.assertTrue(self.service.test_model()['ok'])
            self.assertTrue(self.service.settings()['model_test']['ok'])
        self.assertEqual(self.calls[-1][2]['anthropic-version'],'2023-06-01')

    def test_notes_work_without_model_and_summarize_with_model(self):
        self.store.enqueue('/note 회의: 금요일 출시 검토','note')
        self.service.run_one()
        self.store.enqueue('/notes','list')
        self.service.run_one()
        self.assertIn('금요일',self.store.jobs()[0]['response'])
        self.model()
        self.store.enqueue('/summarize','summary')
        self.service.run_one()
        self.assertTrue(any('금요일' in m.get('content','') for m in self.calls[-1][1]['messages'] if m['role']=='user'))
        self.assertEqual(len(QuickStore(self.temp.name).notes()),1)

    def test_idempotent_requests_and_interrupted_recovery(self):
        task=self.store.enqueue('hello','same')
        self.assertEqual(task,self.store.enqueue('hello','same'))
        with self.assertRaises(ValueError):self.store.enqueue('different','same')
        with self.store.db() as db:db.execute("UPDATE jobs SET status='running',delivery='sending'")
        self.store.recover()
        self.assertEqual(self.store.jobs()[0]['status'],'interrupted')
        self.assertEqual(self.store.jobs()[0]['delivery'],'unknown')
        self.assertFalse(self.service.run_one())

    def pair(self):
        link=self.service.connect_telegram({'token':'123456:TEST_TOKEN'})['url']
        code=parse_qs(urlsplit(link).query)['start'][0]
        cfg=self.store.config('telegram')
        self.service.ingest_update({'update_id':10,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'/start '+code}},cfg['generation'])
        return cfg['generation']

    def test_telegram_pairing_dedup_and_unauthorized_sender(self):
        generation=self.pair()
        self.assertEqual(self.store.config('telegram')['user_id'],42)
        self.assertNotIn('pair_code',json.dumps(self.service.settings()))
        self.service.run_one();self.service.deliver_one()
        update={'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'/note telegram note'}}
        self.service.ingest_update(update,generation);self.service.ingest_update(update,generation)
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':12,'message':{'from':{'id':99},'chat':{'id':99,'type':'private'},'text':'private data?'}},generation)
        self.assertEqual(len(self.store.jobs()),2)
        self.assertEqual(len(self.store.notes()),1)
        sends=[c for c in self.calls if c[0].endswith('/sendMessage')]
        self.assertEqual(len(sends),2)
        self.assertTrue(all(c[1]['chat_id']==42 for c in sends))
        self.assertNotIn('/start ',json.dumps(self.store.history()))

    def test_disconnect_cancels_outgoing_and_stale_updates(self):
        generation=self.pair()
        self.service.run_one()
        self.service.disconnect_telegram()
        self.service.deliver_one()
        self.assertEqual(self.store.jobs()[0]['delivery'],'cancelled')
        self.service.ingest_update({'update_id':20,'message':{}},generation)
        self.assertEqual(self.store.config('telegram')['cursor'],11)

    def test_ambiguous_send_not_automatically_repeated(self):
        self.pair();self.service.run_one()
        calls=[]
        def fail(*args,**kwargs):calls.append(1);raise ProviderError('timeout')
        self.service.telegram_transport=fail
        self.service.deliver_one();self.service.deliver_one()
        self.assertEqual(calls,[1])
        self.assertEqual(self.store.jobs()[0]['delivery'],'unknown')

    def test_group_chat_cannot_pair(self):
        self.service.connect_telegram({'token':'123456:TEST_TOKEN'})
        cfg=self.store.config('telegram')
        self.service.ingest_update({'update_id':1,'message':{'from':{'id':42},'chat':{'id':-42,'type':'group'},'text':'/start '+cfg['pair_code']}},cfg['generation'])
        self.assertIsNone(self.store.config('telegram')['user_id'])
        self.assertEqual(self.store.jobs(),[])

    def test_actual_router_model_and_free_catalog(self):
        from unittest.mock import patch
        from personal_agent.providers import ModelAdapter
        adapter=ModelAdapter(lambda *a,**kw:{'model':'test/actual:free','choices':[{'message':{'content':'hello'}}]})
        result=adapter.invoke({'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'},'test',[])
        self.assertEqual(result.model,'test/actual:free')
        with patch('personal_agent.quickstart_service.request_json',return_value={'data':[
            {'id':'good:free','pricing':{'prompt':'0','completion':'0'}},
            {'id':'paid:free','pricing':{'prompt':'1','completion':'0'}},
            {'id':'missing:free'}]}):
            self.assertEqual([m['id'] for m in self.service.free_models()['models']],['good:free'])

    def test_easy_model_connections(self):
        from unittest.mock import patch
        with patch('personal_agent.quickstart_service.request_json',return_value={'key':'test-only-key'}) as transport:
            self.service.connect_openrouter({'code':'test-code','verifier':'a'*64})
            self.assertEqual(self.store.config('model')['model'],'openrouter/free')
            self.assertEqual(self.store.secret('model_key'),'test-only-key')
            self.assertNotIn('test-only-key',str(self.service.settings()))
            self.assertEqual(transport.call_args.args[1]['code_challenge_method'],'S256')
        with patch('personal_agent.quickstart_service.request_json',return_value={'models':[{'name':'local-model','size':123},{}]}) as transport:
            self.assertEqual(self.service.local_models()['models'][0]['name'],'local-model')
            self.assertIsNone(transport.call_args.args[1])

    def test_optional_password_local_http(self):
        self.service.start()
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.service))
        thread=threading.Thread(target=server.serve_forever);thread.start()
        url='http://127.0.0.1:'+str(server.server_port)
        def post(path,body,headers=None):
            req=Request(url+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json',**(headers or {})})
            return build_opener().open(req,timeout=3)
        try:
            with self.assertRaises(HTTPError) as error:post('/api/claim',{}, {'Host':'evil.test'})
            self.assertEqual(error.exception.code,403)
            with post('/api/claim',{}) as r:self.assertEqual(r.status,200)
            self.assertTrue(self.store.config('local_access'))
            with self.assertRaises(HTTPError) as error:post('/api/local-login',{}, {'Origin':'https://evil.test'})
            self.assertEqual(error.exception.code,403)
            with post('/api/local-login',{}) as r:self.assertIn('HttpOnly',r.headers['Set-Cookie'])
        finally:
            self.service.stop.set();server.shutdown();thread.join();server.server_close()
            for worker in self.service.threads:worker.join(timeout=2)

    def test_http_setup_chat_csrf_and_logout(self):
        self.service.start()
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.service))
        thread=threading.Thread(target=server.serve_forever);thread.start()
        client=build_opener(HTTPCookieProcessor(CookieJar()))
        url='http://127.0.0.1:'+str(server.server_port)
        def request(path,body=None,headers=None):
            req=Request(url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
            with client.open(req,timeout=3) as response:return json.load(response)
        try:
            self.assertFalse(request('/api/status')['authenticated'])
            with self.assertRaises(HTTPError) as error:request('/api/state')
            self.assertEqual(error.exception.code,401)
            with self.assertRaises(HTTPError) as error:request('/api/claim',{'password':'long-password-test','code':self.store.bootstrap.read_text()},{'Origin':'https://evil.test'})
            self.assertEqual(error.exception.code,403)
            request('/api/claim',{'password':'long-password-test'})
            self.assertTrue(request('/api/status')['authenticated'])
            request('/api/chat',{'message':'/note HTTP proof','request_key':'http'})
            for _ in range(30):
                state=request('/api/state')
                if state['notes']:break
                time.sleep(.1)
            self.assertEqual(state['notes'][0]['content'],'HTTP proof')
            request('/api/logout',{})
            self.assertFalse(request('/api/status')['authenticated'])
        finally:
            self.service.stop.set();server.shutdown();thread.join();server.server_close()
            for worker in self.service.threads:worker.join(timeout=2)


if __name__=='__main__':unittest.main()
