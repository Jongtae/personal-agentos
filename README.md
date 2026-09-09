# AgentOS

[English](README.md) | [한국어](README.ko.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

AgentOS is a local-first personal agent built around files and folders the owner controls. It preserves source material, uses it in conversation and work, saves reusable results as ordinary files, and keeps the owner's policy, work queue, approvals, evidence, and recovery in a user-scoped runtime on their Mac.

The experience is conversation and work—including a personal Telegram bot—not a file manager. AgentOS is not only a message relay: it chooses the assistant, enforces tool and data boundaries, persists work state, and records a result and its evidence.

## A personal AI assistant, not another chat surface

ChatGPT and enterprise agent platforms provide broad conversational and organisation-managed AI experiences. AgentOS is for one owner: a personal assistant that keeps the owner's memory, connected context, approvals, and work evidence under the owner's control while coordinating selected AI engines and tools.

The owner asks for an outcome, not a sequence of integrations. AgentOS can select an approved assistant and use only the connected capabilities needed for that task; it records what actually ran and asks before consequential external actions. Its purpose is not to expose a catalogue of agents, but to make them feel like one accountable personal assistant.

This is a different trust boundary from an enterprise platform. AgentOS keeps its personal state in the owner-controlled runtime and treats connected engines as bounded workers. Changing an engine must not discard the owner's memory, permissions, approval history, or recoverable work evidence.

- The owner chooses which folders, services, tools, and assistants are connected.
- Connected reference folders are read-only by default; AgentOS writes new material only in the owner-granted managed workspace.
- Originals are preserved and remain distinct from extracted text, summaries, drafts, and final records. Search indexes are rebuildable and separate from durable work/approval/evidence/recovery/authentication state.
- The current API-model preview can send recent conversation history under its configured provider policy; strict task-relevant context minimisation is a planned AgentOS boundary, not a current interoperability claim.
- Sending externally, changing files or accounts, and other consequential actions require explicit approval.
- Work state and evidence remain available for cancellation, retry, recovery, export, and restore.

The current first-flow boundary is the bilingual [file-workspace contract](docs/file-workspace-first-experience-contract.en.md); long-term direction is in the [Personal AI Assistant Vision](docs/personal-ai-assistant-vision.en.md). Service connectors such as Drive are optional imports/actions, not the storage foundation. AgentOS does not add a cloud-sync engine or central authentication server.

## Current baseline

Version 1.0.4 and the Hub v2/Drive delivery history are retained as historical evidence, not the active product selector. The active program is [#314 file-and-folder personal workspace](https://github.com/Jongtae/personal-agentos/issues/314); its first implementation has not started. A future supported candidate must be the exact commit named by current validation, not a version label alone. The bot token remains local and excluded from settings, events, exports, logs, and acceptance reports.

Owner state can move between local runtimes with `scripts/agentos-backup.py DATA ARCHIVE` and `scripts/agentos-restore.py ARCHIVE EMPTY_DATA`. The archive is integrity-checked and carries memory, work evidence, and reviewed assistant declarations—not credentials, sessions, local-folder grants, engine/model selections, or Telegram pairing. Claim and reconnect the destination runtime explicitly.

## Development installation

```sh
brew install jongtae/agentos/agentos
agentos start
```

The Homebrew path remains for developers and self-hosters while the v2 consumer installer is built.

## Governance

Every active Hub v2 milestone has a GitHub issue, branch, PR, and automated validation. During Master Plan development, external capabilities are verified against documented contracts and mocks; the owner configures real credentials and connections only in the operating-mode deployment after the Master Plan is complete. The full [contract-first development governance](docs/development-governance.en.md) defines the quality gates. Read [AGENTS.md](AGENTS.md), [PRD.md](PRD.md), [TASKS.md](TASKS.md), and [roadmap](docs/roadmap.md) before implementation.

Active work is made executable through the [Goal Execution Contract](docs/goal-execution-contract.en.md), which separates executable iterations from vision, historical records, and reserved proposals.
