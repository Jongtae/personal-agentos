# DRIVE-LOCAL-OP-01 — Local-only Drive OAuth operating test

## Owner outcome

On the same Mac, an owner can open a local browser authorization link, complete Google OAuth, and see a redacted success or recovery result. The runtime uses only `localhost`; it is not publicly hosted.

## Authority and boundaries

Enable this path only when `AGENTOS_DRIVE_LOCAL_ONLY=1` and all required owner-local configuration values are present. The only allowed callback is `http://localhost:<port>/oauth/google/callback`. Client secrets and tokens must never be emitted in HTML, API responses, Telegram text, logs, source control, or test fixtures. This is a Mac-local browser flow; a phone cannot resolve the Mac's localhost.

## Acceptance evidence

Automated tests cover disabled configuration, explicit local-only configuration, callback validation, successful redacted completion, and failure recovery. The owner then performs the logged-in Google consent observation using a separately created local Web OAuth client; that observation is deployment evidence, not an automated claim.

## Non-goals

No public hostname, public tunnel, separate hosting, arbitrary redirect URL, raw token display, Drive-wide permission, or KakaoTalk delivery.
