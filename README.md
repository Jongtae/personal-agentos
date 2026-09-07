# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS is a local-first personal-agent runtime. It keeps an owner's memory, context, tool permissions, work queue, approvals, and evidence in a user-scoped isolated runtime on their Mac, while using connected AI execution engines such as Codex or Claude Code to complete work.

The everyday surface is a personal Telegram bot. AgentOS is not only a message relay: it chooses the assistant, enforces tool and data boundaries, persists work state, and records the result and its evidence.

## Current baseline

Version 1.0.3 remains the maintained self-hosted API-model preview. Hub v2 is the active product roadmap: subscription-connected engines, an owner-created BotFather Telegram bot paired privately to the local runtime, and an opt-in local context inbox. The bot token is entered once, kept only in the local private connection store, and is excluded from settings, events, exports, logs, and acceptance reports. See [Hub v2 product basis](docs/agentos-hub-v2.ko.md).

Owner state can move between local runtimes with `scripts/agentos-backup.py DATA ARCHIVE` and `scripts/agentos-restore.py ARCHIVE EMPTY_DATA`. The archive is integrity-checked and carries memory, work evidence, and reviewed assistant declarations—not credentials, sessions, local-folder grants, engine/model selections, or Telegram pairing. Claim and reconnect the destination runtime explicitly.

## Development installation

```sh
brew install jongtae/agentos/agentos
agentos start
```

The Homebrew path remains for developers and self-hosters while the v2 consumer installer is built.

## Governance

Every active Hub v2 milestone has a GitHub issue, branch, PR, automated validation, and named live acceptance evidence. Read [AGENTS.md](AGENTS.md), [PRD.md](PRD.md), [TASKS.md](TASKS.md), and [roadmap](docs/roadmap.md) before implementation.
