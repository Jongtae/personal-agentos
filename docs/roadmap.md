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

## M6 — reviewed runtime extensions

P6-01 makes the reviewed declaration-only package registry an enforced runtime
configuration source. Built-in and installed roles follow the same bounded
host-action declarations; disabled or invalid packages cannot be selected for
delegation or expose tools. The authenticated runtime state shows package,
role, tool, permission, and enabled-state declarations alongside tool traces.

## M7 — safe Telegram task cards

P7-01 creates one persisted, editable task card for each ordinary request from
the paired private Telegram owner. Inline callbacks are bound to the owner,
private chat, exact card, and active Telegram generation; they can cancel only
jobs that remain queued. Card progress is best-effort and never retried after
an ambiguous Telegram response, avoiding duplicate cards.

P7-02 adds a separate durable notification outbox for Telegram terminal states
and document-sharing approval. Approval buttons are bound to the paired owner,
private chat, exact notification, active generation, and the current
model-and-folder fingerprint. Cards and notifications contain only status text,
never request text, secrets, or document contents; sends left ambiguous by a
restart are retained as unknown rather than replayed.

P7-03 provides the owner-run, redacted live-acceptance procedure and aggregate
evidence check for one paired Telegram account. It requires observed card
creation and cancellation, document approval, terminal notification, shared
web history, and continuity after a normal restart; it does not treat mocked
transport coverage as a real Telegram claim.

## Stage 2 follow-up — user-approved context capture

After M7 release acceptance, [#100](https://github.com/Jongtae/personal-agentos/issues/100)
is the intake point for a local-first context inbox spanning deliberate clipboard,
browser, and native-companion inputs. It is connected to the Native companion
continuity Epic [#48](https://github.com/Jongtae/personal-agentos/issues/48). The
source scopes, provenance, sensitive-data rejection, URL safety, retention, and
explicit model-sharing boundaries are detailed in `docs/context-capture-idea.ko.md`.
