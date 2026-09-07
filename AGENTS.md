# AgentOS contribution workflow

## Product priority

AgentOS is a local-first personal-agent runtime. AgentOS owns the personal state, assistant policy, tool boundary, work queue, approvals, evidence, and recovery; a connected Codex or Claude Code process is a bounded execution engine, not the owner of that state.

Every active Hub v2 task must advance one or more outcomes:

- no-API-key consumer onboarding through an existing AI subscription
- reliable Telegram-based personal work completion
- owner-controlled memory, context, tools, and approvals
- transparent execution evidence and recoverable failures
- lower setup and operating burden without broad host access

Do not expand Kubernetes, appliance, task-card polish, or UI work unless it directly advances these outcomes.

## Required lifecycle

Every milestone and iteration uses:

1. a GitHub issue with user outcome, runtime impact, acceptance criteria, non-goals, and validation plan
2. a matching branch
3. small intentional commits
4. a pull request with automated and live validation evidence named separately
5. merge, issue closeout, and a ledger entry

The active delivery order is `delivery-plan.yaml`. Historical v1/P7 plans are archived rather than deleted. An iteration cannot advance until its predecessor is complete or its explicitly recorded external blocker is resolved.

## Truthfulness and safety

- A capability is complete only when its actual execution is observed.
- Tests, mocks, connection checks, and live acceptance are different evidence and must be named separately.
- AgentOS must retain ownership of personal state when an external execution engine is selected.
- Each owner runtime is isolated from the host home directory and other owner runtimes. Engines receive only declared AgentOS tools; do not add arbitrary shell access, unapproved folders, host mounts, Docker socket access, external writes, or direct broad network access without a dedicated approval design and acceptance suite.
- Context capture is opt-in, local-first, sensitive-data filtered, and shared externally only under the selected assistant's policy.
- The managed control plane may create personal bots and relay transient data, but must not persist message bodies, personal history, documents, tool payloads, or provider credentials.
- Never claim a Codex, Claude Code, Telegram managed-bot, consumer installer, or hosting path works unless that exact path has live evidence.

## Pull request closeout

Every PR states what changed, why, validation evidence, known limitations, data/security impact, and the issue it closes. Squash merge feature work into `main` after validation passes. Record completed work in `TASKS.md`, `docs/roadmap.md`, and `docs/issue-branch-ledger.jsonl` together.
