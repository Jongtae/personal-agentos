import json,tempfile,unittest
from pathlib import Path
from personal_agent.plugins import PluginRegistry
class PluginTests(unittest.TestCase):
 def test_lifecycle(self):
  with tempfile.TemporaryDirectory() as folder:
   manifest=Path(folder)/'demo.json';manifest.write_text(json.dumps({'version':1,'id':'demo','tools':[{'id':'notes','host_action':'list_notes','mode':'read_only'}],'roles':[]}))
   registry=PluginRegistry(Path(folder)/'data');self.assertEqual(registry.install(manifest),'demo');self.assertTrue(registry.list()[0]['enabled']);self.assertFalse(registry.set_enabled('demo',False)['enabled']);registry.remove('demo');self.assertEqual(registry.list(),[])
