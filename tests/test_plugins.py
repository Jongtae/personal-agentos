import json,tempfile,unittest
from pathlib import Path
from personal_agent.plugins import PluginRegistry
from personal_agent.quickstart import plugins_main
class PluginTests(unittest.TestCase):
 def test_lifecycle(self):
  with tempfile.TemporaryDirectory() as folder:
   manifest=Path(folder)/'demo.json';manifest.write_text(json.dumps({'version':1,'id':'demo','tools':[{'id':'notes','host_action':'list_notes','mode':'read_only'}],'roles':[]}))
   registry=PluginRegistry(Path(folder)/'data');self.assertEqual(registry.install(manifest),'demo');self.assertTrue(registry.list()[0]['enabled']);self.assertFalse(registry.set_enabled('demo',False)['enabled']);registry.remove('demo');self.assertEqual(registry.list(),[])
 def test_cli_lists_declaration_plugins(self):
  with tempfile.TemporaryDirectory() as folder:
   manifest=Path(folder)/'demo.json';manifest.write_text(json.dumps({'version':1,'id':'demo','tools':[],'roles':[]}))
   data=Path(folder)/'data';plugins_main(['--data',str(data),'install',str(manifest)])
   self.assertTrue(PluginRegistry(data).list()[0]['enabled'])
