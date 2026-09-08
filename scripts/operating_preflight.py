"""Exercise credential-free product paths and fail closed on unsafe deployment gaps."""
import argparse
import json
from pathlib import Path
import re
import stat
import sys
import tempfile

REPOSITORY = Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

REQUIRED_SCRIPTS = ("compose-backup.sh", "compose-restore.sh", "compose-update.sh")


def _product_probe():
    """Run the real queue, bounded adapter/MCP bridge, health, and restore path."""
    from personal_agent.bounded_execution import BoundedExecutionAdapter
    from personal_agent.portable_state import export_owner_state, restore_owner_state
    from personal_agent.quickstart_service import AgentService
    from personal_agent.quickstart_store import QuickStore
    from personal_agent.subscription_engines import SubscriptionEngines

    with tempfile.TemporaryDirectory(prefix="agentos-preflight-") as folder:
        root = Path(folder)
        source = QuickStore(root / "source")
        first_claim = not source.claimed() and source.bootstrap.is_file()
        with source.db() as db:
            db.execute("INSERT INTO notes VALUES (?,?,?)", ("fixture-note", "approved fixture note", 1))
        engine = root / "fixture-claude"
        engine.write_text(f"""#!{sys.executable}
import json, subprocess, sys
config = json.loads(open(sys.argv[sys.argv.index('--mcp-config') + 1]).read())['mcpServers']['agentos']
p = subprocess.Popen([config['command'], *config['args']], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
try:
    p.stdin.write(json.dumps({{'jsonrpc':'2.0','id':1,'method':'tools/call','params':{{'name':'list_notes','arguments':{{}}}}}}) + '\\n')
    p.stdin.flush()
    reply = json.loads(p.stdout.readline())
    print(json.dumps({{'result': 'fixture engine received ' + reply['result']['content'][0]['text']}}))
finally:
    p.terminate(); p.wait(timeout=3)
""", encoding="utf-8")
        engine.chmod(engine.stat().st_mode | stat.S_IXUSR)
        finder = lambda command: str(engine) if command == "claude" else None
        adapter = BoundedExecutionAdapter(finder=finder, runtime_root=root / "turns")
        service = AgentService(source, subscription_engines=SubscriptionEngines(finder=finder), execution_adapter=adapter)
        service.connect_subscription_engine({"engine": "claude-code", "officially_authenticated": True})
        completed = source.enqueue("/summarize", "fixture-completed")
        executed = service.run_one()
        result = source.job(completed)
        engine_round_trip = executed and result["status"] == "succeeded" and "approved fixture note" in result["response"]

        health_service = AgentService(source)
        health_service.start()
        local_health = health_service.healthy()
        health_service.stop.set()
        for thread in health_service.threads:
            thread.join(timeout=2)
        stopped = not health_service.healthy()

        queued = source.enqueue("queued before backup", "fixture-queued")
        running = source.enqueue("running before backup", "fixture-running")
        with source.db() as db:
            db.execute("UPDATE jobs SET status='running', delivery='sending' WHERE id=?", (running,))
        archive = export_owner_state(source.root, root / "owner.tar.gz")
        restored_path = restore_owner_state(archive, root / "restored")
        restored = QuickStore(restored_path)
        quarantined = all(restored.job(ident)["status"] == "interrupted" for ident in (queued, running))
        duplicate_safe = restored.enqueue("queued before backup", "fixture-queued") == queued
        replay_safe = not AgentService(restored).run_one()
        profile_excluded = not (restored_path / "engine-profile").exists() and restored.config("subscription_engine") is None

    return {
        "first_claim": first_claim,
        "local_health": local_health,
        "clean_stop": stopped,
        "bounded_engine_mcp_round_trip": engine_round_trip,
        "restore_quarantines_incomplete_work": quarantined,
        "restored_request_is_duplicate_safe": duplicate_safe and replay_safe,
        "engine_profile_excluded_from_restore": profile_excluded,
    }


def inspect(root, product_probe=None):
    """Return a secret-free readiness report without Docker or credentials."""
    root = Path(root).resolve()
    failures = []
    pyproject, compose, dockerfile = root / "pyproject.toml", root / "compose.yaml", root / "Dockerfile"
    version = None
    if pyproject.exists():
        matched = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject.read_text(encoding="utf-8"), re.M)
        version = matched.group(1) if matched else None
    if not version:
        failures.append("missing-project-version")
    compose_text = compose.read_text(encoding="utf-8") if compose.exists() else ""
    docker_text = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
    structural = {
        "loopback_binding": '127.0.0.1:${AGENTOS_PORT:-8787}:8787' in compose_text,
        "separate_owner_volume": "agentos-data:/state" in compose_text and "agentos-data:" in compose_text,
        "separate_engine_profile_volume": "agentos-engine-profile:/engine-profile" in compose_text and "agentos-engine-profile:" in compose_text,
        "nonroot_runtime": "USER agentos" in docker_text,
        "local_health_check": "healthcheck:" in compose_text and "/healthz" in compose_text,
        "recovery_scripts": all((root / "scripts" / script).is_file() for script in REQUIRED_SCRIPTS),
        # Same-container CLIs can read the owner volume with container-level
        # permissions. A dedicated IPC/isolation design is required first.
        "subscription_engine_isolated": False,
    }
    failure_names = {
        "loopback_binding": "unsafe-or-missing-loopback-binding",
        "separate_owner_volume": "missing-named-owner-volume",
        "separate_engine_profile_volume": "missing-separated-engine-profile-volume",
        "nonroot_runtime": "missing-nonroot-runtime-user",
        "local_health_check": "missing-local-health-check",
        "recovery_scripts": "missing-recovery-scripts",
        "subscription_engine_isolated": "subscription-engine-isolation-design-required",
    }
    failures.extend(failure_names[name] for name, passed in structural.items() if not passed)
    try:
        product = (product_probe or _product_probe)()
    except Exception as exc:
        product = {"probe_completed": False, "error_class": type(exc).__name__}
    for name, passed in product.items():
        if name != "error_class" and passed is not True:
            failures.append("product-check-failed-" + name.replace("_", "-"))
    return {
        "state": "ready" if not failures else "not-ready",
        "supported_version": version,
        "execution_path": "unsupported-pending-isolated-subscription-engine",
        "checks": {**structural, **product},
        "recovery_actions": failures,
        "deferred_owner_gates": [
            "explicit operating-deployment approval",
            "local runtime claim",
            "separate isolated subscription-engine installation and official login",
            "optional Telegram token entry and owner pairing",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    report = inspect(args.root)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["state"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
