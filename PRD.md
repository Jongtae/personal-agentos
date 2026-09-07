# AgentOS Hub v2

## Product outcome

A Mac owner installs AgentOS, connects a ChatGPT or Claude subscription without an API key, creates a personal Telegram bot, and assigns real work to trusted assistants. AgentOS retains the owner's memory, context, tool policy, approvals, and evidence across engine changes.

## Primary user

A non-developer Mac user who already uses a ChatGPT or Claude subscription and wants a personal agent they can reach through Telegram.

## Core capabilities

- Assistant-first setup with Codex and Claude Code as default execution engines.
- Telegram personal bot for requests, progress, approvals, and results.
- AgentOS-owned MCP tools for web research, connected documents, notes, and reviewed delegation.
- User-scoped isolated AgentOS runtime, local-first task queue, evidence, recovery, and opt-in context inbox.
- Three curated assistants: personal records, research and briefing, project review.
- Portable owner export and restore; managed hosting remains an explicit opt-in future path.

## Boundaries

Included: local Mac runtime, subscription-engine connection, owner-created BotFather personal-bot pairing, read-only research/document work, note writes, explicit approval, opt-in clipboard/URL context, export/restore without connection secrets.

Excluded: API key as a consumer prerequisite, arbitrary shell or file writes, automatic cloud failover, persistent relay content storage, unmanaged community assistants, user-managed Kubernetes installation, native mobile app, and additional messengers. Kubernetes remains an internal managed-hosting isolation option.

## Success measures

- A new owner completes installation, official engine login, personal-bot creation, and a first source-backed Telegram task without an API key.
- AgentOS shows work state and evidence while preventing engines from reaching undeclared host capabilities.
- Restart preserves local state and Telegram updates are processed after reconnect.
- Context capture rejects sensitive values and shares data externally only by assistant policy.
