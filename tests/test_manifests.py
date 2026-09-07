import unittest
from personal_agent.manifests import BUILTIN_MANIFEST,validate
class ManifestTests(unittest.TestCase):
 def test_builtin_is_valid(self):
  manifest=validate(BUILTIN_MANIFEST)
  self.assertEqual(manifest['version'],1)
  self.assertEqual([role['id'] for role in manifest['roles']],['researcher','reviewer','planner'])
  self.assertTrue(all(role['permissions']==['read_only'] for role in manifest['roles']))
 def test_rejects_unlisted_host_action(self):
  with self.assertRaises(ValueError):validate({'version':1,'tools':[{'id':'shell','host_action':'shell'}],'roles':[]})
 def test_rejects_role_permission(self):
  with self.assertRaises(ValueError):validate({'version':1,'tools':[],'roles':[{'id':'x','permissions':['network_write']} ]})
