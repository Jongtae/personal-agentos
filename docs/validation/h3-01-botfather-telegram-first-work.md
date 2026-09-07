# H3-01 BotFather Telegram first-work acceptance

This is a live owner acceptance procedure. Unit tests validate the local
boundary; they do not demonstrate that a BotFather bot or a Codex subscription
worked for an owner.

1. In Telegram BotFather, create a dedicated bot with no existing webhook.
   In authenticated local AgentOS settings, paste its token once. Confirm that
   AgentOS validates the bot and webhook state locally and generates a private,
   time-limited pairing link. Do not paste the token into this procedure,
   settings screenshots, logs, or reports.
2. Open the pairing link from the owner's private Telegram account. Confirm
   that a group or another account cannot submit work. Restart AgentOS and
   confirm it resumes polling from its durable cursor without replaying an
   uncertain delivery.
3. Connect the already officially authenticated Codex subscription. Send a
   harmless Telegram request that needs a public source, then verify the
   delivered response and its AgentOS web execution evidence.
4. In the web UI, record the first-work confirmation only after observing the
   BotFather bot, private pairing, source-backed Codex result, and Telegram
   delivery.

The resulting `telegram_first_work_acceptance` report contains only boolean
checks. It intentionally excludes message text, Telegram identifiers, pairing
links, BotFather tokens, provider credentials, capabilities, and source
payloads.
