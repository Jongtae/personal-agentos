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

Completed: P1-01 through P1-03 established live native-tool validation,
traceable capability recovery, and web/Telegram continuity evidence.

## M2 — private documents and safety

Completed: connected folders support local TXT, Markdown, PDF, DOCX, and XLSX
extraction with file and line, page, paragraph, or sheet/cell evidence.
External models are blocked from document search and reads until the owner
explicitly approves the current model-and-folder scope; that approval resets
when the model or connected folders change. Document-derived evidence cannot
be used as a public web-search query.

## M3 — continuity and installation

Completed: P3-01 and P3-02 delivered Docker Compose, persistent data, health
checks, backup/restore, and service-operation paths.

## M4 — extensibility

P4-01 delivered declarative bounded tool and role manifests
([#40](https://github.com/Jongtae/personal-agentos/issues/40)); P4-02 delivered
the local plugin install, disable, validation, and removal lifecycle
([#43](https://github.com/Jongtae/personal-agentos/issues/43)).

The design draws publicly credited lessons from
[b3rys/b3rys-team-os](https://github.com/b3rys/b3rys-team-os), without claiming
an unagreed partnership or importing its code. See the
[b3os design reference](b3os-design-reference.ko.md) for the adopted boundaries
and a future interoperability proposal.

## M5 — v1 release

Completed: P5-03 adds a reproducible product-validation gate and records
Homebrew, Compose persistence, live model/document, and Telegram restart
continuity evidence. Native clients, additional channels, and managed hosting
remain separate future product-vision work.
