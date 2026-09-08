"""Exercise credential-free product paths and fail closed on unsafe deployment gaps."""
import argparse
import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import re
import stat
import sys
import tempfile
import threading

REPOSITORY = Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

REQUIRED_SCRIPTS = ("compose-backup.sh", "compose-restore.sh", "compose-update.sh")


def _product_probe():
    """Run the real isolated gateway/sidecar/MCP, health, and restore path."""
    from personal_agent.isolated_engine_gateway import IsolatedEngineGateway
    from personal_agent.isolated_engine_sidecar import IsolatedEngineSidecar
    from personal_agent.isolated_engine_sidecar import make_handler as make_engine_handler
    from personal_agent.portable_state import export_owner_state, restore_owner_state
    from personal_agent.quickstart import ISOLATED_MCP_PATH
    from personal_agent.quickstart import make_handler as make_agentos_handler
    from personal_agent.quickstart_service import AgentService
    from personal_agent.quickstart_store import QuickStore

    with tempfile.TemporaryDirectory(prefix="agentos-preflight-") as folder:
        root = Path(folder)
        source = QuickStore(root / "source")
        first_claim = not source.claimed() and source.bootstrap.is_file()
        with source.db() as db:
            db.execute("INSERT INTO notes VALUES (?,?,?)", ("fixture-note", "approved fixture note", 1))
        engine = root / "codex"
        engine.write_text(f"""#!{sys.executable}
import json, os, subprocess, sys
assert sys.argv[1:6] == ['exec', '--json', '--sandbox', 'read-only', '--skip-git-repo-check']
assert os.listdir('.') == []
settings = {{}}
index = 6
while index < len(sys.argv) - 1:
    assert sys.argv[index] == '-c'
    name, raw = sys.argv[index + 1].split('=', 1)
    settings[name] = json.loads(raw)
    index += 2
p = subprocess.Popen(
    [settings['mcp_servers.agentos.command'], *settings['mcp_servers.agentos.args']],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
)
def rpc(value):
    p.stdin.write(json.dumps(value) + '\\n'); p.stdin.flush()
    return json.loads(p.stdout.readline())
tools = rpc({{'jsonrpc':'2.0','id':1,'method':'tools/list','params':{{}}}})
assert [item['name'] for item in tools['result']['tools']] == ['list_notes']
denied = rpc({{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{{'name':'save_note','arguments':{{'content':'no'}}}}}})
assert denied['error']['code'] == -32601
reply = rpc({{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{{'name':'list_notes','arguments':{{}}}}}})
p.stdin.close(); p.wait(timeout=3)
text = 'fixture engine received ' + reply['result']['content'][0]['text']
print(json.dumps({{'type':'item.completed','item':{{'type':'agent_message','text':text}}}}))
""", encoding="utf-8")
        engine.chmod(engine.stat().st_mode | stat.S_IXUSR)
        sidecar = IsolatedEngineSidecar(
            "http://127.0.0.1:1" + ISOLATED_MCP_PATH,
            codex_binary=str(engine), timeout=5,
        )
        engine_server = ThreadingHTTPServer(("127.0.0.1", 0), make_engine_handler(sidecar))
        engine_thread = threading.Thread(target=engine_server.serve_forever, daemon=True)
        engine_thread.start()
        gateway = IsolatedEngineGateway(
            f"http://127.0.0.1:{engine_server.server_port}/execute", timeout=8,
        )
        service = AgentService(
            source,
            isolated_engine_adapter=gateway,
        )
        agentos_server = ThreadingHTTPServer(
            ("127.0.0.1", 0), make_agentos_handler(service),
        )
        agentos_thread = threading.Thread(target=agentos_server.serve_forever, daemon=True)
        agentos_thread.start()
        sidecar.callback_url = (
            f"http://127.0.0.1:{agentos_server.server_port}" + ISOLATED_MCP_PATH
        )
        try:
            source.put("subscription_engine", {
                "id": "codex",
                "connected_at": 0,
                "authentication": "fixture-only-no-login",
            })
            completed = source.enqueue("/summarize", "fixture-completed")
            executed = service.run_one()
            result = source.job(completed)
            engine_round_trip = (
                executed
                and result["status"] == "succeeded"
                and "approved fixture note" in result["response"]
            )
        finally:
            agentos_server.shutdown()
            agentos_server.server_close()
            agentos_thread.join(timeout=2)
            engine_server.shutdown()
            engine_server.server_close()
            engine_thread.join(timeout=2)

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
        "isolated_engine_gateway_sidecar_mcp_round_trip": engine_round_trip,
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
    engine_section = compose_text.partition("\n  engine:\n")[2].partition("\nnetworks:\n")[0]
    isolated_engine = all((
        re.search(r"(?m)^  engine:\s*$", compose_text) is not None,
        "AGENTOS_ISOLATED_ENGINE_URL: http://engine:8766/execute" in compose_text,
        "personal_agent.isolated_engine_sidecar" in engine_section,
        "http://agentos:8787/internal/isolated-engine/mcp" in engine_section,
        "agentos-engine-profile:/engine-profile" in engine_section,
        "agentos-data:/state" not in engine_section,
        "read_only: true" in engine_section,
        re.search(r"(?m)^      - engine-internal\s*$", engine_section) is not None,
        "internal: true" in compose_text,
    ))
    structural = {
        "loopback_binding": '127.0.0.1:${AGENTOS_PORT:-8787}:8787' in compose_text,
        "separate_owner_volume": "agentos-data:/state" in compose_text and "agentos-data:" in compose_text,
        "separate_engine_profile_volume": "agentos-engine-profile:/engine-profile" in compose_text and "agentos-engine-profile:" in compose_text,
        "nonroot_runtime": "USER agentos" in docker_text,
        "local_health_check": "healthcheck:" in compose_text and "/healthz" in compose_text,
        "recovery_scripts": all((root / "scripts" / script).is_file() for script in REQUIRED_SCRIPTS),
        "subscription_engine_isolated": isolated_engine,
        # The internal-only network intentionally cannot reach the provider.
        # Operating readiness requires a narrow, owner-approved egress policy;
        # preflight must not mistake architecture evidence for live readiness.
        "isolated_engine_external_egress_policy": False,
    }
    failure_names = {
        "loopback_binding": "unsafe-or-missing-loopback-binding",
        "separate_owner_volume": "missing-named-owner-volume",
        "separate_engine_profile_volume": "missing-separated-engine-profile-volume",
        "nonroot_runtime": "missing-nonroot-runtime-user",
        "local_health_check": "missing-local-health-check",
        "recovery_scripts": "missing-recovery-scripts",
        "subscription_engine_isolated": "subscription-engine-isolation-design-required",
        "isolated_engine_external_egress_policy": "isolated-engine-egress-policy-required",
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
        "execution_path": "isolated-subscription-engine-pending-egress-policy",
        "checks": {**structural, **product},
        "recovery_actions": failures,
        "deferred_owner_gates": [
            "explicit operating-deployment approval",
            "local runtime claim",
            "owner-approved engine image build and official login after egress acceptance",
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
