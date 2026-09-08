# Owner-Approved Operating Deployment Preparation Contract

## Status and outcome

`OP-01` is historical preparation evidence only. Its former claim that released `v1.0.4` was a supported candidate has been corrected by active `OP-02`: that tag predates the stabilization and preflight work, and its Compose image has no safe subscription-engine path. Do not deploy it. See the OP-02 remediation contract for current, fail-closed status.

The outcome is a credential-free, reproducible preparation package: exact install/start/configure/health/stop/recovery instructions, a machine-readable local preflight, and fixture evidence for its pass and failure states. This is not a claim that Docker, Telegram, Codex, Claude Code, or any provider is operating for an owner.

## Ordered owner procedure

1. **Install and select:** no checkout is currently a supported owner deployment candidate. The owner must wait for OP-02 closeout to name an immutable candidate. `python3 scripts/operating_preflight.py --root .` correctly fails closed while subscription-engine isolation is unimplemented.
2. **Start:** after the owner approves an operating deployment, run `docker compose up -d --build`. The owner may set only `AGENTOS_PORT` to select a local port; no public host, host-home mount, Docker socket mount, or credential environment variable is part of this path.
3. **Health and local claim:** wait for `http://127.0.0.1:${AGENTOS_PORT:-8787}/healthz` to return `{"ok": true}`. Open the local URL, claim the newly created runtime, and retain the generated local recovery material according to the UI instructions.
4. **Credential gates, after the deployment approval:** the owner alone chooses an already-installed subscription CLI and confirms its official login in the local AgentOS settings. If Telegram is desired, the owner separately creates a dedicated bot and enters its token into the local private connection store, then completes owner pairing. These gates are not part of preflight and no token, OAuth client, endpoint, or external connection is created by this cycle.
5. **Stop and recover:** use `docker compose down` to stop while retaining the named data volume. Before destructive volume replacement, use `scripts/compose-backup.sh ARCHIVE.tar.gz`; stop the service, replace with an empty data volume, run `scripts/compose-restore.sh ARCHIVE.tar.gz`, then start again. Portable restore deliberately excludes credentials, sessions, local-folder grants, engine selection, and Telegram pairing, so the owner must claim and reconnect the restored runtime.

## Health, failure, and recovery contract

`/healthz` is the only unauthenticated local health endpoint. Compose must fail its health check when it cannot reach that endpoint. The preflight is fail-closed: a version mismatch, non-loopback port, missing named volume, missing non-root runtime, missing health check, or missing start/backup/restore scripts is a non-ready result with a named recovery action. It performs no Docker operation, network request, credential read, or external provider call.

The supported stop/recovery path preserves the named volume across `down` and refuses restore while AgentOS is running. Backup and portable restore are secret-free by contract. Interrupted or uncertain work remains in the owner-local queue and is handled through the existing recovery surface; this preparation cycle does not retry an engine or resend Telegram work.

## Threat and data boundary

The container runs as the dedicated `agentos` user and receives only its internal `/data` volume. The host sees one loopback port and an owner-chosen archive directory only during backup/restore. No host home, arbitrary host directory, Docker socket, public tunnel, broad network policy, credentials, note bodies, prompts, or provider payloads are introduced by OP-01.

The preflight report contains only version, structural readiness booleans, and recovery identifiers. It never reads owner data, private connection files, environment secrets, or external CLI credentials.

## Automated evidence and deferred operating evidence

Fixtures cover ready, version-mismatch, unsafe binding, missing health check, missing runtime user, and missing recovery-script states. The repository CI runs this suite with the existing plan/document/ledger checks and the complete test suite. Docker Compose validation may be run on disposable data only; it is development evidence, not owner operating evidence.

Operating evidence is deliberately deferred: after explicit owner approval, an owner can record the actual selected release, local health result, and separately configured connection health. Until then, the prepared path is only *deployment-ready*, never *operating-configured*.

## Non-goals

OP-01 does not install Docker or a subscription CLI, enter credentials, configure OAuth, create a Telegram bot, activate an external connection, deploy a public endpoint, add a connector/A2A peer/marketplace capability, or change unrelated UI.
