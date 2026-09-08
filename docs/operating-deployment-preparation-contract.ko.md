# 소유자 승인 운영 배포 준비 계약

## 상태와 결과

`OP-01`은 소유자가 승인한 운영 배포 한 번을 준비하지만 실제로 수행하지는 않는다. 지원 후보는 저장소의 Docker Compose 경로를 사용하는 출시된 `v1.0.4` 소스 체크아웃이다. 이 경로는 non-root AgentOS 컨테이너 하나를 실행하고, 소유자 상태는 named `agentos-data` volume에만 보관하며, 서비스는 `127.0.0.1:${AGENTOS_PORT:-8787}`에만 바인딩한다.

결과물은 credential 없이 재현 가능한 준비 패키지이다. 정확한 설치·시작·설정·건강 검사·중단·복구 절차, machine-readable 로컬 preflight, 그리고 통과/실패 상태의 fixture 증거를 제공한다. 이는 Docker, Telegram, Codex, Claude Code 또는 어느 provider가 소유자에게 운영 중이라는 주장이 아니다.

## 순서가 있는 소유자 절차

1. **설치와 선택:** 소유자는 Docker Compose를 준비하고 서명/출시된 저장소 tag `v1.0.4`를 체크아웃한다. 소유자는 `python3 scripts/operating_preflight.py --root .`를 실행하며, 같은 버전, local-only port binding, named data volume, non-root container, health check, 필수 runbook script를 보고해야 한다.
2. **시작:** 소유자가 운영 배포를 승인한 뒤 `docker compose up -d --build`를 실행한다. 소유자는 local port를 선택하기 위해 `AGENTOS_PORT`만 설정할 수 있다. public host, host-home mount, Docker socket mount, credential environment variable은 이 경로에 포함되지 않는다.
3. **건강 검사와 로컬 claim:** `http://127.0.0.1:${AGENTOS_PORT:-8787}/healthz`가 `{"ok": true}`를 반환할 때까지 기다린다. 로컬 URL을 열고 새 runtime을 claim하며, UI 지시에 따라 생성된 로컬 recovery material을 보관한다.
4. **배포 승인 후 credential gate:** 소유자만 이미 설치된 subscription CLI를 선택하고 로컬 AgentOS 설정에서 공식 login을 확인한다. Telegram이 필요하면 소유자는 전용 bot을 별도로 만들고 token을 로컬 private connection store에 입력한 뒤 owner pairing을 완료한다. 이 gate는 preflight의 일부가 아니며 이 cycle은 token, OAuth client, endpoint, 외부 connection을 만들지 않는다.
5. **중단과 복구:** named data volume을 보존하려면 `docker compose down`으로 중단한다. 파괴적인 volume 교체 전에는 `scripts/compose-backup.sh ARCHIVE.tar.gz`를 사용한다. 서비스를 중단하고 빈 data volume으로 교체한 뒤 `scripts/compose-restore.sh ARCHIVE.tar.gz`를 실행하고 다시 시작한다. portable restore는 credential, session, local-folder grant, engine selection, Telegram pairing을 의도적으로 제외하므로 소유자가 복원된 runtime을 claim하고 다시 연결해야 한다.

## 건강, 실패, 복구 계약

`/healthz`는 유일한 unauthenticated local health endpoint이다. Compose는 이 endpoint에 닿지 못하면 health check가 실패해야 한다. preflight는 fail-closed다. version mismatch, non-loopback port, missing named volume, missing non-root runtime, missing health check, missing start/backup/restore script는 이름 있는 recovery action을 가진 non-ready 결과다. Docker 작업, network request, credential read, 외부 provider call은 수행하지 않는다.

지원되는 중단/복구 경로는 `down` 뒤에도 named volume을 보존하며 AgentOS가 실행 중이면 restore를 거절한다. backup과 portable restore는 계약상 secret-free다. 중단되었거나 불확실한 작업은 owner-local queue에 남아 기존 recovery surface로 처리된다. 이 준비 cycle은 engine 재시도나 Telegram 작업 재전송을 하지 않는다.

## 위협 및 데이터 경계

컨테이너는 전용 `agentos` 사용자로 실행되며 내부 `/data` volume만 받는다. host에는 loopback port 하나와 backup/restore 중 owner-chosen archive directory만 노출된다. OP-01은 host home, arbitrary host directory, Docker socket, public tunnel, broad network policy, credential, note body, prompt, provider payload를 추가하지 않는다.

preflight report에는 version, 구조적 readiness boolean, recovery identifier만 있다. owner data, private connection file, environment secret, 외부 CLI credential은 읽지 않는다.

## 자동 증거와 보류된 운영 증거

fixture는 ready, version mismatch, unsafe binding, missing health check, missing runtime user, missing recovery-script 상태를 다룬다. 저장소 CI는 기존 plan/document/ledger 검사와 전체 test suite에 이 suite를 포함한다. Docker Compose 검증은 disposable data에서만 실행할 수 있으며 owner operating evidence가 아닌 development evidence다.

운영 증거는 의도적으로 보류된다. 명시적인 소유자 승인 후 소유자는 실제 선택한 release, local health 결과, 별도로 설정한 connection health를 기록할 수 있다. 그 전에는 준비된 경로는 *deployment-ready*일 뿐 *operating-configured*가 아니다.

## 비목표

OP-01은 Docker 또는 subscription CLI를 설치하지 않고, credential을 입력하지 않으며, OAuth를 설정하지 않고, Telegram bot을 만들지 않으며, 외부 connection을 활성화하거나 public endpoint를 배포하지 않고, connector/A2A peer/marketplace capability를 추가하거나 무관한 UI를 바꾸지 않는다.
