#!/bin/sh
# Export the Compose data volume without copying connection secrets to the host.
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

if [ ! -d "$archive_dir" ]; then
  echo "backup directory does not exist: $archive_dir" >&2
  exit 64
fi

# The only host path exposed to this one-off container is the owner-selected
# archive directory. The persistent AgentOS volume remains owned by Compose.
docker compose run --rm --no-deps -T \
  -v "$archive_dir:/backup" \
  --entrypoint python agentos -c '
import sys
from personal_agent.portable_state import export_owner_state
print(export_owner_state("/data", "/backup/" + sys.argv[1]))
' "$archive_name"
