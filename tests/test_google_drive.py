import unittest
from personal_agent.google_drive import GoogleDrive

class DriveTests(unittest.TestCase):
 def test_search_redacts_token_and_returns_metadata(self):
  seen=[]
  def transport(url,body,headers): seen.append((url,headers));return {'files':[{'id':'a','name':'plan','mimeType':'text/plain'}]}
  result=GoogleDrive(transport,'secret').search('plan')
  self.assertEqual(result,[{'id':'a','name':'plan','mime_type':'text/plain','modified_time':''}])
  self.assertNotIn('secret',seen[0][0])
