# v1 acceptance

Validated on 2026-09-07:

- 72 automated tests passed.
- The installed CLI setup, authenticated note, restart persistence, and
  single-instance checks passed.
- Docker Compose built the current image, retained a named data volume, and
  reported a healthy loopback service.
- Model, Telegram pairing, document boundaries, local documents, notes, and
  bounded delegation retain their acceptance evidence from M1 and M2.

The owner must supply their own model credentials and Telegram bot token;
these secrets are never packaged in a release artifact.
