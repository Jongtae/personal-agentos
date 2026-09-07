# AgentOS Hub v2 roadmap

AgentOS Hub v2 is a local-first personal-agent runtime, not a generic model gateway. The Mac hosts the owner-controlled runtime; AgentOS owns personal state, assistants, permissions, tools, task lifecycle, and evidence; Codex or Claude Code performs bounded engine turns.

## M0 — Product basis and delivery sequence

[#103](https://github.com/Jongtae/personal-agentos/issues/103) records the current product contract, freezes legacy P7 work, and moves the delivery loop onto Hub v2.

## M1 — Subscription engine connection

[#104](https://github.com/Jongtae/personal-agentos/issues/104) delivers consumer onboarding that detects Codex or Claude Code, guides the owner to its official login, and records only owner-confirmed connection without API-key setup. It does not inspect credentials or run the engine; bounded execution follows in M2. Homebrew remains a developer path.

## M1.5 — Personal runtime isolation

[#109](https://github.com/Jongtae/personal-agentos/issues/109) creates the user-scoped OCI container or managed lightweight VM, dedicated volume, mediated read-only file boundary, and hosted Kubernetes translation. The consumer never operates Docker or Kubernetes directly.

## M2 — AgentOS-owned execution boundary

[#105](https://github.com/Jongtae/personal-agentos/issues/105) adds bounded execution adapters and AgentOS MCP tools inside the isolated owner runtime. Engines do not receive arbitrary host access or a route outside that runtime.

## M3 — Personal Telegram bot and first work

[#106](https://github.com/Jongtae/personal-agentos/issues/106) creates a personal bot through the managed-bot flow and proves a real source-backed Telegram task through Codex.

## M4 — Personal context inbox

[#107](https://github.com/Jongtae/personal-agentos/issues/107) adds opt-in local clipboard/URL capture, sensitive-data filtering, retention, and per-assistant sharing policy.

## M5 — Trusted assistants and portability

[#108](https://github.com/Jongtae/personal-agentos/issues/108) exposes three official assistants and adds portable owner export/restore plus a managed-hosting migration design.

## Historical baseline

The v1 runtime and 1.0.3 release are retained as documented maintenance history. P7 Telegram task-card acceptance and release work are frozen rather than treated as Hub v2 prerequisites.
