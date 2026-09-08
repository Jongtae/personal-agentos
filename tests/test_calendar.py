import tempfile,unittest
from personal_agent.calendar import CalendarCreate,CalendarError
from personal_agent.quickstart_store import QuickStore
class T(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.calls=[];self.c=CalendarCreate(QuickStore(self.tmp.name),lambda u,b,h:self.calls.append((u,b,h)) or {'id':'e1'})
 def tearDown(self):self.tmp.cleanup()
 def test_one_time_approval_and_idempotency(self):
  d=self.c.draft({'summary':'x','start':'2026-01-01T10:00','end':'2026-01-01T11:00','timezone':'Asia/Seoul'});a=self.c.approve(d['id'],'owner');self.assertEqual(self.c.create(d['id'],a['approval_id'],'owner')['id'],'e1');self.c.create(d['id'],a['approval_id'],'owner');self.assertEqual(len(self.calls),1)
 def test_no_approval_no_write(self):
  d=self.c.draft({'summary':'x','start':'a','end':'b','timezone':'z'})
  with self.assertRaises(CalendarError):self.c.create(d['id'],'no','owner')
  self.assertFalse(self.calls)
 def test_status_expiry_foreign_owner_and_transport_recovery(self):
  clock=[0];c=CalendarCreate(QuickStore(self.tmp.name),lambda *_:(_ for _ in ()).throw(TimeoutError()),now=lambda:clock[0]);d=c.draft({'summary':'x','start':'a','end':'b','timezone':'z'});a=c.approve(d['id'],'owner');clock[0]=901;self.assertEqual(c.status(d['id'],'owner')['state'],'expired')
  with self.assertRaises(CalendarError):c.create(d['id'],a['approval_id'],'other')
 def test_scope_timeout_and_malformed_response_fail_closed_without_secret_status(self):
  event={'summary':'x','start':'a','end':'b','timezone':'z'}
  for transport,scope,error in ((lambda *_:{'id':'x'},False,'scope-denied'),(lambda *_:(_ for _ in ()).throw(TimeoutError()),True,'transport-error'),(lambda *_:{},True,'malformed-response')):
   c=CalendarCreate(QuickStore(self.tmp.name),transport,scope_granted=lambda:scope);d=c.draft(event,'owner');a=c.approve(d['id'],'owner')
   with self.assertRaises(CalendarError):c.create(d['id'],a['approval_id'],'owner')
   status=c.status(d['id'],'owner');self.assertEqual(status['state'],'failed');self.assertEqual(status['error_class'],error);self.assertNotIn('approval',str(status))
 def test_owner_bound_preview_and_changed_canonical_payload_never_posts(self):
  d=self.c.draft({'summary':'x','start':'a','end':'b','timezone':'z'},'owner');a=self.c.approve(d['id'],'owner')
  with self.assertRaises(CalendarError):self.c.preview(d['id'],'other')
  rows=self.c._rows();rows[d['id']]['payload']['summary']='changed';self.c._put(rows)
  with self.assertRaises(CalendarError):self.c.create(d['id'],a['approval_id'],'owner')
  self.assertEqual(self.c.status(d['id'],'owner')['error_class'],'payload-changed');self.assertFalse(self.calls)
