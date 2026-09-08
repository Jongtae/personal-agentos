# Goal Execution Contract

## Purpose

This contract makes an active AgentOS work item executable as an agent goal. A goal is not a restatement of a document title: it is a bounded commitment with an authoritative source, allowed authority, observable evidence, and a truthful terminal condition.

Use this contract for every new active design, implementation, release, remediation, operating-mode deployment, or documentation iteration. Historical records remain historical; vision documents and reserved proposals are inputs, not executable goals.

## Goal-ready record

Before activating a goal, its issue and source plan must identify all of the following.

| Field | Required meaning |
| --- | --- |
| Objective | One user-visible outcome, including the scope that must be true at completion. |
| Source of truth | The issue, active `delivery-plan.yaml` iteration, and governing contract documents. The active delivery plan decides order. |
| State and predecessors | `active` work has satisfied dependencies. `reserved`, `proposed`, archived, and blocked work is not silently activated. |
| Allowed authority | Files, runtime boundaries, repositories, and external systems the goal may change. Read-only inspection is allowed; new credentials, external actions, or scope expansion require an explicit contract. |
| Non-goals | Adjacent work deliberately excluded so the agent cannot substitute an easier or broader result. |
| Work units | Small ordered deliverables, each with its own observable result. Design work fixes contracts before dependent implementation begins. |
| Evidence | Exact automated checks, fixtures, review artifacts, and—only for operating mode—deployment health evidence. Mock and operating evidence are named separately. |
| Completion rule | A requirement-by-requirement audit proving every promised artifact, state transition, and check. |
| Blocked rule | The concrete external condition that prevents progress, recovery attempts already made, and the next authority or state change required. |

## Execution lifecycle

1. Inspect the current repository, issue, branch, plan, and prior evidence; do not rely only on prior conversation.
2. Derive a checklist from the goal-ready record. Preserve every explicit requirement and dependency.
3. Create the required issue and `codex/` branch before changing implementation or documentation. Keep commits intentional and scoped.
4. Complete the ordered work units. After each material change, test the relevant contract before moving on.
5. Run the declared complete validation set, including plan/doc parity, local-link, ledger, and full-suite checks when the source plan requires them.
6. Create a PR that distinguishes automated evidence from operating evidence, merge it, close the issue, and update `TASKS.md`, `docs/roadmap.md`, and the ledger together.
7. Perform the completion audit. Only then report the goal complete.

## Autonomous delivery-cycle delegation

For a Master Plan cycle explicitly delegated by the owner, the Agent does not wait for owner review after every small D/I iteration. Within the vision, active delivery plan, proposal, and design-contract scope, it may select one **bounded owner friction** and execute its required design → implementation → automated validation → PR merge → closeout sequence in order.

This delegation is not authority for automatic installation, permission escalation, or an operating-mode transition. The Agent must stop and request a cycle-level review before credential or OAuth configuration, a new external connection/endpoint, permission or scope expansion, a consequential external action, expansion of a personal-data boundary, a security/governance boundary change, or Master Plan cycle completion. If the next selection exceeds documented scope or requires a product judgment between equally valid owner outcomes, the Agent reports candidates and evidence instead of starting implementation.

## Terminal-state discipline

- A goal is **complete** only when current authoritative state proves every completion item. Intent, a partial fixture, an unmerged branch, or a narrow test cannot prove a broader claim.
- A goal remains **active** while a safe next action exists, even if work is difficult or incomplete.
- A goal is **blocked** only after the same concrete external blocker has recurred across three goal turns and no meaningful safe progress remains. The report must name the blocker, evidence, and the smallest required next input.
- A goal never treats a routine owner manual test, real credential, or live provider as a development blocker. Those belong to the separately documented operating-mode deployment unless the active goal explicitly authorizes it.

## Design–implementation traceability

A completed design contract is evidence that an interface and acceptance boundary were specified; it is not evidence that the capability exists. Every Master Plan design entry must name its dependent implementation entry and bilingual contract. That implementation must link back to the design, declare automated evidence, and remain inactive until a goal-ready issue authorizes it.

The delivery-plan verifier rejects a design without this mapping. It also rejects a Master Plan or capability `development_complete` claim unless every declared implementation is documented complete with its mapped automated evidence. `design_complete`, `in_progress`, and `requires-goal-ready-issue` are intentionally narrower states and must never be rendered as a user-facing capability completion or operating claim.

## Document routing

| Document kind | Goal behavior |
| --- | --- |
| Vision | Supplies direction and non-goals; never activates work by itself. |
| Master Plan | Supplies phases, completion criteria, and design/implementation ordering. Its active iteration must still be selected in the delivery plan. |
| Active delivery plan | Selects the next executable iteration and its declared validation commands. |
| Design contract | Becomes a design goal only when its predecessor is complete; it must define the dependent implementation's contracts and fixtures. |
| Issue | Carries the goal-ready record and PR closeout evidence. |
| Reserved/proposed proposal | Records a candidate and missing promotion evidence; it cannot create implementation work until promoted explicitly. |
| Operating-mode runbook | Is executable only after development completion and only with its explicit owner-controlled configuration authority. |

## Goal prompt template

Use this template when activating a goal:

```text
Execute <iteration ID and user outcome> from <authoritative issue and delivery-plan entry>.

Preserve the stated predecessors, non-goals, data/permission boundaries, and operating-mode separation. Work only within the documented authority. Implement the ordered work units, then run every declared validation and perform a requirement-by-requirement completion audit against current repository and PR state.

Do not mark the goal complete until the issue, branch, PR merge, tracker/roadmap/ledger closeout, and all stated evidence are current. Treat live credentials, real providers, and manual owner validation as out of scope unless this specific goal explicitly authorizes operating-mode work. If a single external blocker persists for three consecutive goal turns after safe recovery attempts, mark it blocked with evidence; otherwise continue.
```

## Required final report

The final report names the outcome, merged PR/issue, exact validation evidence, data/security effect, known limits, and any remaining operating-mode configuration. It must not claim an external capability is live when only mock-contract evidence exists.
