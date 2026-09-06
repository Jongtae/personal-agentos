# Roadmap

## M0 — product source and governance

Separate product development from the Homebrew tap, establish issue-first PR
work, and preserve the validated 0.2.x baseline.

Completed: `personal-agentos` preserves the product history; the v0.2.2
release feeds the Formula-only Homebrew tap; governance documentation, labels,
v1 milestone, issues, branches, PRs, and ledger records are present.

Remaining administration: the GitHub Project board awaits a token with Project
write access. It does not block product source, release, or iteration work.

## M1 — reliable personal runtime

Make model-driven capability selection, tool execution, traces, recovery, and
web/Telegram continuity dependable.

Current delivery: P1-01 is waiting for a live free-model tool-call success;
P1-01a adds the bounded local delivery loop that records and retries that gate
without advancing to M2.

## M2 — private documents and safety

Add structured document reading, source evidence, data-boundary visibility,
and explicit approval semantics.

## M3 — continuity and installation

Provide supported Homebrew and Docker Compose installations, long-running
services, backup/restore, updates, and Telegram operations.

## M4 — extensibility

Define safe tool and role manifests, migrate built-ins, and add local plugin
lifecycle management.

## M5 — v1 release

Run release acceptance for macOS and Linux/VPS, publish a versioned GitHub
Release, and update the Homebrew tap from the release artifact.
