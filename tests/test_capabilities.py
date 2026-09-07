import tempfile
import unittest
from personal_agent.capabilities import CapabilityRegistry
from personal_agent.quickstart_store import QuickStore

class CapabilityTests(unittest.TestCase):
 def test_enable_requires_exact_declared_scope(self):
  with tempfile.TemporaryDirectory() as root:
   registry=CapabilityRegistry(QuickStore(root))
   with self.assertRaises(ValueError): registry.transition('builtin-mcp-read','enabled',())
   self.assertEqual(registry.transition('builtin-mcp-read','enabled',('read',))['state'],'enabled')
   self.assertEqual(registry.transition('builtin-mcp-read','paused')['state'],'paused')
   self.assertEqual(registry.transition('builtin-mcp-read','disconnected')['state'],'disconnected')
