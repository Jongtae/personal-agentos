"""Create a portable AgentOS data backup without copying temporary locks."""
import argparse
import shutil
import tempfile
from pathlib import Path

parser=argparse.ArgumentParser();parser.add_argument('data');parser.add_argument('archive');args=parser.parse_args()
data=Path(args.data).expanduser().resolve();archive=Path(args.archive).expanduser().resolve()
if not data.is_dir():parser.error('AgentOS data directory does not exist.')
with tempfile.TemporaryDirectory() as temporary:
 # Connection secrets (including a BotFather token) never leave the local
 # runtime through a portable export.  They must be reconnected after restore.
 staging=Path(temporary)/'agentos-data';shutil.copytree(data,staging,ignore=shutil.ignore_patterns('instance.lock','*.lock','connections.json'))
 archive.parent.mkdir(parents=True,exist_ok=True)
 result=shutil.make_archive(str(archive.with_suffix('')),'gztar',temporary,'agentos-data')
 target=archive if archive.suffixes[-2:]==['.tar','.gz'] else archive.with_suffix('.tar.gz')
 Path(result).replace(target)
 print(target)
