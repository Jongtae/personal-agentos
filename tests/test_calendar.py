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
