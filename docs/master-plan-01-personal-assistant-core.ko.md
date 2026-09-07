# Master Plan 1 — Personal Assistant Core

## 상태와 목표

**상태: active — D-01 완료, I-01 미시작.** UX-05의 남은 수동 Telegram 관찰은 소유자 결정으로 release gate에서 제외됐으며, 이 결정은 해당 관찰이 통과했다는 주장이 아니다. [D-01 Personal Space 경계 계약](mp1-d01-personal-space-contract.ko.md)은 자동 설계 검증과 함께 병합되었고, I-01은 별도의 범위가 정해진 이슈와 구현 브랜치가 필요하다.

목표는 한 명의 사용자가 AgentOS 개인 공간에서 자연어로 결과를 요청하고, AgentOS가 개인 상태·승인·증거·복구를 소유한 채 검토된 연결만 조율하는 개인 비서 코어를 검증하는 것이다.

## 고정 기본값과 경계

- 기본 2nd brain은 외부 서비스가 아닌 AgentOS 개인 공간이다.
- 첫 외부 지식 연결은 Google Drive 읽기 전용이다.
- 첫 A2A 연결은 특정 상용 runtime이 아닌 호환성 test peer다.
- 외부 Agent는 사용자가 명시 요청할 때만 호출한다.
- 첫 승인형 외부 행동은 Google Calendar의 새 일정 생성이다.
- Calendar 수정·삭제, 이메일 발송, 공개 MCP/A2A URL, arbitrary runtime 설치, marketplace는 MP1 범위 밖이다.

## 설계와 구현의 반복 규칙

각 Phase는 `D-*` 설계 iteration과 `I-*` 구현 iteration으로 나뉜다. `D-*`는 사용자 결과, 데이터 흐름, 위협 모델, API/저장 contract, fixture, automated/live acceptance를 확정한다. 정상 PR 병합과 정의된 자동 검증을 통과하면 별도 제품 승인 없이 해당 `I-*` 구현 iteration을 활성화할 수 있다.

각 iteration은 GitHub 이슈, `codex/` 브랜치, 작은 의도적 커밋, PR, 자동 검증과 live evidence를 갖는다. 완료 작업은 `TASKS.md`, `docs/roadmap.md`, `docs/issue-branch-ledger.jsonl`에 함께 기록한다.

## Phase sequence

| Phase | 설계 iteration | 구현 결과 |
| --- | --- | --- |
| 1. Personal Space | D-01 개인 기억·원문·작업 증거의 경계 | I-01 기본 개인 공간과 단일 비서 UX |
| 2. Capability lifecycle | D-02 MCP/A2A/runtime registry와 on/off 상태 | I-02 검토된 카탈로그, enable/pause/disconnect, audit |
| 3. Drive knowledge | D-03 Google OAuth·읽기·공유 경계 | I-03 Google Drive 읽기 전용 connector |
| 4. A2A delegation | D-04 Agent Card·task·artifact·취소 contract | I-04 호환성 test peer와 명시 위임 |
| 5. Calendar action | D-05 incremental OAuth·미리보기·단발 승인 | I-05 Google Calendar 새 일정 생성 |
| 6. Core release | D-06 통합 ReAct 정책·fallback·acceptance | I-06 개인 비서 코어 release |

### Phase 1 — Personal Space

D-01은 명시 저장 기억, 안전한 작업 요약, 원본 source of truth, 작업 증거의 경계를 결정한다. I-01은 연결 선택을 강요하지 않는 단일 비서 UX와 기억·근거·삭제·내보내기 흐름을 제공한다.

### Phase 2 — Capability lifecycle

D-02는 capability descriptor, 상태(`available`, `connected-disabled`, `enabled`, `paused`, `auth-required`, `error`, `disconnected`), grant, secret 분리, audit contract를 결정한다. I-02는 검토된 목록에서 연결을 enable/pause/disconnect하고 실행 근거를 보는 관리 흐름을 제공한다.

### Phase 3 — Drive knowledge

D-03은 OAuth Authorization Code + PKCE, 최소 읽기 scope, 비밀값 보관, 검색 후 선택 읽기, 외부 모델 공유 경계를 결정한다. I-03은 전체 동기화 없이 Google Drive 검색·읽기·출처·health check·연결 해제를 제공한다.

### Phase 4 — A2A delegation

D-04는 test peer의 Agent Card, 명시 위임, task 상태, polling/SSE, 취소, timeout, artifact 검증을 결정한다. I-04는 A2A 결과를 신뢰하지 않는 evidence로 정규화하고, AgentOS 비밀값·로컬 경로·전체 기억을 제공하지 않는 adapter를 제공한다.

### Phase 5 — Calendar action

D-05는 Drive와 분리된 incremental OAuth write scope, 기본 primary calendar, event preview, owner-bound exact approval, payload hash, idempotency를 결정한다. I-05는 새 이벤트 생성 하나만 제공하며 수정·삭제·참석자 초대·자동 충돌 해결은 제공하지 않는다.

### Phase 6 — Core release

D-06은 개인 공간, Drive 근거, 명시 A2A 검토, Calendar 초안을 조율하는 ReAct 정책과 연결이 없을 때의 fallback을 결정한다. I-06은 새 설치부터 pause/disconnect와 export/restore까지의 end-to-end release acceptance를 실행한다.

## 완료 증거

MP1은 한 실제 사용자 흐름에서 개인 공간, Drive 근거, 명시 A2A 위임, Calendar 승인형 생성, 연결 pause/disconnect, export/restore가 각각 관찰되고 증거가 남을 때만 complete다. fixture나 mock은 실제 서비스 연결의 증거를 대체하지 않는다.

MP1 완료 뒤의 다음 선택은 [Master Plan 2](master-plan-02-proposal.ko.md) 절차를 따른다.
