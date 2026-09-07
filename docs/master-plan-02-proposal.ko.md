# Master Plan 2 — Proposal Template

## 상태

**상태: reserved.** MP2는 MP1 구현이나 활성 delivery plan이 아니다. [Master Plan 1](master-plan-01-personal-assistant-core.ko.md)의 완료 증거가 생기기 전에는 기능·이슈·일정을 확정하지 않는다.

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
