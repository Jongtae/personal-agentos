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

