# 소유자 승인 운영 배포 준비 계약

## 상태와 결과

`OP-01`은 과거 preparation evidence일 뿐이다. release된 `v1.0.4`가 지원 candidate라는 과거 주장은 active `OP-02`에서 정정되었다. 해당 tag는 stabilization과 isolated-engine 작업보다 앞선다. 배포하지 말아야 한다. 현재 branch는 별도 isolated engine, 전용 profile, capability-limited read-only MCP boundary를 선언하지만 engine network에는 의도적으로 external-provider egress가 없다. 현재 fail-closed 상태는 OP-02 remediation contract를 참조한다.

결과물은 credential 없이 재현 가능한 준비 패키지이다. 조건부 설치·시작·설정·건강 검사·중단·복구 절차, machine-readable 로컬 preflight, 그리고 local product/failure state의 fixture 증거를 제공한다. `isolated-engine-egress-policy-required`가 남아 있는 동안 deployment-ready가 아니다. 이는 Docker image가 build되었거나 Telegram, Codex, Claude Code, official login 또는 어느 live provider가 소유자에게 운영 중이라는 주장이 아니다.

## 순서가 있는 소유자 절차

1. **설치와 선택:** 현재 지원되는 owner deployment candidate는 없다. owner는 OP-02 closeout이 immutable candidate를 명시할 때까지 기다려야 한다. `python3 scripts/operating_preflight.py --root .`는 isolated service를 올바르게 인식하지만 engine이 provider에 도달할 수 없으므로 `isolated-engine-egress-policy-required`와 함께 fail closed한다.
2. **closeout 및 owner 승인 뒤에만 시작:** 향후 확정된 procedure는 owner에게 `docker compose up -d --build` 실행을 안내할 수 있다. owner는 local port를 선택하기 위해 `AGENTOS_PORT`만 설정할 수 있다. public host, host-home mount, Docker socket mount, credential environment variable은 이 경로에 포함되지 않는다. 이 contract는 현재 image가 build되거나 start된다고 주장하지 않는다.
3. **승인된 start가 성공한 뒤에만 health 및 local claim:** owner는 `http://127.0.0.1:${AGENTOS_PORT:-8787}/healthz`가 `{"ok": true}`를 반환할 때까지 기다리고, local URL을 열어 새 runtime을 claim하며, UI 지시에 따라 생성된 local recovery material을 보관한다. 이 cycle은 그러한 operating result를 기록하지 않는다.
4. **deployment 승인과 accepted egress 뒤에만 credential gate:** owner만 isolated subscription CLI를 선택하고 approved engine profile을 통해 official login을 완료한다. Telegram이 필요하면 owner는 전용 bot을 별도로 만들고 token을 local private connection store에 입력한 뒤 owner pairing을 완료한다. 이 gate는 preflight의 일부가 아니며 이 cycle은 login, token, OAuth client, endpoint, live inference, external connection을 만들거나 증명하지 않는다.
5. **중단과 복구:** named data volume을 보존하려면 `docker compose down`으로 중단한다. 파괴적인 volume 교체 전에는 `scripts/compose-backup.sh ARCHIVE.tar.gz`를 사용한다. 서비스를 중단하고 빈 data volume으로 교체한 뒤 `scripts/compose-restore.sh ARCHIVE.tar.gz`를 실행하고 다시 시작한다. portable restore는 credential, session, local-folder grant, engine selection, Telegram pairing을 의도적으로 제외하므로 소유자가 복원된 runtime을 claim하고 다시 연결해야 한다.

## 건강, 실패, 복구 계약

`/healthz`는 유일한 unauthenticated local health endpoint이다. Compose는 이 endpoint에 닿지 못하면 health check가 실패해야 한다. preflight는 fail-closed다. version mismatch, non-loopback port, missing named volume, missing non-root runtime, missing health check, missing recovery script, missing isolated-engine boundary, missing accepted engine-egress policy는 이름 있는 recovery action을 가진 non-ready 결과다. Docker 작업, credential read, 외부 provider call은 수행하지 않는다. 유일한 network activity는 temporary AgentOS와 engine HTTP server 사이의 loopback fixture round trip이다.

지원되는 중단/복구 경로는 `down` 뒤에도 named volume을 보존하며 AgentOS가 실행 중이면 restore를 거절한다. backup과 portable restore는 계약상 secret-free다. 중단되었거나 불확실한 작업은 owner-local queue에 남아 기존 recovery surface로 처리된다. 이 준비 cycle은 engine 재시도나 Telegram 작업 재전송을 하지 않는다.

## 위협 및 데이터 경계

AgentOS container는 전용 `agentos` 사용자로 실행되며 내부 `/state` owner volume만 받는다. 별도 engine service는 `/engine-profile`만 받고 owner-state mount와 host port가 없으며, read-only filesystem과 read-only Codex sandbox를 사용하고 internal gateway 및 authenticated `list_notes`-only MCP callback을 통해 AgentOS와 통신한다. host에는 loopback AgentOS port 하나와 backup/restore 중 owner-chosen archive directory만 노출된다. host home, arbitrary host directory, Docker socket, public tunnel, broad network policy, credential, live provider payload는 추가하지 않는다.

preflight report에는 version, 구조적 readiness boolean, recovery identifier만 있다. owner data, private connection file, environment secret, 외부 CLI credential은 읽지 않는다.

## 자동 증거와 보류된 운영 증거

fixture는 isolated gateway/sidecar/read-only-MCP product path, version mismatch, unsafe binding, missing health check, missing runtime user, recovery behavior, named egress-policy blocker를 다룬다. Recovery fixture는 incomplete work quarantine, automatic replay 거부, duplicate safety, portable restore의 engine profile/configuration 제외를 계속 검증한다. 저장소 CI는 기존 plan/document/ledger 검사와 전체 test suite에 이 suite를 포함한다. Static Compose check와 fixture execution은 development evidence이며 Docker image build나 owner operating evidence를 주장하지 않는다.

운영 증거는 의도적으로 보류된다. egress acceptance, OP-02 closeout, 명시적인 owner 승인 뒤에 owner는 실제 선택한 release, Docker build/start, local health 결과, official login, 별도로 설정한 connection health를 기록할 수 있다. 그 전에는 이 경로는 remediation preparation일 뿐 *deployment-ready*도 *operating-configured*도 아니다.

## 비목표

OP-01과 현재 remediation preparation은 Docker를 install/build하거나 subscription CLI를 설치하지 않고, credential 입력, official login, OAuth 설정, Telegram bot 생성, external connection activation/test, live provider inference, public endpoint 배포, connector/A2A peer/marketplace capability 추가, 무관한 UI 변경을 수행하지 않는다.
