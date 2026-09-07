import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
class BackupScripts(unittest.TestCase):
 def test_backup_restore(self):
  with tempfile.TemporaryDirectory() as folder:
   source=Path(folder)/'source';source.mkdir();(source/'agentos.db').write_text('state')
   archive=Path(folder)/'backup.tar.gz';target=Path(folder)/'target'
   subprocess.run(['python3',str(ROOT/'scripts/agentos-backup.py'),str(source),str(archive)],check=True,capture_output=True,text=True)
   subprocess.run(['python3',str(ROOT/'scripts/agentos-restore.py'),str(archive),str(target)],check=True,capture_output=True,text=True)
   self.assertEqual((target/'agentos.db').read_text(),'state')
