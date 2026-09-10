# Development Governance — Contract-First Delivery

## Purpose

AgentOS uses contract-first delivery with automated quality gates. It is designed to keep development fast, repeatable, and independent of a person manually exercising every feature or third-party service on every change.

## Method

The governance combines four complementary practices:

1. **Contract-first development.** Every capability defines its user outcome, boundary, inputs, outputs, failure states, data classification, and non-goals before implementation.
2. **Consumer-driven contract testing.** An AgentOS adapter is tested against versioned fixtures and test doubles that represent the precise external request/response contract it consumes.
3. **Test-pyramid automation.** Most coverage is focused unit and component testing; a smaller set verifies local integration and end-to-end product flows. UI or manual broad-stack testing is never the default release gate.
4. **Continuous-integration quality gates.** Every pull request runs deterministic formatting, canonical-document existence, local-link, contract-fixture, and relevant automated tests before it can merge. Historical translations must link to their English canonical source; translation parity is not a merge gate.

## Development completion rule

The [Goal Execution Contract](goal-execution-contract.en.md) defines how an active plan/issue becomes an executable goal, how it remains active or becomes blocked, and the audit required before completion.

An iteration is complete when all of the following are recorded in its issue and pull request:

- a documented contract and threat/data-boundary decision;
- versioned success, denial, timeout, malformed-response, and recovery fixtures where applicable;
- automated tests that exercise the product code against those fixtures or mocks;
- required repository checks passing in CI; and
- known limitations and the exact distinction between mock evidence and operating evidence.

No person is required to perform a routine manual acceptance test, log in to a third-party provider, or create a provider token to complete a development iteration. Human review remains a product and security design activity, not a recurring test gate.

## External integrations and agents

MCP servers, A2A peers, runtimes, OAuth providers, and external action APIs are implemented behind AgentOS-owned adapters. Their development contracts must state allowed scopes, request and response schemas, timeouts, cancellation, idempotency, redaction, approval behavior, error mapping, and disconnect/recovery behavior.

Development uses local mock peers and fixtures only. It never requires live credentials, a live URL, a real provider account, or a real action. A mock must reject undeclared requests so an adapter cannot accidentally grow an unreviewed dependency.

## Operating-mode deployment

Only after an entire Master Plan is complete does the owner deploy AgentOS in operating mode and configure real credentials, OAuth client registrations, endpoints, and enabled connections. This is configuration and activation, not retroactive manual acceptance testing of every development PR.

The deployed runtime must use automated startup and health checks, fail closed on missing or invalid configuration, redact secrets from evidence, and retain a machine-readable deployment report. An operating connection may be described as configured only when its automated health check succeeds. Mock evidence remains labelled as development evidence and never as proof that the external service is live.

## Governance controls

- One GitHub issue, `codex/` branch, focused commits, and a PR are required for every iteration.
- CI blocks merge on failed automated gates; it does not wait for a person to carry out a routine live test.
- A contract change requires its fixture and mock suite to change in the same PR.
- New scopes, external writes, credentials, data classes, or recovery semantics require a contract and threat-model update before implementation.
- Tests must be deterministic, hermetic where possible, and safe to run without personal data or external credentials.
- A capability is described as *development-complete* after its declared automated gates pass. It is described as *operating-configured* only after the later automated deployment health check succeeds.

## Non-goals

This policy does not claim that mocks prove vendor availability, account entitlement, network reachability, or real-world provider behavior. It also does not allow undocumented external calls, arbitrary runtime installation, or bypassing approval and local-first data boundaries.
