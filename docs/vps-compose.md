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
