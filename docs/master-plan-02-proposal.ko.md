# Master Plan 2 — Proposal Template

## 상태

**상태: reserved.** MP2는 MP1 구현이나 활성 delivery plan이 아니다. [Master Plan 1](master-plan-01-personal-assistant-core.ko.md)의 완료 증거가 생기기 전에는 기능·이슈·일정을 확정하지 않는다.

후보는 활성 delivery-plan iteration으로 승격되고 [Goal 실행 계약](goal-execution-contract.ko.md)에 따른 goal-ready issue가 생긴 뒤에만 실행 가능한 goal이 된다. 후보를 기록하는 일은 구현 authority를 주지 않는다.

## 승격 조건

MP1의 named live acceptance와 실제 사용 중 발견된 가장 큰 개인 비서 마찰을 기록한 뒤에만 MP2를 `proposed`로 승격한다. 다음 정보를 모두 채운다.

1. 사용자 결과와 MP1만으로 해결할 수 없는 이유
2. 실제 사용 증거와 영향을 받은 owner workflow
3. 후보 유형: 추가 2nd brain, 추가 승인형 행동, 검토된 runtime, 추가 A2A Agent, 연결 관리 개선, 또는 검토된 capability acquisition
4. 개인 데이터, OAuth scope, 외부 행동, 비용, 실패·복구 영향
5. MP1 상태·증거·portable export와의 호환성 및 migration 필요 여부
6. 최소 `D-MP2-*`와 `I-MP2-*` 단계, 자동화 검증, named live acceptance
7. MP1 비목표를 뒤집는 경우의 별도 위협 모델과 사용자 가치 근거

capability acquisition 제안에는 출처와 고정 버전, 라이선스, 설치 계획, 요청 권한·데이터 범위, 격리, 비용, health check, 제거·복구 절차와 소유자 승인 흐름을 추가로 기록한다. Agent의 추천은 가능하지만 자동 설치·활성화·권한 상승은 제안만으로 허용하지 않는다.

## 제안 기록

| 항목 | 채울 내용 |
| --- | --- |
| 문제 | |
| 대상 사용자와 workflow | |
| MP1 evidence | |
| 후보 capability | |
| 데이터와 권한 경계 | |
| 비목표 | |
| 설계 iteration | |
| 구현 iteration | |
| automated validation | |
| live acceptance | |
| rollout/recovery | |

MP2는 다음 기능 목록이 아니라, MP1 실사용 증거를 바탕으로 다음 가장 큰 개인 비서 마찰 하나를 선택하는 의사결정 문서다.

## 후보 기록 — 대화 우선 설정

**후보 상태: 기록됨, proposed 아님.** 소유자는 개인 비서의 설정을 이해하거나 관리하기 위해 대화를 떠나야 하는 마찰을 다음 후보로 식별했다. 이는 제품 방향일 뿐 MP1 실사용 증거가 아니므로 MP2를 활성화하거나 `delivery-plan.yaml`을 변경하지 않는다.

| 항목 | 후보 기록 |
| --- | --- |
| 문제 | 현재 설정은 로컬 웹 화면에서 가장 잘 확인할 수 있지만, 소유자의 자연스러운 제어면은 대화다. 일상적인 상태 질문과 lifecycle 행동마다 화면을 전환하면 비서 경험이 끊긴다. |
| 대상 사용자와 workflow | 소유자는 주 대화에서 “무엇이 연결되어 있어?”, “Drive를 일시 정지해줘”, “이 peer를 연결 해제해줘”라고 요청한다. 비서는 현재 상태와 영향을 설명하고 되돌릴 수 있는 변경 초안을 만든 뒤 명시 확인이 있을 때만 실행한다. 소유자는 언제든 검토와 수동 관리를 위한 로컬 설정 화면을 열 수 있다. |
| MP1 evidence | MP1은 정책 소유 orchestration, capability lifecycle gate, approval, redacted evidence, 결정적 recovery, 로컬 웹 API를 제공한다. 아직 settings-intent grammar, pending-change contract, settings information architecture는 제공하지 않는다. |
| 후보 capability | 대화 우선 설정 제어와 Chrome Settings형 로컬 보조 화면: 검색과 category navigation, 평이한 요약, 현재 상태, 수동 관리 화면, audit/recovery link를 제공하고 control plane을 중복하지 않는다. 제안 category는 Assistant, Connections, Data & privacy, Approvals & activity, Runtime & recovery다. |
| 데이터와 권한 경계 | 읽기는 redacted state에서 바로 답할 수 있다. 변경은 정확한 target, before/after state, effect, recovery를 적은 소유자 귀속·짧은 수명의 pending change를 만든다. 일치하는 명시 확인만 이를 적용할 수 있다. Secret, OAuth authorization code, token, password, raw path, approval ID, Personal Space 전체 record는 대화에서 받거나 표시하지 않는다. OAuth나 민감 credential 입력은 인증된 로컬 웹/OS browser 흐름으로 넘긴다. |
| 비목표 | 자연어에서 임의 설정 변경, silent enable/pause/disconnect/credential 교체/외부 행동, 대화에서 secret 수집, 원격 hosted settings control plane, 로컬 수동 설정 화면의 대체는 범위가 아니다. |
| 설계 iteration | `D-MP2-01`은 먼저 intent vocabulary, pending-change state machine, confirmation·expiry·idempotency·cancellation·owner binding, setting별 risk tier, HTTP/Telegram parity, redaction, audit/export/restore, threat model, 로컬 settings navigation/read model을 정의해야 한다. |
| 구현 iteration | `I-MP2-01`은 승인된 설계 뒤에만 진행할 수 있다. 기존 capability lifecycle state에 대한 작은 검토된 read/change vocabulary, 하나의 preview/confirm controller, 보조 settings category를 구현한다. 새 provider connection과 credential은 별도 승인 흐름으로 남긴다. |
| automated validation | Fixture는 read-only answer, 정확한 preview/confirm, 만료/다른 owner/replay confirmation 거절, 모호한 언어에서 mutation 없음, lifecycle gate 강제, HTTP/Telegram parity, redacted transcript/evidence/export, settings navigation read model, 결정적 recovery를 증명해야 한다. |
| live acceptance | 아직 정의하거나 요구하지 않는다. 승격 전에는 반복해서 settings surface가 필요했던 owner workflow, 실제 마찰, credential을 노출하지 않는 운영 모드 안전 관찰을 기록한다. |
| rollout/recovery | 대화형 read-only status부터 시작한다. 변경 초안은 명시 확인 뒤에만 제공한다. 모든 변경은 inverse 또는 이름 있는 recovery action을 보여주며, 대화 경로가 실패해도 로컬 수동 설정 화면을 계속 사용할 수 있다. |
