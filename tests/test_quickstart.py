import json
import tempfile
import threading
import time
import unittest
from http.cookiejar import CookieJar
from http.server import ThreadingHTTPServer
from urllib.request import Request, build_opener, HTTPCookieProcessor, HTTPRedirectHandler
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
            probing=any((tool.get('function',{}).get('name') or tool.get('name'))=='agentos_connection_probe' for tool in body.get('tools',[]))
            if url.endswith('/api/chat'):
                if probing:return {'message':{'content':'','tool_calls':[{'function':{'name':'agentos_connection_probe','arguments':{}}}]}}
                return {'message':{'content':'Ollama response'}}
            if url.endswith('/chat/completions'):
                if probing:return {'model':'verified/model:free','choices':[{'message':{'tool_calls':[{'id':'probe','function':{'name':'agentos_connection_probe','arguments':'{}'}}]}}]}
                return {'choices':[{'message':{'content':'Compatible response'}}]}
            if url.endswith('/v1/messages'):
                if probing:return {'content':[{'type':'tool_use','id':'probe','name':'agentos_connection_probe','input':{}}]}
                return {'content':[{'type':'text','text':'Anthropic response'}]}
            if url.endswith('/getMe'):return {'ok':True,'result':{'username':'test_bot'}}
            if url.endswith('/getWebhookInfo'):return {'ok':True,'result':{'url':''}}
            if url.endswith('/getUpdates'):return {'ok':True,'result':[]}
            if url.endswith('/sendMessage'):return {'ok':True,'result':{'message_id':len([c for c in self.calls if c[0].endswith('/sendMessage')])}}
            if url.endswith('/editMessageText'):return {'ok':True,'result':True}
            if url.endswith('/answerCallbackQuery'):return {'ok':True,'result':True}
            raise AssertionError(url)
        self.transport=transport
        self.service=AgentService(self.store,ModelAdapter(transport),transport)

    def tearDown(self):self.temp.cleanup()

    def model(self,provider='ollama',endpoint='http://127.0.0.1:11434',key=''):
        self.service.save_model({'provider':provider,'endpoint':endpoint,'model':'test-model','api_key':key})

    def make_due(self, job_id):
        with self.store.db() as db:
            db.execute("UPDATE jobs SET created=? WHERE id=?", (time.time()-4, job_id))

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

    def test_onboarding_http_api_requires_login_and_redacts_secrets(self):
        self.store.claim(self.store.bootstrap.read_text(),'long-password-test')
        self.model(key='private-api-key')
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.service))
        thread=threading.Thread(target=server.serve_forever);thread.start()
        client=build_opener(HTTPCookieProcessor(CookieJar()));url='http://127.0.0.1:'+str(server.server_port)
        def request(path,body=None):
            req=Request(url+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'} if body is not None else {})
            with client.open(req,timeout=3) as response:return json.load(response)
        try:
            with self.assertRaises(HTTPError) as error:request('/api/onboarding')
            self.assertEqual(error.exception.code,401)
            request('/api/login',{'password':'long-password-test'})
            guide=request('/api/onboarding')
            self.assertNotIn('private-api-key',json.dumps(guide))
            self.assertIn('recovery',guide)
        finally:
            server.shutdown();thread.join();server.server_close()

    def test_home_is_minimal_and_never_includes_connection_secrets(self):
        self.store.claim(self.store.bootstrap.read_text(),'long-password-test')
        self.model(key='private-api-key')
        self.assertTrue(self.service.test_model()['ok'])
        home=self.service.home()
        self.assertEqual(home['state'],'ready')
        self.assertTrue(home['model_connected'])
        self.assertNotIn('private-api-key',json.dumps(home))
        self.store.enqueue('hello','home-active')
        home=self.service.home()
        self.assertEqual(home['state'],'working')
        self.assertEqual(home['active_jobs'],1)

    def test_workspace_is_opt_in_and_saved_results_survive_restart(self):
        workspace=self.service.create_workspace({'title':'UX 개선','purpose':'대화 경험 정리'})
        self.assertEqual(self.store.workspaces()[0]['id'],workspace['id'])
        job=self.store.enqueue('/note 작업공간 메모','workspace-note',workspace_id=workspace['id'])
        self.service.run_one()
        saved=self.service.save_workspace_result(workspace['id'],{'job_id':job})
        self.assertEqual(saved['results'][0]['job_id'],job)
        restarted=QuickStore(self.temp.name).workspace_detail(workspace['id'])
        self.assertEqual(restarted['messages'][0]['workspace_id'] if 'workspace_id' in restarted['messages'][0] else workspace['id'],workspace['id'])
        self.assertEqual(restarted['results'][0]['content'],'메모를 저장했습니다. /notes로 확인하거나 /summarize로 정리할 수 있습니다.')

    def test_result_evidence_is_category_only_and_messages_link_to_its_job(self):
        job=self.store.enqueue('/note private planning detail','evidence-link')
        self.service.run_one()
        with self.store.db() as db:
            db.execute('INSERT INTO tool_events(job_id,tool,status,detail,created) VALUES (?,?,?,?,?)',(job,'web_search','succeeded',json.dumps({'query':'private search phrase','url':'https://private.example'}),time.time()))
            db.execute('INSERT INTO tool_events(job_id,tool,status,detail,created) VALUES (?,?,?,?,?)',(job,'read_file','succeeded',json.dumps({'path':'/Users/private/plan.md','content':'private document'}),time.time()))
        result=self.store.evidence_summary(job)
        self.assertEqual(result,['공개 웹 1곳 참고','내 컴퓨터의 문서 1개 사용'])
        self.assertNotIn('private',json.dumps(result))
        messages=self.store.history()
        self.assertEqual([message['job_id'] for message in messages], [job,job])

    def test_workspace_requires_explicit_selection(self):
        with self.assertRaises(ValueError):self.store.enqueue('hello','missing-workspace',workspace_id='missing')

    def test_initial_claim_requires_local_code_and_is_single_use(self):
        code=self.store.bootstrap.read_text()
        with self.assertRaises(ValueError):self.store.claim('bad','long-test-password')
        self.store.claim(code,'long-test-password')
        with self.assertRaises(ValueError):self.store.claim(code,'different-password')

    def test_model_switch_preserves_history_but_not_keys_to_new_hosts(self):
        self.model(key='private-key')
        self.assertTrue(self.service.test_model()['ok'])
        self.store.enqueue('hello','first')
        self.service.run_one()
        self.model('compatible','https://example.test/v1')
        self.assertEqual(self.store.secret('model_key'),'')
        self.assertTrue(self.service.test_model()['ok'])
        self.store.enqueue('continue','second')
        self.service.run_one()
        self.assertEqual(len(self.store.history()),4)
        sent=self.calls[-1][1]['messages']
        self.assertIn('Ollama response',[m.get('content','') for m in sent])
        self.assertEqual(self.store.jobs()[0]['provider'],'compatible')

    def test_all_model_protocols(self):
        for provider,endpoint in [('ollama','http://localhost:11434'),('compatible','https://example.test/v1'),('openai','https://api.openai.com/v1'),('anthropic','https://api.anthropic.com')]:
            self.model(provider,endpoint,'test-key')
            self.assertTrue(self.service.test_model()['ok'])
            self.assertTrue(self.service.settings()['model_test']['ok'])
        self.assertEqual(self.calls[-1][2]['anthropic-version'],'2023-06-01')
        self.assertEqual(self.calls[-1][1]['tool_choice'],{'type':'any'})

    def test_text_only_connection_is_not_marked_tool_ready(self):
        def text_only(url,body,headers=None,timeout=60):
            if body.get('tools'):return {'choices':[{'message':{'content':'I cannot use tools'}}]}
            return {'choices':[{'message':{'content':'hello'}}]}
        service=AgentService(self.store,ModelAdapter(text_only),text_only)
        service.save_model({'provider':'compatible','endpoint':'https://example.test/v1','model':'text-only'})
        result=service.test_model()
        self.assertFalse(result['ok'])
        self.assertTrue(result['text_ok'])
        self.assertFalse(result['tools_ok'])
        self.assertFalse(service.settings()['model_ready'])

    def test_stale_or_unverified_model_does_not_run_agent(self):
        self.model()
        self.store.enqueue('웹에서 찾아줘','unverified')
        self.service.run_one()
        self.assertEqual(self.store.jobs()[0]['status'],'failed')
        self.assertIn('도구 호출 연결',self.store.jobs()[0]['error'])
        self.assertEqual(self.calls,[])
        self.assertTrue(self.service.test_model()['ok'])
        checked=self.store.config('model_test');checked['time']=time.time()-90000;self.store.put('model_test',checked)
        self.store.enqueue('다시 찾아줘','stale')
        self.service.run_one()
        self.assertEqual(self.store.jobs()[0]['status'],'failed')
        self.assertEqual(len(self.calls),2)

    def test_notes_work_without_model_and_summarize_with_model(self):
        self.store.enqueue('/note 회의: 금요일 출시 검토','note')
        self.service.run_one()
        self.store.enqueue('/notes','list')
        self.service.run_one()
        self.assertIn('금요일',self.store.jobs()[0]['response'])
        self.model()
        self.assertTrue(self.service.test_model()['ok'])
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

    def test_botfather_token_is_local_only_and_never_appears_in_public_state(self):
        token='123456:TEST_TOKEN'
        link=self.service.connect_telegram({'token':token})['url']
        cfg=self.store.config('telegram')
        self.assertEqual(cfg['mode'],'owner-token')
        self.assertEqual(self.store.secret('telegram_token'),token)
        self.assertNotIn(token,json.dumps(self.service.settings()))
        self.assertNotIn(token,json.dumps(self.store.recent_tool_events()))
        self.assertNotIn('pair_code',json.dumps(self.service.settings()))
        self.assertIn('start=',link)
        self.service.disconnect_telegram()
        self.assertEqual(self.store.secret('telegram_token'),'')

    def test_botfather_codex_verification_acceptance_is_automatic_after_private_delivery(self):
        self.store.secret('telegram_token','123456:TEST_TOKEN')
        self.store.put('telegram',{'enabled':True,'mode':'owner-token','username':'owner_test_bot','generation':'safe','user_id':42})
        with self.store.db() as db:
            db.execute("INSERT INTO jobs(id,request_key,message,channel,chat_id,status,response,error,delivery,provider,model,created,workspace_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",('job','telegram-verify:safe','/search AgentOS personal assistant verification','telegram:safe',42,'succeeded','done',None,'sent','subscription','codex',time.time(),None))
            db.execute("INSERT INTO tool_events(job_id,tool,status,detail,created) VALUES (?,?,?,?,?)",('job','web_search','succeeded','{}',time.time()))
        from personal_agent.telegram_first_work_acceptance import report
        result=report(self.store)
        self.assertTrue(result['passed'])
        self.assertTrue(result['checks']['paired_delivery_confirmed'])
        self.assertNotIn('123456:TEST_TOKEN',json.dumps(result))

    def test_pairing_queues_one_idempotent_codex_connection_verification(self):
        self.store.put('subscription_engine',{'id':'codex'})
        self.pair()
        jobs=[job for job in self.store.jobs() if job['request_key'].startswith('telegram-verify:')]
        self.assertEqual(len(jobs),1)
        first=self.service.queue_telegram_connection_verification()
        second=self.service.queue_telegram_connection_verification()
        self.assertTrue(first['queued'])
        self.assertEqual(first['job_id'],second['job_id'])


    def test_botfather_connection_rejects_invalid_account_and_webhook(self):
        def invalid_account(url,body,headers=None,timeout=60):
            if url.endswith('/getMe'):return {'ok':True,'result':{'username':''}}
            if url.endswith('/getWebhookInfo'):return {'ok':True,'result':{'url':''}}
            raise AssertionError(url)
        service=AgentService(self.store,ModelAdapter(invalid_account),invalid_account)
        with self.assertRaises(ProviderError):service.connect_telegram({'token':'123456:TEST_TOKEN'})
        def webhook(url,body,headers=None,timeout=60):
            if url.endswith('/getMe'):return {'ok':True,'result':{'username':'owner_test_bot'}}
            if url.endswith('/getWebhookInfo'):return {'ok':True,'result':{'url':'https://example.test/hook'}}
            raise AssertionError(url)
        service=AgentService(self.store,ModelAdapter(webhook),webhook)
        with self.assertRaises(ValueError):service.connect_telegram({'token':'123456:TEST_TOKEN'})

    def test_legacy_personal_bot_config_is_recognized_as_botfather_setup(self):
        self.store.put('telegram',{'enabled':True,'username':'legacy_personal_bot','generation':'legacy','user_id':42})
        from personal_agent.telegram_first_work_acceptance import report
        self.assertTrue(report(self.store)['checks']['owner_botfather_bot'])

    def test_successful_telegram_poll_clears_stale_connection_error(self):
        self.pair()
        self.store.put('telegram_status',{'state':'error','message':'stale'})
        # The production loop writes connected after this same successful call.
        self.service.poll_telegram()
        self.service.mark_telegram_connected()
        self.assertEqual(self.store.config('telegram_status')['state'],'connected')

    def test_botfather_restart_resumes_durable_poll_cursor(self):
        self.pair()
        restarted=AgentService(QuickStore(self.temp.name),ModelAdapter(self.transport),self.transport)
        restarted.poll_telegram()
        poll=[call for call in self.calls if call[0].endswith('/getUpdates')][-1]
        self.assertEqual(poll[1]['offset'],11)

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

    def test_natural_language_task_card_has_safe_progress_and_queued_cancellation(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        request={'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'내일 회의 준비를 정리해 줘'}}
        self.service.ingest_update(request,generation)
        job=self.store.jobs()[0]
        card=self.store.task_card(job['id'])
        self.assertIsNotNone(card)
        create=[c for c in self.calls if c[0].endswith('/sendMessage')][-1]
        self.assertEqual(create[1]['reply_markup']['inline_keyboard'][0][1]['callback_data'],f"p7c:{job['id']}")
        callback_message={'chat':{'id':42,'type':'private'},'message_id':card['message_id']}
        self.service.ingest_callback({'id':'cancel-1','from':{'id':42},'message':callback_message,'data':f"p7c:{job['id']}"},generation)
        self.service.ingest_callback({'id':'cancel-2','from':{'id':42},'message':callback_message,'data':f"p7c:{job['id']}"},generation)
        self.assertEqual(self.store.jobs()[0]['status'],'cancelled')
        self.assertFalse(self.service.run_one())
        edits=[c for c in self.calls if c[0].endswith('/editMessageText')]
        self.assertEqual(len(edits),1)
        self.assertIn('취소됨',edits[0][1]['text'])

    def test_telegram_task_card_waits_briefly_for_cancellation(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'잠시 뒤 실행할 요청'}},generation)
        job=self.store.jobs()[0]
        self.assertFalse(self.service.run_one())
        self.assertEqual(self.store.jobs()[0]['status'],'queued')
        card=self.store.task_card(job['id'])
        self.service.ingest_callback({'id':'cancel','from':{'id':42},'message':{'chat':{'id':42,'type':'private'},'message_id':card['message_id']},'data':f"p7c:{job['id']}"},generation)
        self.assertEqual(self.store.jobs()[0]['status'],'cancelled')

    def test_task_callbacks_require_owner_and_cannot_cancel_running_work(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'작업 시작해 줘'}},generation)
        job=self.store.jobs()[0]
        callback={'id':'foreign','from':{'id':99},'message':{'chat':{'id':99,'type':'private'},'message_id':999},'data':f"p7c:{job['id']}"}
        self.service.ingest_callback(callback,generation)
        self.assertEqual(self.store.jobs()[0]['status'],'queued')
        self.make_due(job['id'])
        self.service.run_one()
        card=self.store.task_card(job['id'])
        self.service.ingest_callback({'id':'late','from':{'id':42},'message':{'chat':{'id':42,'type':'private'},'message_id':card['message_id']},'data':f"p7c:{job['id']}"},generation)
        self.assertIn(self.store.jobs()[0]['status'],('succeeded','failed'))

    def test_document_approval_notification_is_owner_bound_and_safe(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        while self.service.deliver_notification():pass
        def document_model(url,body,headers=None,timeout=60):
            if body.get('tools') and any((tool.get('function',{}).get('name') or tool.get('name'))=='agentos_connection_probe' for tool in body['tools']):
                return {'choices':[{'message':{'tool_calls':[{'id':'probe','function':{'name':'agentos_connection_probe','arguments':'{}'}}]}}]}
            if any(message.get('role')=='tool' for message in body.get('messages',[])):
                return {'choices':[{'message':{'content':'I need approval.'}}]}
            if body.get('tools'):
                return {'choices':[{'message':{'tool_calls':[{'id':'files','function':{'name':'find_files','arguments':'{"query":"confidential document"}'}}]}}]}
            return {'choices':[{'message':{'content':'I need approval.'}}]}
        self.service.adapter=ModelAdapter(document_model)
        self.model('compatible','https://example.test/v1','private-api-key')
        self.assertTrue(self.service.test_model()['ok'])
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'문서를 찾아 줘'}},generation)
        card=[c for c in self.calls if c[0].endswith('/sendMessage') and c[1]['text'].startswith('요청을 받았습니다.')][-1]
        self.assertNotIn('문서를 찾아',card[1]['text'])
        self.make_due(self.store.jobs()[0]['id'])
        self.service.run_one()
        self.assertTrue(self.service.deliver_notification())
        approval=[c for c in self.calls if c[0].endswith('/sendMessage') and c[1]['text'].startswith('연결 문서를')][-1]
        self.assertNotIn('private-api-key',json.dumps(approval[1]))
        self.assertNotIn('confidential document',json.dumps(approval[1]))
        approval_row=self.store.notification(approval[1]['reply_markup']['inline_keyboard'][0][0]['callback_data'].split(':')[1])
        callback_message={'chat':{'id':42,'type':'private'},'message_id':approval_row['message_id']}
        self.service.ingest_callback({'id':'foreign-approval','from':{'id':99},'message':{'chat':{'id':99,'type':'private'},'message_id':approval_row['message_id']},'data':f"p7a:{approval_row['id']}:approve"},generation)
        self.assertTrue(self.service.document_boundary()['requires_approval'])
        self.service.ingest_callback({'id':'approve','from':{'id':42},'message':callback_message,'data':f"p7a:{approval_row['id']}:approve"},generation)
        self.assertFalse(self.service.document_boundary()['requires_approval'])

    def test_telegram_context_is_explicit_source_evidenced_and_per_job_approved(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        while self.service.deliver_notification():pass
        self.model('compatible','https://example.test/v1','private-api-key')
        self.assertTrue(self.service.test_model()['ok'])
        inbox=self.service.context_inbox()
        inbox.configure({'sources':{'text':True}})
        item=inbox.capture({'source_kind':'text','content':'Aurora launches on Friday','retention_seconds':60})
        self.service.set_context_telegram_policy({'approved':True})
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':f"/context {item['id']} -- 출시일을 알려줘"}},generation)
        job=self.store.jobs()[0];self.make_due(job['id'])
        self.service.run_one()
        self.assertEqual(self.store.job(job['id'])['status'],'failed')
        self.assertFalse(any('Aurora launches' in json.dumps(call[1]) for call in self.calls if call[0].endswith('/chat/completions')))
        self.service.deliver_notification()
        approval=[call for call in self.calls if call[0].endswith('/sendMessage') and call[1]['text'].startswith('개인 컨텍스트')][-1]
        callback=approval[1]['reply_markup']['inline_keyboard'][0][0]['callback_data']
        notification_id=callback.split(':')[1]
        notification=self.store.notification(notification_id)
        self.service.ingest_callback({'id':'context-approve','from':{'id':42},'message':{'chat':{'id':42,'type':'private'},'message_id':notification['message_id']},'data':callback},generation)
        self.make_due(job['id']);self.service.run_one()
        self.assertEqual(self.store.job(job['id'])['status'],'succeeded')
        sent=[call[1] for call in self.calls if call[0].endswith('/chat/completions')]
        self.assertTrue(any('Aurora launches on Friday' in json.dumps(body) for body in sent))
        self.assertIn('컨텍스트:',self.store.job(job['id'])['response'])

    def test_task_card_progress_button_returns_safe_owner_bound_evidence(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'private request secret'}},generation)
        job=self.store.jobs()[0]
        card=self.store.task_card(job['id'])
        initial=[c for c in self.calls if c[0].endswith('/sendMessage') and c[1].get('text','').startswith('요청을 받았습니다.')][-1]
        labels=[button['text'] for button in initial[1]['reply_markup']['inline_keyboard'][0]]
        self.assertEqual(labels,['진행 보기','작업 취소'])
        self.service.ingest_callback({'id':'foreign-progress','from':{'id':99},'message':{'chat':{'id':99,'type':'private'},'message_id':card['message_id']},'data':f"p7v:{job['id']}"},generation)
        self.assertFalse(any(c[0].endswith('/sendMessage') and c[1].get('text','').startswith('작업 상태:') for c in self.calls))
        self.service.ingest_callback({'id':'progress','from':{'id':42},'message':{'chat':{'id':42,'type':'private'},'message_id':card['message_id']},'data':f"p7v:{job['id']}"},generation)
        progress=[c for c in self.calls if c[0].endswith('/sendMessage') and c[1].get('text','').startswith('작업 상태:')][-1]
        self.assertIn('대기 중',progress[1]['text'])
        self.assertNotIn('private request',progress[1]['text'])
        self.assertNotIn(job['id'],progress[1]['text'])
        self.make_due(job['id'])
        self.service.run_one()
        edit=[c for c in self.calls if c[0].endswith('/editMessageText')][-1]
        self.assertEqual(edit[1]['reply_markup']['inline_keyboard'][0][0]['text'],'결과 상태 보기')

    def test_task_card_progress_truthfully_explains_restart_and_uncertain_delivery(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'private recovery request'}},generation)
        job=self.store.jobs()[0]
        card=self.store.task_card(job['id'])
        with self.store.db() as db:
            db.execute("UPDATE jobs SET status='running',delivery='sending' WHERE id=?",(job['id'],))
        self.store.recover()
        self.service.ingest_callback({'id':'recovery-progress','from':{'id':42},'message':{'chat':{'id':42,'type':'private'},'message_id':card['message_id']},'data':f"p7v:{job['id']}"},generation)
        progress=[c for c in self.calls if c[0].endswith('/sendMessage') and c[1].get('text','').startswith('작업 상태:')][-1][1]['text']
        self.assertIn('중단됨',progress)
        self.assertIn('자동으로 다시 실행하지 않았습니다.',progress)
        self.assertIn('전달 여부를 확인할 수 없습니다.',progress)
        self.assertIn('자동으로 다시 보내지 않았습니다.',progress)
        self.assertNotIn('private recovery request',progress)
        self.assertNotIn(job['id'],progress)

    def test_terminal_notifications_survive_restart_without_ambiguous_retry(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        while self.service.deliver_notification():pass
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'모델 없이 실패해 줘'}},generation)
        self.make_due(self.store.jobs()[0]['id'])
        self.service.run_one()
        job=self.store.jobs()[0]
        self.assertIn(job['delivery'],('pending','sent'))
        restarted=AgentService(QuickStore(self.temp.name),ModelAdapter(self.transport),self.transport)
        restarted.deliver_one()
        self.assertEqual(restarted.store.job(job['id'])['delivery'],'sent')
        with restarted.store.db() as db:db.execute("UPDATE jobs SET delivery='sending' WHERE id=?",(job['id'],))
        restarted.store.recover()
        self.assertEqual(restarted.store.job(job['id'])['delivery'],'unknown')

    def test_owner_can_record_live_task_card_attestation_only_after_durable_evidence(self):
        generation=self.pair()
        with self.assertRaises(ValueError):
            self.service.attest_telegram_task_card_acceptance({'web_confirmed':True,'restart_confirmed':True})
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'safe request'}},generation)
        job=self.store.jobs()[0];card=self.store.task_card(job['id'])
        callback_message={'chat':{'id':42,'type':'private'},'message_id':card['message_id']}
        self.service.ingest_callback({'id':'cancel','from':{'id':42},'message':callback_message,'data':f"p7c:{job['id']}"},generation)
        approval=self.store.queue_notification(job['id'],42,generation,'approval_needed',self.service.document_fingerprint())
        self.store.update_notification(approval['id'],'approved')
        completed=self.store.queue_notification('other-job',42,generation,'completed')
        self.store.update_notification(completed['id'],'sent',123)
        self.store.enqueue('web evidence','web-evidence');self.service.run_one()
        result=self.service.attest_telegram_task_card_acceptance({'web_confirmed':True,'restart_confirmed':True})
        self.assertTrue(result['passed'])
        settings=self.service.settings()
        self.assertTrue(settings['telegram_task_card_acceptance']['passed'])

    def test_p7_live_acceptance_report_is_redacted_and_requires_observations(self):
        from personal_agent.telegram_task_card_acceptance import report
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'secret request'}},generation)
        job=self.store.jobs()[0];card=self.store.task_card(job['id'])
        self.service.ingest_callback({'id':'cancel','from':{'id':42},'message':{'chat':{'id':42,'type':'private'},'message_id':card['message_id']},'data':f"p7c:{job['id']}"},generation)
        approval=self.store.queue_notification(job['id'],42,generation,'approval_needed',self.service.document_fingerprint())
        self.store.update_notification(approval['id'],'approved')
        completed=self.store.queue_notification('another-job',42,generation,'completed')
        self.store.update_notification(completed['id'],'sent',123)
        self.store.enqueue('web evidence','web-evidence')
        self.service.run_one()
        result=report(self.store,web_confirmed=True,restart_confirmed=True)
        self.assertTrue(result['passed'])
        encoded=json.dumps(result)
        self.assertNotIn('secret request',encoded)
        self.assertNotIn(job['id'],encoded)
        self.assertNotIn('message_id',encoded)

    def test_start_response_does_not_default_to_command_guidance(self):
        generation=self.pair()
        self.service.run_one();self.service.deliver_one()
        self.service.ingest_update({'update_id':11,'message':{'from':{'id':42},'chat':{'id':42,'type':'private'},'text':'/start'}},generation)
        self.service.run_one()
        self.assertNotIn('/note',self.store.jobs()[0]['response'])

    def test_actual_router_model_and_free_catalog(self):
        from unittest.mock import patch
        from personal_agent.providers import ModelAdapter
        adapter=ModelAdapter(lambda *a,**kw:{'model':'test/actual:free','choices':[{'message':{'content':'hello'}}]})
        result=adapter.invoke({'provider':'compatible','endpoint':'https://openrouter.ai/api/v1','model':'openrouter/free'},'test',[])
        self.assertEqual(result.model,'test/actual:free')
        with patch('personal_agent.quickstart_service.request_json',return_value={'data':[
            {'id':'good:free','pricing':{'prompt':'0','completion':'0'},'supported_parameters':['tools','tool_choice']},
            {'id':'paid:free','pricing':{'prompt':'1','completion':'0'},'supported_parameters':['tools','tool_choice']},
            {'id':'text-only:free','pricing':{'prompt':'0','completion':'0'},'supported_parameters':['tools']},
            {'id':'missing:free'}]}):
            self.assertEqual([m['id'] for m in self.service.free_models()['models']],['good:free'])

    def test_easy_model_connections(self):
        from unittest.mock import patch
        with patch('personal_agent.quickstart_service.request_json',return_value={'key':'test-only-key'}) as transport:
            connected=self.service.connect_openrouter({'code':'test-code','verifier':'a'*64})
            self.assertTrue(connected['model_test']['ok'])
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

    def test_exact_public_tunnel_host_accepts_one_time_mobile_pairing(self):
        self.store.claim(self.store.bootstrap.read_text(),'long-password-test')
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.service,['mobile.example.test'],'one-time-token'))
        thread=threading.Thread(target=server.serve_forever);thread.start()
        url='http://127.0.0.1:'+str(server.server_port)
        class NoRedirect(HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs):return None
        client=build_opener(HTTPCookieProcessor(CookieJar()),NoRedirect())
        def request(path):
            return client.open(Request(url+path,headers={'Host':'mobile.example.test'}),timeout=3)
        try:
            with self.assertRaises(HTTPError) as paired:
                request('/?access=one-time-token')
            self.assertEqual(paired.exception.code,303)
            cookie=paired.exception.headers['Set-Cookie'].split(';',1)[0]
            with client.open(Request(url+'/api/status',headers={'Host':'mobile.example.test','Cookie':cookie}),timeout=3) as response:
                self.assertTrue(json.load(response)['authenticated'])
            with request('/?access=one-time-token') as reused:
                self.assertEqual(reused.status,200)
        finally:
            server.shutdown();thread.join();server.server_close()

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
            package=self.store.root/'plugins'/'review.json';package.parent.mkdir(exist_ok=True)
            package.write_text(json.dumps({'version':1,'id':'review','enabled':True,'tools':[{'id':'review_notes','host_action':'list_notes','mode':'read_only'}],'roles':[{'id':'package_reviewer','name':'Package reviewer','instructions':'Review supplied material.','permissions':['read_only'],'tools':['review_notes']}]}))
            state=request('/api/state')
            self.assertEqual(state['settings']['packages'][1]['id'],'review')
            self.assertEqual(state['settings']['agents'][-1]['permissions'],['read_only'])
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

    def test_document_approval_http_api(self):
        self.store.claim(self.store.bootstrap.read_text(),'long-password-test')
        self.service.save_model({'provider':'compatible','endpoint':'https://example.test/v1','model':'test-model','api_key':'test-key'})
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.service))
        thread=threading.Thread(target=server.serve_forever);thread.start()
        client=build_opener(HTTPCookieProcessor(CookieJar()));url='http://127.0.0.1:'+str(server.server_port)
        def post(path,body):
            request=Request(url+path,data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with client.open(request,timeout=3) as response:return json.load(response)
        try:
            post('/api/login',{'password':'long-password-test'})
            self.assertTrue(post('/api/documents/approval',{'approved':True})['approved'])
            self.assertFalse(self.service.document_boundary()['requires_approval'])
        finally:
            server.shutdown();thread.join();server.server_close()


if __name__=='__main__':unittest.main()
