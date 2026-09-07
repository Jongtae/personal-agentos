import unittest
from personal_agent.manifests import BUILTIN_MANIFEST,validate
class ManifestTests(unittest.TestCase):
 def test_builtin_is_valid(self):self.assertEqual(validate(BUILTIN_MANIFEST)['version'],1)
 def test_rejects_unlisted_host_action(self):
  with self.assertRaises(ValueError):validate({'version':1,'tools':[{'id':'shell','host_action':'shell'}],'roles':[]})
 def test_rejects_role_permission(self):
  with self.assertRaises(ValueError):validate({'version':1,'tools':[],'roles':[{'id':'x','permissions':['network_write']} ]})
