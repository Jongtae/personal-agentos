# 최상위 명세 완결

## 상태와 권한

**상태: TOP / issue #265 아래 active.** 이 문서는 소유자가 승인한 최상위 Goal의 권위 있는 실행 inventory다. Root [Hub v2 PRD](../PRD.md), 활성 delivery plan, 현재 Master Plan/operating contract, source code, 현재 GitHub evidence를 다룬다. Archived plan과 legacy `agentos/PRD.md` prototype은 historical input이며 구현 범위가 아니다.

승인된 row에 안전한 다음 행동이 남아 있으면 최상위 Goal은 active로 유지된다. Substep issue, PR, closeout은 그 substep만 끝낸다. Agent는 선행조건과 authority가 충족되면 이미 열거된 다음 실행 가능 row로 즉시 진행한다. 새 feature 추가, reserved proposal 복원, data/permission boundary 확대, operating deployment는 할 수 없다.

## 요구사항 inventory

| ID | 출처와 사용자 결과 | 현재 evidence | 다음 행동 | 소유자 설정 의존성 |
| --- | --- | --- | --- | --- |
| CORE-01 | Root Hub v2 PRD: local-first subscription assistant가 state, policy, tool, queue, approval, evidence, recovery 소유 | Hub module/fixture test, MP1 R-01–R-05 issue #217–#225 | Current source link 조정과 final integration 재실행 | Operating mode의 official engine login |
| CORE-02 | MP1: Personal Space, lifecycle, Drive, A2A, Calendar, ReAct, export/restore | Mock-contract evidence #180, #185, #191, #201, #205, #209, #217–#225 | Current integration regression; 새 feature 없음 | Drive/Calendar OAuth와 explicit action approval |
| MP2-01 | 완료된 conversation setting, reviewed recommendation, owner-local retrieval | Automated evidence #235, #243, #251; status는 #270에서 조정 | 다음 MP2 feature 선택 금지 | Marketplace/install/connection authority 없음 |
| STAB-01 | Telegram approved-note summary, bounded engine tool roundtrip, recovery | Fixture/CI evidence #255 | Current end-to-end mock path 재실행 | Telegram token/live provider는 owner-only |
| DEPLOY-01 | OP-01/OP-02: isolated Compose, default-deny egress, health, restore/no replay | OP-02 source `18538eabc00a20de64f4c5f5a6ac004aeda2469e`; current main에 이후 safeguard 포함 | Credential-free Compose build/start/health/stop/restore validation과 exact current candidate | Exact DNS allowlist, claim, official login, optional Telegram pairing |
| GOV-01 | Evidence-only delivery governance | Merged #263/#264와 controller test | 승인된 top-level inventory에만 확장 | 없음 |
| STATUS-01 | README, MP2 proposal, open Hub/UX epic | #270에서 조정: v1.0.4는 unsupported, MP2는 development complete, stale epic은 historical administrative record | TOP-03 audit까지 current claim 보존 | 없음 |
| LEGACY-01 | `agentos/PRD.md` prototype | Hub v2와 충돌하고 current plan에 없음 | Decision-needed; 구현/복원 금지 | 별도 owner product decision |

## 상세 추적성

| ID | 구현 상태와 선행조건 | Verification과 완료 evidence |
| --- | --- | --- |
| HUB-01 | Codex/Claude subscription adapter; 남은 predecessor 없음 | `test_subscription_engines.py`; official login이 아닌 fixture evidence |
| HUB-02 | Paired Telegram request/progress/result/recovery; STAB-01 complete | `test_telegram*.py`, `test_isolated_engine_integration.py`; token/pairing claim 없음 |
| HUB-03 | Isolated owner runtime, bounded tool, queue, approval, evidence/recovery; OP-02 complete | `test_agent_runtime.py`, `test_operating_recovery.py`, `test_isolated_engine_integration.py` |
| HUB-04 | Sensitive filtering/policy sharing이 있는 opt-in clipboard/URL context | `test_context_inbox.py`; external sharing claim 없음 |
| HUB-05 | Curated personal-records, research/briefing, project-review assistant policy | `test_mp1_release.py`; final current integration은 TOP-02 |
| HUB-06 | Web research, connected-document read, note, reviewed delegation tool boundary | `test_agent_runtime.py`, `test_documents.py`, `test_mp1_release.py` |
| HUB-07 | Connection secret을 제외한 portable export/restore | `test_operating_recovery.py`, `test_mp1_release.py` |
| DEPLOY-01 | Owner setup이 아닌 current technical gap: container build/start/health/stop/restore proof 없음 | TOP-01은 isolated credential-free Compose validation 추가 또는 concrete environment blocker 기록 필요 |
| STATUS-01 | Documentation/issue-state reconciliation은 complete | PR #270과 required CI; old epic을 조용히 close하지 않음 |

## 순서 있는 substep

| ID | 결과 | 선행조건 | 완료 evidence |
| --- | --- | --- | --- |
| TOP-00 | Inventory, governance transition, status-source reconciliation | #265 active | Complete: PR #266과 #270, bilingual inventory, plan/controller/template check, CI |
| TOP-01 | Exact credential-free deployment candidate와 Compose lifecycle proof | TOP-00 merged | build/start/health/stop/restore fixture, preflight, independent review |
| TOP-02 | Full current product integration regression 및 defect repair | TOP-01 candidate | full suite와 product-flow fixture |
| TOP-03 | Final requirement-to-evidence audit와 owner operating checklist | TOP-02 merged | 모든 row mapping, unresolved review finding 없음, candidate/procedure current |

## 소유자 운영 checklist

TOP-03 뒤에만 owner가 operating deployment를 승인할 수 있다. Exact candidate 검토, 승인한 exact provider DNS name 구성, local build/start, runtime claim, official subscription login, 원하는 경우에만 local Telegram token 입력, 해당 OAuth 승인, health와 live task 한 건 관찰, recovery material 보관, 필요 시 stop/restore 순서로 수행한다. Mock evidence는 이 action을 증명하지 않는다.

## 완료 규칙

모든 row가 current merged implementation/verification evidence를 갖거나 실제 owner operating action(login, secret entry, live connection approval) 또는 별도 owner product decision으로 명시 분류될 때만 TOP은 complete다. Implementation defect, missing technical environment proof, stale candidate, unresolved review finding은 owner setup으로 분류할 수 없다. Substep closeout, closed issue, local test, release label 하나만으로는 최상위 완료 규칙을 충족하지 않는다.
