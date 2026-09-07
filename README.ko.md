# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS는 로컬 우선 개인 에이전트 런타임입니다. Mac의 사용자 범위 격리 런타임에 소유자의 메모리, 컨텍스트, 도구 권한, 작업 큐, 승인 및 증거를 보관하면서, Codex 또는 Claude Code 같은 연결된 AI 실행 엔진을 사용해 작업을 완료합니다.

일상적인 사용 화면은 개인 Telegram 봇입니다. AgentOS는 단순한 메시지 중계기가 아닙니다. 어시스턴트를 선택하고, 도구 및 데이터 경계를 적용하며, 작업 상태를 지속하고, 결과와 그 증거를 기록합니다.

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

모든 활성 Hub v2 마일스톤에는 GitHub 이슈, 브랜치, PR, 자동화된 검증 및 이름이 지정된 실제 승인 증거가 있습니다. 구현 전에 [AGENTS.md](AGENTS.md), [PRD.md](PRD.md), [TASKS.md](TASKS.md), [로드맵](docs/roadmap.md)을 읽어보세요.
