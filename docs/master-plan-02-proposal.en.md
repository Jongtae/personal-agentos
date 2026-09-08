# Master Plan 2 — Conversation-First Settings

## Status

**Status: proposed.** MP1 is development complete on mock-contract evidence, and the owner explicitly selected conversation-first settings as the next design friction in issue #230. D-MP2-01 and I-MP2-01 are complete on automated mock-contract evidence; no live connection or operating-mode capability is claimed.

A candidate becomes an executable goal only after promotion to an active delivery-plan iteration and a goal-ready issue under the [Goal Execution Contract](goal-execution-contract.en.md). Recording a candidate never grants implementation authority.

## Promotion criteria

Promote MP2 to `proposed` after MP1 development completion and either named operating evidence or an explicit owner selection of the next friction. The latter may promote a design-only iteration, but never claims a live capability. Complete all of the following information.

1. The user outcome and why MP1 alone cannot solve it
2. Real-use evidence and the affected owner workflow
3. Candidate type: an additional second brain, approved action, reviewed runtime, A2A agent, connection-management improvement, or reviewed capability acquisition
4. Personal-data, OAuth-scope, external-action, cost, and failure/recovery impact
5. Compatibility with MP1 state, evidence, and portable export, including required migrations
6. Minimum `D-MP2-*` and `I-MP2-*` steps, automated validation, and named live acceptance
7. A separate threat model and user-value evidence if the proposal reverses an MP1 non-goal

A capability-acquisition proposal additionally records source and pinned version, licence, installation plan, requested permissions and data scope, isolation, cost, health check, removal/recovery procedure, and the owner-approval flow. An agent may recommend a capability, but a recommendation never authorizes automatic installation, activation, or privilege escalation.

## Proposal record template

| Field | Required content |
| --- | --- |
| Problem | |
| Target owner and workflow | |
| MP1 evidence | |
| Candidate capability | |
| Data and permission boundary | |
| Non-goals | |
| Design iteration | |
| Implementation iteration | |
| Automated validation | |
| Live acceptance | |
| Rollout/recovery | |

MP2 is not a next-feature list. It is the decision record that selects one next personal-assistant friction from MP1 real-use evidence.

## Candidate record — conversation-first settings

**Candidate status: selected and proposed for D-MP2-01 design.** The owner identified a likely next friction: a personal assistant should not force its owner to leave conversation merely to understand or manage its own configuration. The explicit selection and MP1 completion promote the design work, not runtime implementation or a live capability claim.

| Field | Candidate record |
| --- | --- |
| Problem | Configuration is currently most inspectable in the local web surface, while the owner's natural control surface is conversation. Switching surfaces for ordinary status questions and lifecycle actions breaks the assistant experience. |
| Target owner and workflow | An owner asks “what is connected?”, “pause Drive”, or “disconnect this peer” in the primary conversation. The assistant explains the current state and impact, drafts a reversible change, and performs it only after an explicit confirmation. The owner can always open a local settings view for review or manual management. |
| MP1 evidence | MP1 supplies policy-owned orchestration, capability lifecycle gates, approvals, redacted evidence, deterministic recovery, and a local web API. It does not yet supply a settings-intent grammar, pending-change contract, or settings information architecture. |
| Candidate capability | Conversation-first settings control plus a Chrome Settings-like local companion: a search and category navigation with plain-language summaries, current state, a manual management view, audit/recovery links, and no duplicated control plane. Proposed categories are Assistant, Connections, Data & privacy, Approvals & activity, and Runtime & recovery. |
| Data and permission boundary | Reads may answer directly from redacted state. Changes create an owner-bound, short-lived pending change that names its exact target, before/after state, effect, and recovery. Only a matching explicit confirmation may apply it. Secrets, OAuth authorization codes, tokens, passwords, raw paths, approval IDs, and whole Personal Space records are never accepted or displayed in conversation. OAuth or sensitive credential entry hands off to authenticated local web/OS browser flow. |
| Non-goals | No arbitrary configuration mutation from natural language; no silent enable, pause, disconnect, credential replacement, or external action; no secret collection in chat; no remote hosted settings control plane; no replacement of the local manual settings screen. |
| Design iteration | [D-MP2-01 contract](d-mp2-01-conversation-settings-contract.en.md) fixes the intent vocabulary; pending-change state machine; confirmation, expiry, idempotency, cancellation, and owner binding; per-setting risk tiers; HTTP/Telegram parity; redaction; audit/export/restore; threat model; and local settings navigation/read model. |
| Implementation iteration | `I-MP2-01` may only follow the merged D-MP2-01 contract and a new goal-ready issue. It would implement a small reviewed read/change vocabulary for existing capability lifecycle state, one preview/confirm controller, and the companion settings categories. New provider connections and credentials remain separate approved flows. |
| Automated validation | Fixtures must prove read-only answers, exact preview/confirm, expired/foreign/replayed confirmation rejection, no mutation on ambiguous language, lifecycle gate enforcement, HTTP/Telegram parity, redacted transcript/evidence/export, settings navigation read model, and deterministic recovery. |
| Live acceptance | Not required for this design iteration and not claimed. I-MP2-01 must define a credential-safe operating-mode observation before any live connection claim. |
| Rollout/recovery | Begin with read-only conversational status. Ship change drafts behind explicit confirmation. Every change exposes its inverse or named recovery action; the manual local settings view remains available if the conversation path fails. |
