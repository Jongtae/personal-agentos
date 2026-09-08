# OP-02 Operating Readiness Remediation Contract

## Correction and outcome

OP-01 remains historical evidence of its then-passing static checks. It did not prove its readiness claim: release tag `v1.0.4` predates the subscription-engine stabilization and preflight changes, and the Compose image contained no supported subscription-engine executable or durable official-login location.

OP-02 is active remediation, not a deployment-ready closeout. The current branch now contains the isolated-engine architecture, but it will supply one reproducible, immutable deployment candidate only when the remaining egress policy is accepted and its exact merge commit is recorded at OP-02 closeout. Until then, neither `v1.0.4` nor the current branch is a supported owner deployment candidate. This cycle does not build an operating Docker image, perform an owner deployment, configure credentials, log in to a provider, or prove live provider execution.

## Supported execution path

The isolated-engine architecture now exists. Compose declares a separate `engine` service and dedicated engine-profile volume; the service has no owner-state mount or host port, runs with a read-only filesystem and dropped capabilities, and shares only an internal network with AgentOS. AgentOS sends one capability-bound task through the gateway. The sidecar launches pinned Codex in an empty working directory and read-only sandbox, and its authenticated MCP callback exposes only `list_notes`. A host CLI or same-container CLI is not a supported path.

The architecture is intentionally unable to reach an external provider: `engine-internal` is an internal-only network and no narrow provider-egress policy exists. Therefore official login and live inference cannot work by design. Preflight recognizes the isolation checks but remains `not-ready` with `isolated-engine-egress-policy-required`. OP-02 cannot close until a narrow, owner-approved external-provider egress policy is specified, implemented, and accepted without adding host-home access, a Docker socket, arbitrary mounts, or a public endpoint.

## Ordered prepared procedure

1. Run `python3 scripts/operating_preflight.py --root .`. Its current non-zero result and `isolated-engine-egress-policy-required` recovery action are the correct safety result while provider egress is absent.
2. The local-only Compose service, data-volume lifecycle, health/stop path, and secret-free recovery behavior are product-path tested in a temporary isolated store.
3. Only after the egress policy and isolated-engine acceptance are complete and a closeout commit is recorded may the owner procedure be finalized as: check out that immutable commit; run preflight; start Compose; claim locally; explicitly approve and complete the isolated engine's official login; and optionally configure Telegram separately. None of those operating results is claimed now.
4. Restore remains stopped-only and empty-target-only. It must never overwrite data, replay unfinished work automatically, copy the engine profile, or recreate credentials.

## Product-path preflight

Preflight validates product behavior rather than text alone. In a disposable isolated store it verifies first claim, local service health and clean stop, an actual gateway-to-sidecar fixture round trip through the authenticated read-only MCP callback, archive/restore exclusion of engine material, quarantine of unfinished work, and duplicate-safe queue behavior. It also checks the separate service, profile, owner-state exclusion, internal network, read-only service, and configured gateway/callback structure. It must fail closed with a named recovery action for each failed product check. Its current egress-policy failure is expected evidence of the remaining gap, not readiness.

External provider access and official CLI authentication are not exercised or represented as successful. Tests may never use an owner credential. The fixture Codex process exercises AgentOS's real gateway, sidecar command boundary, read-only MCP bridge, queue, evidence, and restore code without an external network call. This is development evidence only; it is not a Docker image build, official login, or live provider result.

## Boundaries and non-goals

No host home directory, Docker socket, arbitrary host mount, public endpoint, broad network capability, credential/OAuth entry, external connection activation, Telegram setup, operating deployment, new connector, marketplace, or A2A capability is added. The only persistent engine location is the dedicated internal named volume. A future provider-egress rule must be narrow, explicit, and owner-approved; credential entry and all external activation remain later owner decisions.

## Completion evidence

Completion requires regression tests for the v1.0.4 candidate defect, missing engine path, isolated-engine authentication boundary, narrow external-provider egress policy, startup/health, first claim, selected-engine bounded execution/tool round trip, stop/start, secret-free restore, and duplicate terminal work. The goal remains active through independent Terra version/path review, Sol implementation, and Astra recovery/security review. CI, merge, and tracker/roadmap/ledger closeout must reference the exact merge commit. Only then may the plan enter `requires-explicit-owner-approval`; Docker build, official login, and live provider evidence remain separate owner-approved operating evidence.
