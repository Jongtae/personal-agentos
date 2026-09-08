# OP-02 운영 준비 정정 계약

## 정정과 결과

OP-01은 당시 통과한 정적 검사에 대한 과거 증거로 남는다. 그러나 준비 완료 주장을 증명하지 못했다. release tag `v1.0.4`는 subscription-engine stabilization과 preflight 변경보다 앞서며, Compose image에는 지원되는 subscription-engine executable이나 지속되는 공식 로그인 위치가 없었다.

OP-02는 active remediation이며 deployment-ready closeout이 아니다. 현재 branch에는 isolated-engine architecture가 존재하지만, 남은 egress policy가 acceptance를 통과하고 OP-02 closeout에 정확한 merge commit이 기록될 때에만 재현 가능한 immutable 배포 후보 하나를 제공한다. 그 전까지 `v1.0.4`나 현재 branch는 지원되는 owner deployment candidate가 아니다. 이 cycle은 operating Docker image를 build하거나 owner deployment, credential configure, provider login을 수행하지 않으며 live provider execution을 증명하지 않는다.

## 지원 실행 경로

isolated-engine architecture는 이제 존재한다. Compose는 별도 `engine` service와 전용 engine-profile volume을 선언한다. 이 service에는 owner-state mount와 host port가 없고, read-only filesystem과 dropped capability로 실행되며, AgentOS와 internal network만 공유한다. AgentOS는 gateway를 통해 capability-bound task 하나를 보낸다. sidecar는 빈 working directory와 read-only sandbox에서 pinned Codex를 실행하며, authenticated MCP callback은 `list_notes`만 노출한다. host CLI나 same-container CLI는 지원 경로가 아니다.

이 architecture는 의도적으로 external provider에 도달할 수 없다. `engine-internal`은 internal-only network이며 narrow provider-egress policy가 없다. 따라서 official login과 live inference는 설계상 동작할 수 없다. preflight는 isolation check를 인정하지만 `isolated-engine-egress-policy-required`와 함께 `not-ready`를 유지한다. host-home access, Docker socket, arbitrary mount, public endpoint를 추가하지 않는 narrow owner-approved external-provider egress policy가 명세·구현·검증되기 전에는 OP-02를 close할 수 없다.

## 준비된 순서 절차

1. `python3 scripts/operating_preflight.py --root .`를 실행한다. 현재 non-zero result와 `isolated-engine-egress-policy-required` recovery action은 provider egress가 없는 동안 올바른 safety result다.
2. local-only Compose service, data-volume lifecycle, health/stop path, secret-free recovery behavior는 임시 격리 store에서 product-path test를 거친다.
3. egress policy와 isolated-engine acceptance가 완료되고 closeout commit이 기록된 뒤에만 owner procedure를 다음과 같이 확정할 수 있다. immutable commit checkout, preflight, Compose start, local claim, isolated engine official login의 명시 승인과 실행, 필요한 경우 별도 Telegram configure. 현재는 그 어떤 operating result도 주장하지 않는다.
4. restore는 stopped-only 및 empty-target-only를 유지한다. data overwrite, unfinished work 자동 replay, engine profile copy, credential recreate는 절대 하면 안 된다.

## 제품 경로 preflight

Preflight는 text가 아닌 product behavior를 검증한다. disposable isolated store에서 first claim, local service health와 clean stop, authenticated read-only MCP callback을 통과하는 실제 gateway-to-sidecar fixture round trip, archive/restore의 engine material exclusion, unfinished work quarantine, duplicate-safe queue behavior를 검증한다. 또한 separate service, profile, owner-state exclusion, internal network, read-only service, 설정된 gateway/callback 구조를 검사한다. 각 failed product check에는 named recovery action으로 fail closed해야 한다. 현재 egress-policy failure는 readiness가 아니라 남은 gap의 예상 증거다.

외부 provider access와 공식 CLI authentication은 실행하지 않으며 성공한 것으로 표현하지 않는다. test는 소유자 credential을 사용할 수 없다. fixture Codex process는 외부 network call 없이 AgentOS의 실제 gateway, sidecar command boundary, read-only MCP bridge, queue, evidence, restore code를 실행한다. 이는 development evidence일 뿐 Docker image build, official login, live provider result가 아니다.

## 경계와 비목표

host home directory, Docker socket, arbitrary host mount, public endpoint, broad network capability, credential/OAuth 입력, 외부 connection activation, Telegram setup, 운영 배포, 새 connector, marketplace, A2A capability를 추가하지 않는다. 유일한 persistent engine 위치는 전용 internal named volume이다. 향후 provider-egress rule은 narrow, explicit, owner-approved여야 하며 credential 입력과 모든 외부 activation은 이후 owner decision으로 남는다.

## 완료 증거

완료에는 v1.0.4 candidate defect, missing engine path, isolated-engine authentication boundary, narrow external-provider egress policy, startup/health, first claim, selected-engine bounded execution/tool round trip, stop/start, secret-free restore, duplicate terminal work에 대한 회귀 test가 필요하다. Goal은 독립 Terra version/path 검토, Sol 구현, Astra recovery/security 검토를 모두 통과할 때까지 active다. CI, merge, tracker/roadmap/ledger closeout은 정확한 merge commit을 참조해야 한다. 그 뒤에만 plan은 `requires-explicit-owner-approval`로 들어갈 수 있으며 Docker build, official login, live provider evidence는 별도의 owner-approved operating evidence로 남는다.
