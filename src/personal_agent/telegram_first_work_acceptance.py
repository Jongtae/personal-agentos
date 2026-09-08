"""Redacted H3 first-work acceptance evidence for an owner BotFather bot."""
import json


def report(store, owner_confirmed=None):
    config = store.config('telegram', {})
    # Delivery to the paired private chat is durable evidence.  Do not make
    # the owner repeat a chat message or click an acknowledgement merely to
    # establish that AgentOS can complete its own connection check.
    with store.db() as db:
        job = db.execute("""SELECT id FROM jobs
            WHERE request_key LIKE 'telegram-verify:%' AND channel LIKE 'telegram:%'
              AND status IN ('succeeded','partial') AND delivery='sent'
              AND provider='subscription' AND model='codex'
            ORDER BY created DESC LIMIT 1""").fetchone()
        source = False
        if job:
            rows = db.execute("SELECT detail FROM tool_events WHERE job_id=? AND tool='web_search' AND status='succeeded'", (job['id'],)).fetchall()
            for row in rows:
                try:
                    detail = json.loads(row['detail'])
                except (TypeError, ValueError):
                    detail = {}
                source = source or isinstance(detail, dict)
    checks = {
        'owner_botfather_bot': config.get('mode', 'owner-token') == 'owner-token' and config.get('enabled') is True,
        'paired_private_owner': isinstance(config.get('user_id'), int),
        'codex_first_work_delivered': bool(job),
        'source_backed_evidence': bool(source),
        'paired_delivery_confirmed': bool(job),
    }
    return {'checks': checks, 'passed': all(checks.values())}
