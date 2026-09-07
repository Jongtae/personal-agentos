"""Redacted H3 first-work acceptance evidence for an owner BotFather bot."""
import json


def report(store, owner_confirmed=None):
    config = store.config('telegram', {})
    attestation = store.config('telegram_first_work_acceptance', {})
    if owner_confirmed is None:
        owner_confirmed = attestation.get('owner_confirmed') is True
    with store.db() as db:
        job = db.execute("""SELECT id FROM jobs
            WHERE channel LIKE 'telegram:%' AND status IN ('succeeded','partial')
              AND delivery='sent' AND provider='subscription' AND model='codex'
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
        'owner_botfather_bot': config.get('mode') == 'owner-token' and config.get('enabled') is True,
        'paired_private_owner': isinstance(config.get('user_id'), int),
        'codex_first_work_delivered': bool(job),
        'source_backed_evidence': bool(source),
        'owner_observed_live_work': bool(owner_confirmed),
    }
    return {'checks': checks, 'passed': all(checks.values())}
