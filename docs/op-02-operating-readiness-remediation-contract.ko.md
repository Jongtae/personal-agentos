# OP-02 운영 준비 정정 계약

## 정정과 결과

OP-01은 당시 통과한 정적 검사에 대한 과거 증거로 남는다. 그러나 준비 완료 주장을 증명하지 못했다. release tag `v1.0.4`는 subscription-engine stabilization과 preflight 변경보다 앞서며, Compose image에는 지원되는 subscription-engine executable이나 지속되는 공식 로그인 위치가 없었다.

OP-02는 active remediation이며 deployment-ready closeout이 아니다. OP-02 closeout에 정확한 merge commit이 기록될 때에만 재현 가능한 immutable 배포 후보 하나를 제공한다. 그 전까지 `v1.0.4`나 현재 branch는 지원되는 owner deployment candidate가 아니다. 이 cycle은 owner deployment나 credential configure를 수행하지 않는다.

## 지원 실행 경로

현재 Compose service에는 지원되는 subscription-engine executable이 의도적으로 없다. 같은 container에 CLI를 넣으면 그 process가 owner-state volume을 읽을 수 있으므로 profile volume만으로는 execution boundary가 되지 않는다. preflight는 host CLI나 same-container CLI가 사용 가능하다고 가장하지 않고 `subscription-engine-isolation-design-required`로 fail closed 한다.

필요한 지원 경로는 owner-state mount가 없는 별도 isolated engine runtime, 전용 official-login profile, AgentOS로 연결되는 capability-limited authenticated IPC/MCP proxy다. proxy는 선언된 per-task tool과 evidence exchange만 노출할 수 있다. 그 container에는 host home directory, Docker socket, arbitrary mount, public endpoint가 주어지면 안 된다. 이 material security boundary는 OP-02를 close하기 전에 별도 구현과 acceptance evidence가 필요하다.

## 준비된 순서 절차

1. `python3 scripts/operating_preflight.py --root .`를 실행한다. 현재 non-zero result는 isolated engine path가 생길 때까지 올바른 safety result다.
2. local-only Compose service, data-volume lifecycle, health/stop path, secret-free recovery behavior는 임시 격리 store에서 product-path test를 거친다.
3. isolated-engine acceptance가 구현되고 closeout commit이 기록되면 owner procedure는 다음으로 확정된다. immutable commit checkout, preflight, Compose start, local claim, isolated engine의 official login에 대한 명시 승인과 실행, 필요한 경우 별도 Telegram configure.
4. restore는 stopped-only 및 empty-target-only를 유지한다. data overwrite, unfinished work 자동 replay, engine profile copy, credential recreate는 절대 하면 안 된다.

## 제품 경로 preflight

Preflight는 text가 아닌 product behavior를 검증한다. disposable isolated store에서 first claim, local service health와 clean stop, bounded fixture-engine MCP round trip, archive/restore의 engine material exclusion, unfinished work quarantine, duplicate-safe queue behavior를 검증한다. Compose structural constraint도 검사한다. 각 failed product check에는 named recovery action으로 fail closed해야 한다. 현재 named isolation failure는 readiness가 아니라 남은 gap의 예상 증거다.

외부 provider와 공식 CLI authentication은 fixture로 표현한다. test는 소유자 credential을 사용할 수 없다. fixture engine은 fabricated service response가 아니라 AgentOS의 실제 bounded adapter, MCP bridge, queue, evidence, restore code를 실행해야 한다.

## 경계와 비목표

host home directory, Docker socket, arbitrary host mount, public endpoint, broad network capability, credential/OAuth 입력, 외부 connection activation, Telegram setup, 운영 배포, 새 connector, marketplace, A2A capability를 추가하지 않는다. 유일한 persistent engine 위치는 전용 internal named volume이다. credential 입력과 외부 activation은 이후 소유자의 명시적 결정이 필요하다.

## 완료 증거

완료에는 v1.0.4 candidate defect, missing engine path, isolated-engine authentication boundary, startup/health, first claim, selected-engine bounded execution/tool round trip, stop/start, secret-free restore, duplicate terminal work에 대한 회귀 test가 필요하다. Goal은 독립 Terra version/path 검토, Sol 구현, Astra recovery/security 검토를 모두 통과할 때까지 active다. CI, merge, tracker/roadmap/ledger closeout은 정확한 merge commit을 참조해야 한다. 그 뒤에만 plan은 `requires-explicit-owner-approval`로 들어갈 수 있다.
