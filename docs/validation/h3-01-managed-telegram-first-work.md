# H3-01 managed Telegram first-work acceptance

This is a live owner acceptance procedure. Unit tests validate the boundary;
they do not demonstrate that Telegram, the managed control plane, or a Codex
subscription worked for an owner.

1. Deploy the managed-bot relay with a credential held only by the control
   plane. Configure its `ManagedBotProvisioner` implementation in the isolated
   owner runtime. Do not paste a BotFather token into AgentOS.
2. In the authenticated AgentOS settings, create a managed personal bot and
   open its one-time pairing link from the owner's private Telegram account.
   Confirm that a group or another account cannot submit work.
3. Connect the already officially authenticated Codex subscription. Send a
   harmless Telegram request that needs a public source, and verify the
   delivered response plus its AgentOS web execution evidence.
4. In the web UI, record the first-work confirmation only after observing the
   bot, private pairing, source-backed Codex result, and Telegram delivery.

The resulting `telegram_first_work_acceptance` report contains only boolean
checks. It intentionally excludes message text, Telegram identifiers, relay
capabilities, provider credentials, and source payloads.

Known deployment prerequisite: this repository provides the narrow runtime
interface but not a managed control-plane service. A live pass must be recorded
only by the deployment that supplies that service and its transient relay.
