# Personal AgentOS v1

## Problem

Personal agents currently require developer-level setup and rebuild work.
People should be able to run their own agent, select models and capabilities,
reach it through normal communication channels, and retain control of their
data and runtime.

## v1 user

A technical individual who can install Homebrew on macOS or Docker Compose on
a single Linux/VPS server.

## v1 outcome

One owner installs AgentOS, connects a model and Telegram, and uses one shared
agent from web and Telegram. The agent can perform web search, weather lookup,
connected-document reading, notes, and bounded researcher/reviewer delegation.
The UI shows work actually performed and recovers clearly from failure.

## v1 boundaries

Included: single owner, one runtime instance, web, Telegram, Homebrew,
Docker Compose, read-only connected files, explicit note/delegation requests,
model adapters, plugin/role manifests.

Excluded: multi-tenant hosting, Kubernetes as an official runtime, native
mobile apps, arbitrary shell/file writes, external service writes, and live
Codex/Claude Code execution adapters.

## Success measures

- a new user reaches first successful agent task from a documented install
- a task shows its capability execution and source evidence
- restart, update, backup, and Telegram recovery retain the owner's runtime
- every supported installation path has repeatable acceptance evidence
