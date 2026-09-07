# Delivery tracks

## Maintained baseline

| Track | Goal | Status |
| --- | --- | --- |
| v1 / M0–M6 | Self-hosted personal runtime, documents, continuity, manifests, and v1 acceptance | Complete baseline through 1.0.3 |
| v1 / M7 | Telegram task-card polish and release gate | Frozen maintenance; it does not block Hub v2 |

## Completed repository maintenance

| Issue | Goal | Status |
| --- | --- | --- |
| [#170](https://github.com/Jongtae/personal-agentos/issues/170) | Localize README navigation and prevent direct integration-branch changes | Complete; awaiting PR merge |
| [#172](https://github.com/Jongtae/personal-agentos/issues/172) | Position AgentOS as an owner-controlled personal AI control plane and record the next proposed Hub v2 outcome | Complete; merged in #173, documentation only |
| [#174](https://github.com/Jongtae/personal-agentos/issues/174) | Add bilingual personal-assistant vision and Master Plan hierarchy | Complete; merged in #175, activated MP1 documentation and reserved MP2 |
| [MP1-D-01 / #176](https://github.com/Jongtae/personal-agentos/issues/176) | Define the Personal Space memory, source, evidence, sharing, and I-01 acceptance contract | Complete; merged in #177, design only and no runtime behavior change |

## Personal AgentOS v1 release delivery

| Iteration | Goal | Status |
| --- | --- | --- |
| [V1-02 / #137](https://github.com/Jongtae/personal-agentos/issues/137) | Telegram daily-work task cards, approvals, cancellation, and truthful recovery | Implementation complete; delivery-controller validation and closeout pending |
| [V1-03 / #138](https://github.com/Jongtae/personal-agentos/issues/138) | Opt-in local documents and context in Telegram work with source evidence and external-sharing approval | Implementation complete; delivery-controller validation and closeout pending |
| [V1-04 / #139](https://github.com/Jongtae/personal-agentos/issues/139) | Docker Compose VPS health, update, backup/restore, and Telegram continuity boundaries | Implementation complete; delivery-controller validation and closeout pending |

## Active: AgentOS Hub v2

| Milestone | Goal | Issue | Status |
| --- | --- | --- | --- |
| M0 | Record Hub v2 product basis and delivery sequence | [#103](https://github.com/Jongtae/personal-agentos/issues/103) | In progress |
| M1 | Connect subscription engines without API-key setup | [#104](https://github.com/Jongtae/personal-agentos/issues/104) | Complete |
| M1.5 | Isolate each personal AgentOS runtime from the Mac host | [#109](https://github.com/Jongtae/personal-agentos/issues/109) | Planned |
| M2 | Run subscription engines through AgentOS-owned tools | [#105](https://github.com/Jongtae/personal-agentos/issues/105) | Complete |
| M3 | Deliver first work through an owner-created BotFather personal bot | [#106](https://github.com/Jongtae/personal-agentos/issues/106) | In progress |
| M4 | Build an opt-in local context inbox | [#107](https://github.com/Jongtae/personal-agentos/issues/107) | Planned |
| M5 | Provide trusted assistants and portable personal state | [#108](https://github.com/Jongtae/personal-agentos/issues/108) | In progress |

The Hub v2 Epic is [#102](https://github.com/Jongtae/personal-agentos/issues/102). The current delivery loop selects this ordered sequence only; historical v1 records remain in the ledger.

## Active: AgentOS UX v1.1

The [UX v1.1 epic](https://github.com/Jongtae/personal-agentos/issues/149) turns the delivered runtime into a minimalist personal-agent DM. Delivery follows [UX-01](https://github.com/Jongtae/personal-agentos/issues/150) through [UX-05](https://github.com/Jongtae/personal-agentos/issues/154): DM home, opt-in workspaces, Telegram continuity, human-readable safety and recovery, a guided Telegram context-selection repair, then release acceptance. UX-04 now adds redacted result-source labels and user-facing recovery next actions. UX-05 cannot tag, release, or update Homebrew until the redacted paired-Telegram acceptance also passes. See [the UX product basis](docs/ux-v1.1-personal-agent-dm.ko.md).

## Planned: Telegram Conversation UX v1.2

[UX-06 / #162](https://github.com/Jongtae/personal-agentos/issues/162) follows UX-05 acceptance. It makes the paired Telegram chat a deliberate assistant conversation: a concise acknowledgement, progress only when needed, one readable terminal answer, optional detail, and private owner-bound actions with truthful recovery.

### UX-06 — Telegram conversation bubbles

[#162](https://github.com/Jongtae/personal-agentos/issues/162) is complete. Each Telegram request now uses one status-card sequence and one terminal answer bubble; long answers use a larger readable preview and direct the owner to local web history. Automated root-suite coverage passed, and the deployed Telegram desktop flow was observed to edit the card to completion and show one terminal answer without a generic completion duplicate.
