# AgentOS Hub v2 roadmap

AgentOS Hub v2 is a local-first personal-agent runtime, not a generic model gateway. The Mac hosts the owner-controlled runtime; AgentOS owns personal state, assistants, permissions, tools, task lifecycle, and evidence; Codex or Claude Code performs bounded engine turns.

## M0 — Product basis and delivery sequence

[#103](https://github.com/Jongtae/personal-agentos/issues/103) records the current product contract, freezes legacy P7 work, and moves the delivery loop onto Hub v2.

## M1 — Subscription engine connection

[#104](https://github.com/Jongtae/personal-agentos/issues/104) delivers consumer onboarding that detects Codex or Claude Code, guides the owner to its official login, and records only owner-confirmed connection without API-key setup. It does not inspect credentials or run the engine; bounded execution follows in M2. Homebrew remains a developer path.

## M1.5 — Personal runtime isolation

[#109](https://github.com/Jongtae/personal-agentos/issues/109) creates the user-scoped OCI container or managed lightweight VM, dedicated volume, mediated read-only file boundary, and hosted Kubernetes translation. The consumer never operates Docker or Kubernetes directly. See [the isolation boundary](runtime-isolation.md).

## M2 — AgentOS-owned execution boundary

[#105](https://github.com/Jongtae/personal-agentos/issues/105) adds bounded execution adapters and AgentOS MCP tools inside the isolated owner runtime. A turn receives an empty temporary working directory, a fixed minimal environment, structured output handling, a timeout, and only the `list_notes`, `save_note`, and `web_search` AgentOS tool facade. Engines do not receive arbitrary host access, owner storage, credentials, document roots, or a route outside that runtime. Automated boundary coverage is complete; a real owner subscription turn still requires separately recorded live acceptance evidence.

## M3 — Personal Telegram bot and first work

**delivered.** [#106](https://github.com/Jongtae/personal-agentos/issues/106) uses an owner-created BotFather bot: the owner pastes its token once into authenticated local AgentOS, which validates it locally, creates a one-time private pairing link, and owns polling, recovery, and delivery. The token remains only in the local private connection store and is excluded from settings, logs, events, exports, and the redacted [live acceptance procedure](validation/h3-01-botfather-telegram-first-work.md).

## M4 — Personal context inbox

**delivered.** [#107](https://github.com/Jongtae/personal-agentos/issues/107) adds opt-in local clipboard/URL capture, sensitive-data filtering, retention, and per-assistant sharing policy.

## M5 — Trusted assistants and portability

**delivered.** [#108](https://github.com/Jongtae/personal-agentos/issues/108) exposes three official assistants and adds portable owner export/restore plus a managed-hosting migration design. The built-ins are researcher, reviewer, and planner; each is an explicit bounded, read-only role. `scripts/agentos-backup.py` exports owner state and reviewed plugin declarations only. It excludes connection secrets, login/session material, local folder grants, selected engines/models, and Telegram pairing; restoring requires a new local claim and explicit reconnection.

## Historical baseline

## Completed repository maintenance

[#170](https://github.com/Jongtae/personal-agentos/issues/170) adds Korean, Simplified Chinese, and Japanese README versions, with navigation between all supported languages. It also adds repository hooks and `main` branch protection to keep work on issue-linked pull-request branches.

The v1 runtime and 1.0.3 release are retained as documented maintenance history. P7 Telegram task-card acceptance and release work are frozen rather than treated as Hub v2 prerequisites.

The [V1-02 Telegram daily-work iteration](https://github.com/Jongtae/personal-agentos/issues/137) makes the existing paired-owner Telegram surface usable for routine natural-language requests: status-only task cards, progress, queued-only cancellation, document-sharing approval, and truthful restart or uncertain-delivery status. It does not replay interrupted work or uncertain Telegram sends.

The [V1-03 safe personal-context iteration](https://github.com/Jongtae/personal-agentos/issues/138) adds an explicit Telegram context attachment form. The owner selects opaque local inbox IDs with `/context ID[,ID] -- request`; AgentOS never selects or enumerates context from prose. Attached items remain local until a model-specific local sharing policy exists and, for an external model, the paired owner approves that exact queued job in Telegram. Results retain local source labels; cards, approvals, and progress controls do not reveal context content.

## Active — AgentOS UX v1.1

The [UX v1.1 epic](https://github.com/Jongtae/personal-agentos/issues/149) turns the delivered personal runtime into a minimal, text-first DM with one visible personal agent. [UX-01](https://github.com/Jongtae/personal-agentos/issues/150) makes the web home conversation-first and moves technical configuration into progressive management. Subsequent iterations add explicit workspaces and saved results, Telegram DM continuity, human-readable data-boundary and recovery language, then release acceptance. UX-04 displays only redacted source categories and counts beside completed results, with one clear recovery next action. UX-03a completes the missing natural-language Telegram context-selection flow before release acceptance. UX-05 blocks tag, GitHub Release, and Homebrew updates until redacted paired-owner Telegram evidence passes. The detailed product basis is in [UX v1.1 personal-agent DM](ux-v1.1-personal-agent-dm.ko.md).

## Planned — Telegram Conversation UX v1.2

[UX-06](https://github.com/Jongtae/personal-agentos/issues/162) begins only after UX-05 releases. It treats the Telegram bubble sequence as product UX: concise acknowledgement, only necessary progress, one scannable completion message, owner-requested detail, clearly distinct approval and recovery prompts, and safe idempotent owner-only controls.

### UX-06 implementation status

**Delivered.** [#162](https://github.com/Jongtae/personal-agentos/issues/162) records the owner-visible bubble contract in [UX-06 Telegram conversation](ux-06-telegram-conversation.ko.md). The implementation preserves one status card and one terminal answer bubble, keeps approval/recovery controls separate, and expands the readable long-result preview. The root suite passed and the deployed Telegram desktop flow was directly observed to edit a status card to completion followed by one terminal answer without a generic completion duplicate.

## Active — Master Plan 1 Personal Assistant Core

The owner closed UX-05 after deciding its remaining manual Telegram observations were disproportionate. This does not claim the waived checks passed. [Master Plan 1](master-plan-01-personal-assistant-core.en.md) is implementation incomplete: R-01 supplies policy-owned ReAct orchestration, R-02 supplies the mock A2A contract, and R-03 supplies the Calendar approval contract; R-04 and R-05 must still complete Drive and release acceptance. External credentials and real connections remain deferred to the owner-controlled operating-mode deployment. The repository-wide [contract-first development governance](development-governance.en.md) defines these gates.
