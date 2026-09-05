# Personal AgentOS

> 최신 제품 방향은 [AgentOS 제품 컨셉](PRODUCT_VISION.ko.md)을 기준으로 합니다. 설치형 데스크톱 대화 앱과 개인 에이전트 생태계가 목표이며, 아래 Kubernetes 구성은 실행 기반 프로토타입 기록입니다.

사용자마다 독립된 에이전트 환경을 Kubernetes 위에 제공하는 개발 MVP입니다.
개인 Namespace, 인증 Secret, ServiceAccount, PVC, 런타임 Deployment를 생성합니다.
원본 `Jongtae/agentos`의 ISO/OS 기능은 이 프로젝트의 구현 대상이 아닙니다.

현재 도구는 결정적 `remember`, `recall`, `list_files`입니다. LLM 추론, 임의 코드 실행, 사용자 가입 UI는 아직 없습니다.

## 구조

```text
관리자 CLI → Kubernetes → 개인 Namespace
                         ├─ 인증 Secret / ServiceAccount
                         ├─ Service → Runtime Deployment (replicas=1)
                         ├─ PVC: 기억 / 작업 큐 / workspace
                         └─ 자원 한도 / NetworkPolicy
```

이번 수직 MVP에서는 개인별 SQLite를 개인 PVC에 저장합니다. 공용 DB를 여러 사용자가 공유하지 않습니다.
동일 환경을 여러 replica로 늘리는 것은 지원하지 않습니다. 업데이트는 Recreate 방식입니다.

## 로컬 실행

필수: Python 3.12+, Docker, kubectl, kind. 이 작업 환경에는 `.tools/kind`와 `.tools/kubeconfig`를 준비했습니다.
Kubernetes 설정은 프로젝트 전용 파일을 사용합니다.

```sh
# 새 환경에서 한 번 실행. 이미 생성된 클러스터에서는 생략합니다.
mkdir -p .tools
kind create cluster --name personal-agent --kubeconfig .tools/kubeconfig --wait 60s

docker build -t personal-agent:dev .
kind load docker-image personal-agent:dev --name personal-agent
python3 -m personal_agent.cli --kubeconfig .tools/kubeconfig create my-agent
python3 -m personal_agent.cli --kubeconfig .tools/kubeconfig status my-agent
python3 -m personal_agent.cli --kubeconfig .tools/kubeconfig connect my-agent
```

`kind`가 PATH에 없으면 위 명령의 `kind`를 `.tools/kind`로 바꿉니다.
`connect`는 127.0.0.1:8080에서 해당 환경으로 연결하며 Ctrl+C로 종료합니다.
이미 존재하는 환경의 `create`는 실패하며 인증 토큰을 덮어쓰지 않습니다. 생성이 중간 실패한 경우 부분 생성 자원을 운영자가 점검해야 합니다.

API: `GET /v1/me`, `GET /v1/tasks`, `POST /v1/tasks`.
`/healthz` 외에는 해당 환경 Secret의 토큰을 Bearer 인증으로 전달해야 합니다.
다음 예시는 토큰을 화면에 출력하지 않고 로컬 메모리에서 사용합니다. 먼저 `connect my-agent`를 실행하세요.

```sh
python3 - <<'PY'
import base64, json, subprocess, urllib.request
raw = subprocess.check_output(['kubectl', '--kubeconfig', '.tools/kubeconfig', '-n', 'agent-my-agent', 'get', 'secret', 'identity', '-o', 'json'])
token = base64.b64decode(json.loads(raw)['data']['token']).decode()
payload = {'action': 'remember', 'key': 'name', 'value': '나의 개인 에이전트', 'request_key': 'first-memory'}
req = urllib.request.Request('http://127.0.0.1:8080/v1/tasks', data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'})
with urllib.request.urlopen(req) as response:
    print(response.read().decode())
PY
```

`recall`은 `key`, `list_files`는 action만 받습니다. `delay_seconds`로 최대 7일 뒤 실행을 예약할 수 있습니다.
같은 `request_key`와 인자를 다시 보내면 기존 작업 ID를 반환합니다. 다른 인자로 재사용하면 거부합니다.
작업 결과는 `GET /v1/tasks`에서 최근 100건을 조회합니다.

```sh
python3 -m personal_agent.cli --kubeconfig .tools/kubeconfig pause my-agent
python3 -m personal_agent.cli --kubeconfig .tools/kubeconfig resume my-agent
```

환경을 중지해도 PVC와 인증은 보존합니다. **중지 중에는 작업을 실행하지 않으며, 기한이 지난 예약은 재개 후 실행합니다.**
사용자가 접속만 끊은 경우 실행 중인 런타임은 계속 예약을 처리합니다. 자동 깨우기는 후속 범위입니다.
kind 클러스터 자체를 삭제하면 로컬 볼륨 데이터도 잃을 수 있으므로 이것을 백업으로 취급하지 않습니다.

## 검증

```sh
python3 -m unittest discover -s tests -v
python3 scripts/e2e.py
```

E2E는 전용 로컬 클러스터에 고유한 두 테스트 환경을 생성하고 확인용으로 남깁니다.
HTTP 인증 거부, 기억/파일 분리, 별도 PVC, 중복 요청, 미접속 예약 실행, 중지/재개, Pod 교체 후 영속성을 검사합니다.
결과는 `E2E_RESULT.json`에 저장합니다. 삭제 명령은 자동 실행하지 않습니다.

## 현재 경계와 다음 단계

- 관리자 CLI는 클러스터 운영 권한을 사용합니다. 사용자 인증/가입을 대신하지 않습니다.
- 토큰 회전, TLS ingress, 공용 관리 API, 사용자 UI는 다음 단계입니다.
- NetworkPolicy를 생성하지만 기본 kind CNI에서 차단 집행을 검증하지 않았습니다. 서로 신뢰하지 않는 사용자에게 공개할 준비는 되지 않았습니다.
- 모든 도구는 제한된 로컬 연산입니다. 외부 부작용 도구는 실행 Job·승인·재시도 계약을 추가한 뒤 이식해야 합니다.
- 저장소 백업/복원, 다중 노드 장애, 저장소 용량 소진, runtime scheduler 장애 복구는 추가 검증 대상입니다.
- `.tools/`에는 kubeconfig 등 로컬 자격 자료가 있으므로 Git에서 제외합니다.

계획은 `PLAN.md`, 원본 분석은 `KUBERNETES_ARCHITECTURE.ko.md`를 참고하세요.
현재 우선순위는 개인 환경 → 실제 LLM 및 원본 도구 → 별도 작업 Job → 자동 깨우기 → 운영 격리입니다.
