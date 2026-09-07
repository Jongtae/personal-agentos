import json
import tempfile
import unittest
from pathlib import Path

from personal_agent.bounded_execution import AgentOSMcpTools, BoundedExecutionAdapter, ExecutionError
from personal_agent.quickstart_service import AgentService
from personal_agent.quickstart_store import QuickStore
from personal_agent.subscription_engines import SubscriptionEngines


class _Capabilities:
    def __init__(self): self.calls=[]
    def execute(self, name, arguments): self.calls.append((name, arguments)); return {'ok': True}


class BoundedExecutionTests(unittest.TestCase):
    def test_mcp_facade_exposes_only_agentos_allowlist(self):
        caps=_Capabilities(); tools=AgentOSMcpTools(caps)
        self.assertEqual([tool['name'] for tool in tools.definitions()], ['list_notes','save_note','web_search'])
        self.assertEqual(tools.call('web_search', {'query':'public weather'}), {'ok':True})
        with self.assertRaises(ExecutionError): tools.call('read_file', {'path':'/etc/passwd'})
        with self.assertRaises(ExecutionError): tools.call('save_note', {'content':''})
        self.assertEqual(caps.calls, [('web_search', {'query':'public weather'})])

    def test_adapter_uses_empty_turn_dir_fixed_env_and_no_shell(self):
        seen={}
        class Done:
            returncode=0
            stdout=json.dumps({'result':'bounded result'})
        def runner(argv, **kwargs):
            seen['argv'],seen['kwargs']=argv,kwargs
            return Done()
        with tempfile.TemporaryDirectory() as folder:
            adapter=BoundedExecutionAdapter(finder=lambda name:'/runtime/'+name, runner=runner, runtime_root=folder)
            result=adapter.execute('claude-code','hello',AgentOSMcpTools(_Capabilities()))
        self.assertEqual(result.content,'bounded result')
        self.assertEqual(seen['argv'][:2], ['/runtime/claude','-p'])
        self.assertTrue(seen['kwargs']['shell'] is False)
        self.assertEqual(set(seen['kwargs']['env']), {'HOME','PATH','LANG'})
        self.assertNotIn('private', str(seen))

    def test_codex_uses_only_its_existing_profile_and_cli_directory(self):
        seen={}
        class Done:
            returncode=0
            stdout=json.dumps({'item':{'type':'agent_message','text':'bounded result'}})
        def runner(argv, **kwargs):
            seen['kwargs']=kwargs
            return Done()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);profile=root/'official-codex-profile';profile.mkdir()
            adapter=BoundedExecutionAdapter(finder=lambda _: '/opt/homebrew/bin/codex', runner=runner,
                                            runtime_root=root/'turns', codex_home=profile)
            result=adapter.execute('codex','hello',AgentOSMcpTools(_Capabilities()))
        self.assertEqual(result.content,'bounded result')
        env=seen['kwargs']['env']
        self.assertEqual(env['CODEX_HOME'],str(profile))
        self.assertTrue(Path(env['HOME']).name.startswith('turn-'))
        self.assertEqual(env['PATH'],'/opt/homebrew/bin:/usr/bin:/bin')
        self.assertNotIn('GITHUB_TOKEN',env)
        self.assertNotIn('OPENAI_API_KEY',env)

    def test_default_engine_run_directory_is_owner_local_and_private(self):
        adapter=BoundedExecutionAdapter()
        self.assertEqual(adapter.runtime_root, Path.home()/'.local/share/agentos/engine-runs')

    def test_codex_uses_last_agent_message_not_terminal_usage_event(self):
        raw='\n'.join([json.dumps({'type':'thread.started'}),json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'final answer'}}),json.dumps({'type':'turn.completed','usage':{'input_tokens':1}})])
        self.assertEqual(BoundedExecutionAdapter._content('codex',raw),'final answer')

    def test_rejects_unstructured_or_failed_engine_output(self):
        class Failed: returncode=1; stdout='{}'
        with tempfile.TemporaryDirectory() as folder:
            adapter=BoundedExecutionAdapter(finder=lambda _: '/runtime/codex', runner=lambda *a,**k:Failed(), runtime_root=folder)
            with self.assertRaises(ExecutionError): adapter.execute('codex','hello',AgentOSMcpTools(_Capabilities()))


class SubscriptionServiceTests(unittest.TestCase):
    def test_selected_subscription_engine_runs_through_bounded_adapter(self):
        class Adapter:
            def __init__(self): self.call=None
            def execute(self, engine, prompt, tools):
                self.call=(engine,prompt,[t['name'] for t in tools.definitions()])
                from personal_agent.bounded_execution import ExecutionResult
                return ExecutionResult('engine answer',engine,0)
        with tempfile.TemporaryDirectory() as folder:
            store=QuickStore(Path(folder)/'data')
            engines=SubscriptionEngines(finder=lambda _: '/runtime/codex', clock=lambda:1)
            adapter=Adapter(); service=AgentService(store, subscription_engines=engines, execution_adapter=adapter)
            service.connect_subscription_engine({'engine':'codex','officially_authenticated':True})
            job=store.enqueue('do work','subscription-test')
            self.assertTrue(service.run_one())
            self.assertEqual(adapter.call[0], 'codex')
            self.assertEqual(adapter.call[2], ['list_notes','save_note','web_search'])
            self.assertEqual(store.job(job)['response'], 'engine answer')


    def test_subscription_preflights_explicit_public_lookup_and_records_sources(self):
        class Network:
            def __init__(self): self.calls=[]
            def execute(self, plan):
                self.calls.append(plan)
                return {'tool':'web_search','query':plan['query'],'retrieved_at':1,
                        'results':[{'title':'Public result','url':'https://example.test/result','snippet':'public snippet'}],
                        'sources':['https://example.test/result']}
        class Adapter:
            def __init__(self): self.prompt=''
            def execute(self, engine, prompt, tools):
                self.prompt=prompt
                from personal_agent.bounded_execution import ExecutionResult
                return ExecutionResult('source-backed answer',engine,0)
        with tempfile.TemporaryDirectory() as folder:
            store=QuickStore(Path(folder)/'data')
            engines=SubscriptionEngines(finder=lambda _: '/runtime/codex', clock=lambda:1)
            adapter=Adapter(); service=AgentService(store, subscription_engines=engines, execution_adapter=adapter)
            network=Network(); service.local_tools=network
            service.connect_subscription_engine({'engine':'codex','officially_authenticated':True})
            job=store.enqueue('성남시 날씨를 찾아줘','subscription-preflight')
            self.assertTrue(service.run_one())
            self.assertEqual(network.calls,[{'tool':'web_search','query':'성남시 날씨'}])
            self.assertIn('https://example.test/result',adapter.prompt)
            with store.db() as db:
                events=[dict(row) for row in db.execute('SELECT tool,status,detail FROM tool_events WHERE job_id=?',(job,))]
            event=next(row for row in events if row['tool']=='web_search' and row['status']=='succeeded')
            self.assertIn('https://example.test/result',event['detail'])

    def test_subscription_lookup_never_derives_private_or_ordinary_prose(self):
        from personal_agent.quickstart_service import subscription_public_lookup_query
        self.assertEqual(subscription_public_lookup_query('/search AgentOS release'), 'AgentOS release')
        self.assertIsNone(subscription_public_lookup_query('/search my api token is abc'))
        self.assertIsNone(subscription_public_lookup_query('내 메모를 정리해줘'))
