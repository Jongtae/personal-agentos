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
   archive=Path(folder)/'backup.tar.gz';target=Path(folder)/'target'
   subprocess.run(['python3',str(ROOT/'scripts/agentos-backup.py'),str(source),str(archive)],check=True,capture_output=True,text=True)
   subprocess.run(['python3',str(ROOT/'scripts/agentos-restore.py'),str(archive),str(target)],check=True,capture_output=True,text=True)
   restored=QuickStore(target)
   self.assertEqual(restored.jobs()[0]['message'],'remember this')
   self.assertFalse(restored.claimed())
   self.assertIsNone(restored.config('file_roots'))
   self.assertFalse((target/'private'/'connections.json').exists())
