# Top-Level Specification Completion

## Status and authority

**Status: active under TOP-01 / issue #265.** This is the authoritative execution inventory for the owner-approved top-level Goal. It covers the root [Hub v2 PRD](../PRD.md), active delivery plan, current Master Plan and operating contracts, source code, and current GitHub evidence. Archived plans and the legacy `agentos/PRD.md` prototype are historical inputs, not implementation scope.

The top-level Goal stays active while an approved row below has a safe next action. A substep issue, PR, or closeout completes only that substep. The Agent immediately advances to the next already-enumerated executable row when its predecessors and authority are satisfied. It cannot add a feature, revive a reserved proposal, widen a data or permission boundary, or perform operating deployment.

## Requirement inventory

| ID | Source and owner outcome | Current evidence | Next action | Owner-setting dependency |
| --- | --- | --- | --- | --- |
| CORE-01 | Root Hub v2 PRD: local-first subscription assistant owns state, policy, tools, queue, approvals, evidence, recovery | Hub modules and fixture tests; MP1 R-01–R-05 issues #217–#225 | Reconcile current source links and rerun final integration | Official engine login only in operating mode |
| CORE-02 | MP1: Personal Space, lifecycle, Drive, A2A, Calendar, ReAct, export/restore | Mock-contract evidence #180, #185, #191, #201, #205, #209, #217–#225 | Current integration regression; no new feature | Drive/Calendar OAuth and explicit action approval |
| MP2-01 | Completed conversation settings, reviewed recommendation, owner-local retrieval | Automated evidence #235, #243, #251 | Reconcile stale MP2 status; do not select a next MP2 feature | No marketplace/install/connection authority |
| STAB-01 | Telegram approved-note summary, bounded engine tool roundtrip, recovery | Fixture/CI evidence #255 | Re-run current end-to-end mock path | Telegram token and live provider remain owner-only |
| DEPLOY-01 | OP-01/OP-02: isolated Compose, default-deny egress, health, restore/no replay | OP-02 source `18538eabc00a20de64f4c5f5a6ac004aeda2469e`; current main includes later safeguards | Credential-free Compose build/start/health/stop/restore validation and exact current candidate | Exact DNS allowlist, claim, official login, optional Telegram pairing |
| GOV-01 | Evidence-only delivery governance | Merged #263/#264 and controller tests | Extend only to this approved top-level inventory | None |
| STATUS-01 | README, MP2 proposal, open Hub/UX epics | Conflicts: v1.0.4 support claim, MP2 `proposed`, stale open epics | Source-of-truth reconciliation before release claim | None |
| LEGACY-01 | `agentos/PRD.md` prototype | Conflicts with Hub v2 and absent from current plans | Decision-needed; do not implement or revive | Separate owner product decision |

## Ordered substeps

| ID | Outcome | Preconditions | Completion evidence |
| --- | --- | --- | --- |
| TOP-00 | Inventory, governance transition, and status-source reconciliation | #265 active | bilingual inventory, plan/controller/template checks, CI |
| TOP-01 | Exact credential-free deployment candidate and Compose lifecycle proof | TOP-00 merged | build/start/health/stop/restore fixtures, preflight, independent review |
| TOP-02 | Full current product integration regression and defect repair | TOP-01 candidate | full suite and product-flow fixtures |
| TOP-03 | Final requirement-to-evidence audit and owner operating checklist | TOP-02 merged | every row mapped; no unresolved review finding; candidate/procedure current |

## Owner operating checklist

After TOP-03, the owner alone may approve operating deployment: review the exact candidate; configure approved exact provider DNS names; build/start locally; claim the runtime; complete official subscription login; enter a local Telegram token only if desired; authorize applicable OAuth; observe health and one live task; retain recovery material; use stop/restore if required. Mock evidence never proves these actions.

## Completion rule

TOP-01 is complete only when every row has current merged implementation and verification evidence, or is explicitly classified as an owner operating setting or separate owner decision. A substep closeout, closed issue, local test, or release label alone cannot satisfy the top-level completion rule.
