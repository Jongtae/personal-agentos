#!/bin/sh
# Restore a secret-free archive into a new, empty Compose data volume.
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 ARCHIVE.tar.gz" >&2
  exit 64
fi

archive=$1
case "$archive" in
  /*) ;;
  *) archive="$(pwd)/$archive" ;;
esac
archive_dir=$(dirname "$archive")
archive_name=$(basename "$archive")

if [ ! -f "$archive" ]; then
  echo "archive does not exist: $archive" >&2
  exit 64
fi
if [ -n "$(docker compose ps -q agentos)" ]; then
  echo "AgentOS is running; stop it and replace its data volume before restoring." >&2
  exit 65
fi

# Restore refuses a non-empty /state/data directory. This makes replacing a runtime
# an explicit operator action and avoids overwriting a live owner's state.
docker compose run --rm --no-deps -T \
  -v "$archive_dir:/backup:ro" \
  --entrypoint python agentos -c '
import sys
from pathlib import Path
from personal_agent.portable_state import restore_owner_state
print(restore_owner_state("/backup/" + sys.argv[1], Path("/state/data")))
' "$archive_name"
