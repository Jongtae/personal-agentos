# Personal AI Assistant Vision

## Purpose and status

This document is AgentOS's long-term north star. It is not a list of shipped or live-verified capabilities; support is determined only by the [current roadmap](roadmap.md) and named acceptance evidence.

## Identity

AgentOS is not a replacement for a general conversation platform or an organisation-managed agent platform. It is a personal AI assistant control plane that lets one owner use selected AI workers and tools while retaining ownership of memory, connected context, permissions, approvals, and work evidence.

The owner states an outcome, not an integration procedure. AgentOS coordinates only approved capabilities so they feel like one accountable personal assistant.

## Default experience

A new owner starts with **my files and folders + my assistant**. The owner entrusts material; AgentOS preserves originals, finds and uses it in conversation/work, and saves results as normal files that a later conversation can reuse. It does not make a file manager that repeatedly asks the owner to select known material, and it does not automatically turn complete conversations or model reasoning into long-term memory.

Second brains, MCP, A2A agents, and specialist runtimes are not onboarding choices. AgentOS suggests a connection only when it would help with real work, and keeps detailed controls in advanced management.

## Material and storage model

Files and folders are the primary material system. A connected reference folder is read-only by default and is searchable/readable within its approved scope; an AgentOS-managed workspace writes new material and results only within owner-granted scope. A normal sync application may synchronize owner files, but AgentOS does not add a sync engine or central authentication service.

AgentOS keeps originals distinct from extracted text/transcriptions/summaries, drafts, and final records. It keeps owner material separate from rebuildable search indexes, and keeps indexes separate from durable task, approval, evidence, recovery, and authentication state. An original is never replaced by a Markdown record or summary. Rename, edit, and delete handling must make stale results safe rather than silently reviving or modifying an original.

## Connection model

| Type | Role | AgentOS responsibility |
| --- | --- | --- |
| MCP | External data and tools | Permissions, data sharing, invocation approval, evidence |
| A2A | Delegated work to an independent specialist agent | Input scope, task state, cancellation, artifact validation |
| Runtime | An isolated local or subscription-backed worker | Execution boundary, tool allowlist, time and cost limits |

A connection can be enabled, paused, or disconnected. Enabling means the assistant may consider that capability; it never automatically permits sensitive-data sharing or an external write.

## Ownership and action principles

- Personal memory, approval history, work state, and execution evidence remain in the owner-controlled runtime.
- External workers receive only the approved minimum context required for a task.
- Reads and research may run within policy, while consequential actions such as external sending, file changes, account changes, or payments require explicit approval.
- Disconnecting removes that connection's secrets and configuration without deleting the owner's work evidence or results.
- Failed work never claims completion and leaves a state that supports cancellation, retry, or recovery.
- A folder grant is not home-directory access, arbitrary shell execution, original overwrite/delete, bulk move, or external transmission authority.
- External AI, messenger, agent, and recipient transmission is a separate policy and approval boundary from local storage.

## Optional connectors and delegation

Service connectors such as Google Drive are optional: they can import selected material or perform a service-specific action under their own boundary. They are not the required storage foundation. Informational/policy websites are likewise not OAuth/token/data relays and are not prerequisites for local file work. Delegating a material bundle or recovering a result from another person/agent remains a future explicit-boundary capability.

## Future capability acquisition

Over time, AgentOS may find and propose a reviewed agent or capability from a catalogue that can handle an owner's request. An agent completing installation, activation, or privilege escalation on its own is not the default behaviour.

This direction is considered only in a separate Master Plan after MP1. At minimum, AgentOS must first present an installation plan with the source and pinned version, licence, requested permissions and data scope, isolation method, cost, removal/recovery method, and health check; the owner must explicitly approve it. An installed capability starts disabled, and is never claimed to work before execution evidence exists.

## Non-goals and proof

MP1 does not include an open marketplace, arbitrary code execution, unbounded automatic delegation, or a central control plane that copies personal data. Future capability acquisition cannot bypass a reviewed catalogue or owner approval, isolation, and validation. AgentOS does not make general claims of superior security over ChatGPT or enterprise agent platforms; it makes the location of personal state and trust boundaries explicit.

No capability is claimed as supported in Master Plan delivery until its declared contract and automated tests pass. External credentials, OAuth clients, endpoints, and activation are configured only in the owner-controlled operating-mode deployment after the Master Plan completes; mock validation does not claim that an external connection is live. The long-term execution plan is managed in [Master Plan 1](master-plan-01-personal-assistant-core.en.md), and the next-plan selection process in [Master Plan 2](master-plan-02-proposal.en.md).
