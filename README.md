# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS is a local-first personal-agent runtime. It keeps an owner's memory, context, tool permissions, work queue, approvals, and evidence in a user-scoped isolated runtime on their Mac, while using connected AI execution engines such as Codex or Claude Code to complete work.

The everyday surface is a personal Telegram bot. AgentOS is not only a message relay: it chooses the assistant, enforces tool and data boundaries, persists work state, and records the result and its evidence.

## A personal AI assistant, not another chat surface

ChatGPT and enterprise agent platforms provide broad conversational and organisation-managed AI experiences. AgentOS is for one owner: a personal assistant that keeps the owner's memory, connected context, approvals, and work evidence under the owner's control while coordinating selected AI engines and tools.

The owner asks for an outcome, not a sequence of integrations. AgentOS can select an approved assistant and use only the connected capabilities needed for that task; it records what actually ran and asks before consequential external actions. Its purpose is not to expose a catalogue of agents, but to make them feel like one accountable personal assistant.

This is a different trust boundary from an enterprise platform. AgentOS keeps its personal state in the owner-controlled runtime and treats connected engines as bounded workers. Changing an engine must not discard the owner's memory, permissions, approval history, or recoverable work evidence.

- The owner chooses which folders, services, tools, and assistants are connected.
- External engines receive only approved, task-relevant context through AgentOS boundaries.
- Sending externally, changing files or accounts, and other consequential actions require explicit approval.
- Work state and evidence remain available for cancellation, retry, recovery, export, and restore.

Planned capability connections will extend this boundary to reviewed MCP tools, external A2A agents, and isolated local runtimes. They are not available as general installation or interoperability claims today.

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
