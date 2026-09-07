import tempfile
import unittest

from personal_agent.quickstart_service import AgentService
from personal_agent.quickstart_store import QuickStore
from personal_agent.subscription_engines import SubscriptionEngines


class SubscriptionEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.store=QuickStore(self.temp.name)
        engines=SubscriptionEngines(finder=lambda command: '/bin/codex' if command=='codex' else None,clock=lambda:1234)
        self.service=AgentService(self.store,subscription_engines=engines)

    def tearDown(self):self.temp.cleanup()

    def test_discovery_never_reads_or_reports_credentials(self):
        engines=self.service.settings()['subscription_engines']['engines']
        self.assertEqual([(e['id'],e['installed']) for e in engines],[('codex',True),('claude-code',False)])
        self.assertNotIn('token',str(engines).lower())

    def test_connect_requires_installed_cli_and_owner_login_confirmation(self):
        with self.assertRaises(ValueError):self.service.connect_subscription_engine({'engine':'codex','officially_authenticated':False})
        status=self.service.connect_subscription_engine({'engine':'codex','officially_authenticated':True})
        self.assertEqual(status['selected'],'codex')
        selected=[e for e in status['engines'] if e['id']=='codex'][0]
        self.assertTrue(selected['connected']);self.assertEqual(selected['authentication'],'owner-confirmed-official-login')
        self.assertFalse(self.store.secret('model_key'))
        with self.assertRaises(ValueError):self.service.connect_subscription_engine({'engine':'claude-code','officially_authenticated':True})
