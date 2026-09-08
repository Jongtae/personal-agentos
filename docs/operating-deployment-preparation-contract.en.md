# Owner-Approved Operating Deployment Preparation Contract

## Status and outcome

`OP-01` is historical preparation evidence only. Its former claim that released `v1.0.4` was a supported candidate has been corrected by active `OP-02`: that tag predates the stabilization and isolated-engine work. Do not deploy it. The current branch declares a separate isolated engine, dedicated profile, and capability-limited read-only MCP boundary, but its engine network intentionally has no external-provider egress. See the OP-02 remediation contract for the current fail-closed status.

The outcome is a credential-free, reproducible preparation package: conditional install/start/configure/health/stop/recovery instructions, a machine-readable local preflight, and fixture evidence for local product and failure states. It is not deployment-ready while `isolated-engine-egress-policy-required` remains. This is not a claim that a Docker image was built or that Telegram, Codex, Claude Code, official login, or any live provider is operating for an owner.

## Ordered owner procedure

1. **Install and select:** no checkout is currently a supported owner deployment candidate. The owner must wait for OP-02 closeout to name an immutable candidate. `python3 scripts/operating_preflight.py --root .` correctly recognizes the isolated service but fails closed with `isolated-engine-egress-policy-required` because the engine cannot reach its provider.
2. **Start, only after closeout and owner approval:** the future finalized procedure may direct the owner to run `docker compose up -d --build`. The owner may set only `AGENTOS_PORT` to select a local port; no public host, host-home mount, Docker socket mount, or credential environment variable is part of this path. This contract does not claim that the images currently build or start.
3. **Health and local claim, only after a successful approved start:** the owner will wait for `http://127.0.0.1:${AGENTOS_PORT:-8787}/healthz` to return `{"ok": true}`, open the local URL, claim the newly created runtime, and retain the generated local recovery material according to the UI instructions. No such operating result is recorded by this cycle.
4. **Credential gates, only after deployment approval and accepted egress:** the owner alone chooses the isolated subscription CLI and completes its official login through the approved engine profile. If Telegram is desired, the owner separately creates a dedicated bot and enters its token into the local private connection store, then completes owner pairing. These gates are not part of preflight and no login, token, OAuth client, endpoint, live inference, or external connection is created or proven by this cycle.
5. **Stop and recover:** use `docker compose down` to stop while retaining the named data volume. Before destructive volume replacement, use `scripts/compose-backup.sh ARCHIVE.tar.gz`; stop the service, replace with an empty data volume, run `scripts/compose-restore.sh ARCHIVE.tar.gz`, then start again. Portable restore deliberately excludes credentials, sessions, local-folder grants, engine selection, and Telegram pairing, so the owner must claim and reconnect the restored runtime.

## Health, failure, and recovery contract

`/healthz` is the only unauthenticated local health endpoint. Compose must fail its health check when it cannot reach that endpoint. The preflight is fail-closed: a version mismatch, non-loopback port, missing named volume, missing non-root runtime, missing health check, missing recovery scripts, missing isolated-engine boundary, or missing accepted engine-egress policy is a non-ready result with a named recovery action. It performs no Docker operation, credential read, or external provider call. Its only network activity is a loopback fixture round trip between temporary AgentOS and engine HTTP servers.

The supported stop/recovery path preserves the named volume across `down` and refuses restore while AgentOS is running. Backup and portable restore are secret-free by contract. Interrupted or uncertain work remains in the owner-local queue and is handled through the existing recovery surface; this preparation cycle does not retry an engine or resend Telegram work.

## Threat and data boundary

The AgentOS container runs as the dedicated `agentos` user and receives only its internal `/state` owner volume. The separate engine service receives only `/engine-profile`, has no owner-state mount or host port, uses a read-only filesystem and read-only Codex sandbox, and communicates with AgentOS through the internal gateway and authenticated `list_notes`-only MCP callback. The host sees one loopback AgentOS port and an owner-chosen archive directory only during backup/restore. No host home, arbitrary host directory, Docker socket, public tunnel, broad network policy, credential, or live provider payload is introduced.

The preflight report contains only version, structural readiness booleans, and recovery identifiers. It never reads owner data, private connection files, environment secrets, or external CLI credentials.

## Automated evidence and deferred operating evidence

Fixtures cover the isolated gateway/sidecar/read-only-MCP product path, version mismatch, unsafe binding, missing health check, missing runtime user, recovery behavior, and named egress-policy blocker. Recovery fixtures still quarantine incomplete work, refuse automatic replay, preserve duplicate safety, and exclude engine profile/configuration from portable restore. The repository CI runs this suite with the existing plan/document/ledger checks and the complete test suite. Static Compose checks and fixture execution are development evidence; no Docker image build or owner operating evidence is claimed.

Operating evidence is deliberately deferred: after egress acceptance, OP-02 closeout, and explicit owner approval, an owner can record the actual selected release, Docker build/start, local health result, official login, and separately configured connection health. Until then, the path is remediation preparation only—neither *deployment-ready* nor *operating-configured*.

## Non-goals

OP-01 and the current remediation preparation do not install or build Docker, install a subscription CLI, enter credentials, perform official login, configure OAuth, create a Telegram bot, activate or test an external connection, run live provider inference, deploy a public endpoint, add a connector/A2A peer/marketplace capability, or change unrelated UI.
