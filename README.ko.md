# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS는 로컬 우선 개인 에이전트 런타임입니다. Mac의 사용자 범위 격리 런타임에 소유자의 메모리, 컨텍스트, 도구 권한, 작업 큐, 승인 및 증거를 보관하면서, Codex 또는 Claude Code 같은 연결된 AI 실행 엔진을 사용해 작업을 완료합니다.

일상적인 사용 화면은 개인 Telegram 봇입니다. AgentOS는 단순한 메시지 중계기가 아닙니다. 어시스턴트를 선택하고, 도구 및 데이터 경계를 적용하며, 작업 상태를 지속하고, 결과와 그 증거를 기록합니다.

## 또 하나의 채팅 화면이 아닌 개인 AI 비서

ChatGPT와 기업용 Agent 플랫폼은 범용 대화 또는 조직이 관리하는 AI 경험을 제공합니다. AgentOS는 한 사람을 위한 개인 AI 비서입니다. 선택한 AI 엔진과 도구를 조율하되, 개인 기억, 연결한 맥락, 승인, 작업 증거의 통제권은 소유자에게 남깁니다.

사용자는 여러 연결을 조작하는 절차가 아니라 원하는 결과를 말합니다. AgentOS는 그 작업에 필요한, 승인된 비서와 기능만 선택하고 실제로 실행된 일을 기록하며 중요한 외부 행동 전에는 승인을 요청합니다. 목적은 Agent 목록을 보여 주는 것이 아니라, 여러 실행자를 하나의 책임 있는 개인 비서처럼 작동하게 하는 것입니다.

이는 기업 Agent 플랫폼과 다른 신뢰 경계입니다. AgentOS는 개인 상태를 소유자 제어 런타임에 보관하고 연결한 AI 엔진을 제한된 작업자로 취급합니다. 엔진을 바꾸어도 개인의 기억, 권한, 승인 기록, 복구 가능한 작업 증거는 잃지 않아야 합니다.

- 연결할 폴더, 서비스, 도구, 비서는 소유자가 선택합니다.
- 현재 API 모델 프리뷰는 설정된 provider 정책에 따라 최근 대화 이력을 외부로 전달할 수 있습니다. 엄격한 작업 관련 최소 맥락 전달은 계획된 AgentOS 경계이며, 현재 제공되는 상호운용성 기능이라고 주장하지 않습니다.
- 외부 전송, 파일·계정 변경 등 중요한 행동은 명시적 승인을 요구합니다.
- 작업 상태와 증거는 취소, 재시도, 복구, 내보내기, 복원을 위해 남습니다.

장기 방향은 한·영 [개인 AI 비서 비전](docs/personal-ai-assistant-vision.ko.md)과 [Master Plan 1](docs/master-plan-01-personal-assistant-core.ko.md)에 기록합니다. 검토된 MCP 도구, 외부 A2A Agent, 격리된 로컬 runtime은 계획된 capability이며 아직 일반적인 설치 또는 상호운용성 제공을 주장하는 기능이 아닙니다.

## 현재 기준선

버전 1.0.3은 계속 유지되는 자체 호스팅 API 모델 프리뷰입니다. Hub v2는 활성 제품 로드맵으로, 구독 연결 실행 엔진, 소유자가 BotFather에서 만든 후 로컬 런타임에 비공개로 페어링한 Telegram 봇, 그리고 옵트인 로컬 컨텍스트 받은편지함을 포함합니다. 봇 토큰은 한 번 입력되며 로컬 비공개 연결 저장소에만 보관되고 설정, 이벤트, 내보내기, 로그 및 승인 보고서에서는 제외됩니다. [Hub v2 제품 기반](docs/agentos-hub-v2.ko.md)을 참고하세요.

소유자 상태는 `scripts/agentos-backup.py DATA ARCHIVE` 및 `scripts/agentos-restore.py ARCHIVE EMPTY_DATA`로 로컬 런타임 사이에서 이동할 수 있습니다. 아카이브는 무결성 검사를 거치며 메모리, 작업 증거, 검토된 어시스턴트 선언을 포함합니다. 자격 증명, 세션, 로컬 폴더 권한, 엔진/모델 선택 또는 Telegram 페어링은 포함하지 않습니다. 대상 런타임은 명시적으로 클레임하고 다시 연결하세요.

## 개발 설치

```sh
brew install jongtae/agentos/agentos
agentos start
```

v2 소비자 설치 프로그램이 만들어지는 동안 Homebrew 경로는 개발자와 자체 호스팅 사용자를 위한 경로로 유지됩니다.

## 거버넌스

모든 활성 Hub v2 마일스톤에는 GitHub 이슈, 브랜치, PR, 자동 검증이 있습니다. Master Plan 개발 중 외부 capability는 문서화된 contract와 mock으로 검증하며, 실제 credential과 connection은 Master Plan 전체 완료 뒤 소유자가 운영 모드로 배포할 때만 설정합니다. 전체 품질 gate는 [contract-first 개발 거버넌스](docs/development-governance.ko.md)에 정의합니다. 구현 전에 [AGENTS.md](AGENTS.md), [PRD.md](PRD.md), [TASKS.md](TASKS.md), [로드맵](docs/roadmap.md)을 읽어보세요.

활성 작업은 [Goal 실행 계약](docs/goal-execution-contract.ko.md)으로 실행 가능하게 만들며, 실행 가능한 iteration과 vision·historical record·reserved proposal을 구분합니다.
