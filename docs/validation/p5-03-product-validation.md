# P5-03 product validation

Validated on 2026-09-07 against `v1.0.0` source commit
`15e691ad5fc866e3587ca1850f0c717b0c101877`.

## Passed v1 evidence

- 77 automated tests passed.
- The Homebrew-installed CLI completed setup, authenticated note persistence,
  restart persistence, and single-instance acceptance.
- Docker Compose built a disposable image, passed `/healthz`, and retained an
  AgentOS note after container recreation with a named volume.
- The existing `gpt-4o-mini` connection completed native tool validation,
  web search, document search/read, bounded delegation, ordinary conversation,
  and note saving.
- The same live model read TXT, Markdown, PDF, DOCX, and XLSX documents with
  source-location evidence. It also passed external-model document approval
  and approval-reset acceptance.
- Documentation now reflects v1 document, Compose, backup, and manifest
  capabilities. Reviewed declaration-only plugin manifests are reachable by
  `agentos plugins` without executing third-party code.

## Remaining live acceptance

The paired Telegram account needs one final manual proof: restart AgentOS,
send a new request to the paired bot, then confirm that the web history shows
the same request and that its delivery trace is recorded. This is deliberately
not automated because it requires the owner's private account and bot token.

## Post-v1 product vision gaps

- Native desktop and mobile companion applications.
- KakaoTalk and WeChat channel feasibility and integrations.
- Managed, multi-tenant hosting with tenant isolation and billing.

The machine-readable, redacted report is produced with:

```sh
python3 scripts/product_validate.py --unit --homebrew --compose --live-model --live-telegram
```
