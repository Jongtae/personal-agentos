# Linux/VPS Docker Compose

Install Docker Engine and the Compose plugin, then clone this repository and run:

```sh
docker compose up -d --build
curl http://127.0.0.1:8787/healthz
```

The service binds to loopback by default. Put a TLS reverse proxy or private tunnel in front of it before remote access. AgentOS data, settings, model keys, and Telegram state remain in the named `agentos-data` volume.

Update without replacing data:

```sh
git pull --ff-only
./scripts/compose-update.sh
```

## Backup and restore

Compose restart and update retain the same `agentos-data` volume, including
the private Telegram pairing. To move or recover owner state, create the
secret-free portable archive while the service is running:

```sh
mkdir -p backups
./scripts/compose-backup.sh "$PWD/backups/agentos-owner.tar.gz"
```

The archive contains work history and reviewed assistant declarations, but
never credentials, sessions, local-folder grants, model selection, or Telegram
pairing. Keep it in owner-controlled storage.

Restoring intentionally requires a new empty data volume. Stop the service,
remove only this Compose project's volume after confirming its name with
`docker compose down --volumes`, then restore and start it again:

```sh
docker compose down --volumes
./scripts/compose-restore.sh "$PWD/backups/agentos-owner.tar.gz"
docker compose up -d
curl --fail http://127.0.0.1:8787/healthz
```

This is a destructive replacement of the local Compose data volume. Claim the
restored runtime and reconnect the model, Telegram bot, and any local folders;
do not treat portable restore as Telegram continuity.

For a disposable VPS acceptance run, use:

```sh
python3 scripts/verify_compose_acceptance.py
```

It verifies image build, health, container recreation with a retained Telegram
pairing record, secret-free backup/restore, and volume cleanup. It does not
send a real Telegram message; paired-account delivery remains a separate live
owner check.
