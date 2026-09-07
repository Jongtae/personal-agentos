"""Restore an AgentOS backup only into an empty data directory."""
import argparse
import tarfile
import tempfile
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('archive');parser.add_argument('data');args=parser.parse_args()
archive=Path(args.archive).expanduser().resolve();data=Path(args.data).expanduser().resolve()
if not archive.is_file():parser.error('Backup archive does not exist.')
if data.exists() and any(data.iterdir()):parser.error('Restore target must be empty.')
with tarfile.open(archive,'r:gz') as bundle:
 members=bundle.getmembers()
 if any(member.name.startswith('/') or '..' in Path(member.name).parts for member in members):parser.error('Unsafe backup archive.')
 with tempfile.TemporaryDirectory() as temporary:
  bundle.extractall(temporary,filter='data')
  restored=Path(temporary)/'agentos-data'
  if not restored.is_dir():parser.error('Invalid AgentOS backup.')
  data.parent.mkdir(parents=True,exist_ok=True);restored.replace(data)
print(data)
