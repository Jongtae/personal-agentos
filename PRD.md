# AgentOS — File-and-folder personal workspace

## Product outcome

An owner entrusts material from approved files and folders. AgentOS preserves originals, finds and understands material in conversation/work, saves reusable outputs as ordinary files, and retains the owner's work policy, approvals, evidence, and recovery across restarts and engine changes.

## Primary user

A non-developer Mac user who wants to use their own materials through a personal agent without repeatedly selecting files or manually reorganising folders.

## Core capabilities

- Connected owner reference folders, read-only by default, searched/read in their approved scope without repeated selection.
- An AgentOS-managed workspace that writes new materials and results only within owner-granted scope.
- Conversation and Telegram paths for requests, progress, explicit approvals, source evidence, recovery, and reuse after restart.
- Original/derived/draft/final provenance, rebuildable search indexes, and durable task/approval/evidence/recovery/auth state kept distinct.
- Bounded subscription execution engines and optional connectors/delegation; AgentOS retains policy and personal state.

## Boundaries

Included: local Mac runtime; owner-approved file/folder connection; read-only reference material; managed-workspace result files; conversation/Telegram work; explicit approval; provenance; durable recovery; and export/restore without connection secrets.

Excluded: automatic full-conversation memory, arbitrary shell or broad home-folder access, original overwrite/deletion or bulk moves without separate authority, automatic cloud sync, central OAuth/authentication, persistent relay content storage, unapproved external transmission, and destructive migration. OCR, transcription, video analysis, advanced large-library search, cloud-only import, and material-bundle delegation are follow-up work.

## Success measures

- An owner saves a meeting note or summary as TXT/MD from approved material and finds/reuses it after app restart in another conversation.
- AgentOS preserves originals, prevents traversal/out-of-grant access, and records source/result relationships.
- Search indexes can be rebuilt without losing task, approval, evidence, recovery, or authentication state.
- External AI, messenger, and agent transmission remains separately controlled and evidence distinguishes mock, local-file, and operating observations.
