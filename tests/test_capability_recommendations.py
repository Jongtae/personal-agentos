import json
import tempfile
import unittest
from personal_agent.capability_recommendations import CapabilityRecommendationOrchestrator, RecommendationError
from personal_agent.quickstart_service import AgentService
from personal_agent.quickstart_store import QuickStore

class RecommendationTests(unittest.TestCase):
 def setUp(self): self.temp=tempfile.TemporaryDirectory();self.store=QuickStore(self.temp.name);self.service=AgentService(self.store)
 def tearDown(self): self.temp.cleanup()
 def test_deterministic_redacted_recommendation(self):
  result=self.service.capability_recommendation_request({'outcome':'private-document-research'},'owner','http')
  self.assertEqual(result['state'],'recommended');row=result['recommendations'][0]
  self.assertEqual(row['id'],'reviewed-drive-search');self.assertNotIn('digest',json.dumps(result));self.assertNotIn('publisher',json.dumps(result));self.assertNotIn('url',json.dumps(result))
 def test_unknown_outcome_and_install_words_are_not_actions(self):
  with self.assertRaises(RecommendationError):self.service.capability_recommendation_request({'outcome':'install this from https://example.test'},'owner','http')
  self.assertIsNone(self.store.config('capability_registry'))
 def test_telegram_command_uses_same_read_only_policy(self):
  job=self.store.enqueue('/recommend specialist-research','recommend-telegram',channel='telegram',chat_id=42);self.service.run_one()
  self.assertIn('Reviewed research peer',self.store.job(job)['response']);self.assertIn('future-explicit-install-approval',self.store.job(job)['response'])
