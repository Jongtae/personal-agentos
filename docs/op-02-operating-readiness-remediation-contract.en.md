# OP-02 Operating Readiness Remediation Contract

## Correction and outcome

OP-01 remains historical evidence of its then-passing static checks. It did not prove its readiness claim: release tag `v1.0.4` predates the subscription-engine stabilization and preflight changes, and the Compose image contained no supported subscription-engine executable or durable official-login location.

OP-02 is active remediation, not a deployment-ready closeout. It will supply one reproducible, immutable deployment candidate only when its exact merge commit is recorded at OP-02 closeout. Until then, neither `v1.0.4` nor the current branch is a supported owner deployment candidate. This cycle does not perform an owner deployment or configure credentials.

## Supported execution path

The current Compose service deliberately has no supported subscription-engine executable. Adding a CLI to the same container would let that process read the owner-state volume, so a profile volume alone is not an execution boundary. Preflight fails closed with `subscription-engine-isolation-design-required` rather than pretending that a host CLI or same-container CLI is usable.

The required supported path is a separately isolated engine runtime with no owner-state mount, a dedicated official-login profile, and a capability-limited authenticated IPC/MCP proxy to AgentOS. The proxy may expose only the declared per-task tools and evidence exchange. Its container must not receive the host home directory, Docker socket, arbitrary mounts, or a public endpoint. This material security boundary needs its own implementation and acceptance evidence before OP-02 can close.

## Ordered prepared procedure

1. Run `python3 scripts/operating_preflight.py --root .`. Its current non-zero result is the correct safety result until the isolated engine path exists.
2. The local-only Compose service, data-volume lifecycle, health/stop path, and secret-free recovery behavior are product-path tested in a temporary isolated store.
3. Once the isolated-engine acceptance is implemented and a closeout commit is recorded, the owner procedure will be finalized as: check out that immutable commit; run preflight; start Compose; claim locally; explicitly approve and complete the isolated engine's official login; and optionally configure Telegram separately.
4. Restore remains stopped-only and empty-target-only. It must never overwrite data, replay unfinished work automatically, copy the engine profile, or recreate credentials.

## Product-path preflight

Preflight validates product behavior rather than text alone. In a disposable isolated store it verifies first claim, local service health and clean stop, a bounded fixture-engine MCP round trip, archive/restore exclusion of engine material, quarantine of unfinished work, and duplicate-safe queue behavior. It also checks Compose structural constraints. It must fail closed with a named recovery action for each failed product check; its current named isolation failure is expected evidence of the remaining gap, not readiness.

External provider and official CLI authentication are represented by fixtures; tests may never use an owner credential. The fixture engine must exercise AgentOS's real bounded adapter, MCP bridge, queue, evidence, and restore code rather than a fabricated service response.

## Boundaries and non-goals

No host home directory, Docker socket, arbitrary host mount, public endpoint, broad network capability, credential/OAuth entry, external connection activation, Telegram setup, operating deployment, new connector, marketplace, or A2A capability is added. The only persistent engine location is the dedicated internal named volume. Credential entry and all external activation require a later explicit owner decision.

## Completion evidence

Completion requires regression tests for the v1.0.4 candidate defect, missing engine path, isolated-engine authentication boundary, startup/health, first claim, selected-engine bounded execution/tool round trip, stop/start, secret-free restore, and duplicate terminal work. The goal remains active through independent Terra version/path review, Sol implementation, and Astra recovery/security review. CI, merge, and tracker/roadmap/ledger closeout must reference the exact merge commit. Only then may the plan enter `requires-explicit-owner-approval`.
