import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
class BackupScripts(unittest.TestCase):
 def test_backup_restore(self):
  with tempfile.TemporaryDirectory() as folder:
   source=Path(folder)/'source'
   from personal_agent.quickstart_store import QuickStore
   store=QuickStore(source);store.claim(store.bootstrap.read_text(),'a-long-test-password')
   store.put('file_roots',[{'path':'/private'}]);store.secret('telegram_token','secret');store.enqueue('remember this','work')
   store.put('a2a_delegations',{'task':{'id':'task','owner':'owner','correlation_id':'private-correlation','state':'completed','peer':'compatibility-a2a-peer','skill':'bounded-research','artifacts':[{'id':'a','text':'private artifact'}]}})
   store.put('calendar_create',{'draft':{'payload':{'summary':'private'},'approval':'secret'}})
   archive=Path(folder)/'backup.tar.gz';target=Path(folder)/'target'
   subprocess.run(['python3',str(ROOT/'scripts/agentos-backup.py'),str(source),str(archive)],check=True,capture_output=True,text=True)
   subprocess.run(['python3',str(ROOT/'scripts/agentos-restore.py'),str(archive),str(target)],check=True,capture_output=True,text=True)
   restored=QuickStore(target)
   self.assertEqual(restored.jobs()[0]['message'],'remember this')
   self.assertFalse(restored.claimed())
   self.assertIsNone(restored.config('file_roots'))
   exported=restored.config('a2a_delegations')['task'];self.assertEqual(exported['state'],'completed');self.assertNotIn('owner',exported);self.assertNotIn('correlation_id',exported);self.assertNotIn('artifacts',exported)
   self.assertIsNone(restored.config('calendar_create'))
   self.assertFalse((target/'private'/'connections.json').exists())
