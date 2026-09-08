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
  row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"research"});self.assertNotIn("secret",str(self.peer.created));row=self.a.status(row["id"],"owner");self.assertEqual(row["state"],"completed");self.assertEqual(self.a.artifact(row["id"],"a","owner")["text"],"ok")
 def test_rejects_implicit_card_and_bad_artifact(self):
  with self.assertRaises(A2AError):self.a.delegate({"prompt":"no"})
  self.peer.event={"state":"completed","artifact":{"id":"a","text":"x"*12001}};row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"});self.assertEqual(self.a.status(row["id"],"owner")["state"],"failed")
 def test_cancel_is_idempotent(self):
  self.peer.event={"state":"working"};row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"});self.a.cancel(row["id"],"owner");self.a.cancel(row["id"],"owner");self.assertEqual(len(self.peer.cancelled),1)
 def test_owner_binding_progress_timeout_and_peer_cancel(self):
  self.peer.event={"state":"working","progress":"halfway"};row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"});self.assertEqual(row["progress"],["halfway"])
  with self.assertRaises(A2AError):self.a.status(row["id"],"other")
  self.peer.event={"state":"canceled"};self.assertEqual(self.a.status(row["id"],"owner")["state"],"canceled")
  self.peer.event={"state":"working"};clock=[0];timed=A2ADelegation(QuickStore(self.tmp.name),self.peer,now=lambda:clock[0],timeout_seconds=1);row=timed.delegate({"explicit":True,"owner":"owner","prompt":"x"});clock[0]=2;self.assertEqual(timed.status(row["id"],"owner")["state"],"timed-out")
 def test_rejects_bad_card_correlation_and_artifact_shape(self):
  self.peer.card=lambda:{"protocol":"a2a/1","skill":"bounded-research","artifact_schema":"json"}
  with self.assertRaises(A2AError):self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"})
  self.peer.card=lambda:{"protocol":"a2a/1","skill":"bounded-research","artifact_schema":"text"};self.peer.event={"state":"completed","artifact":{"id":"a","text":"ok","extra":"no"}}
  row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"});self.assertEqual(self.a.status(row["id"],"owner")["state"],"failed")
 def test_sse_progress_and_duplicate_terminal_event_are_normalized(self):
  self.peer.event={"state":"working"};row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"})
  self.peer.events=lambda ident,correlation:iter(({"correlation_id":correlation,"state":"working","progress":"one"},{"correlation_id":correlation,"state":"completed","artifact":{"id":"a","text":"ok"}},{"correlation_id":correlation,"state":"completed","artifact":{"id":"b","text":"duplicate"}}));row=self.a.status(row["id"],"owner")
  self.assertEqual(row["state"],"completed");self.assertEqual(row["progress"],["one"]);self.assertEqual(row["artifacts"],[{"id":"a","text":"ok"}])
  self.assertEqual(self.a.status(row["id"],"owner")["state"],"completed")
 def test_sse_correlation_mismatch_is_rejected(self):
  self.peer.event={"state":"working"};row=self.a.delegate({"explicit":True,"owner":"owner","prompt":"x"});self.peer.events=lambda ident,correlation:iter(({"correlation_id":"wrong","state":"working"},))
  with self.assertRaises(A2AError):self.a.status(row["id"],"owner")
