import tempfile
import unittest
from personal_agent.a2a import A2ADelegation,A2AError
from personal_agent.quickstart_store import QuickStore
class Peer:
 def __init__(self):self.event={"state":"completed","artifact":{"id":"a","text":"ok"}};self.created=[];self.cancelled=[]
 def card(self):return {"protocol":"a2a/1","skill":"bounded-research","artifact_schema":"text"}
 def create(self,p):self.created.append(p);return {"correlation_id":p["correlation_id"]}
 def status(self,i,c):return {**self.event,"correlation_id":c}
 def cancel(self,i,c):self.cancelled.append((i,c))
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.peer=Peer();self.a=A2ADelegation(QuickStore(self.tmp.name),self.peer)
 def tearDown(self):self.tmp.cleanup()
 def test_explicit_lifecycle_and_artifact(self):
  row=self.a.delegate({"explicit":True,"prompt":"research"});self.assertNotIn("secret",str(self.peer.created));row=self.a.status(row["id"]);self.assertEqual(row["state"],"completed");self.assertEqual(self.a.artifact(row["id"],"a")["text"],"ok")
 def test_rejects_implicit_card_and_bad_artifact(self):
  with self.assertRaises(A2AError):self.a.delegate({"prompt":"no"})
  self.peer.event={"state":"completed","artifact":{"id":"a","text":"x"*12001}};row=self.a.delegate({"explicit":True,"prompt":"x"});self.assertEqual(self.a.status(row["id"])["state"],"failed")
 def test_cancel_is_idempotent(self):
  self.peer.event={"state":"working"};row=self.a.delegate({"explicit":True,"prompt":"x"});self.a.cancel(row["id"]);self.a.cancel(row["id"]);self.assertEqual(len(self.peer.cancelled),1)
