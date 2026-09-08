#!/usr/bin/env python3
"""Report whether this checkout is safe for an owner to begin local setup.

The doctor is diagnostic only: it never starts Compose, changes Docker state,
reads credentials, or contacts a provider.
"""
import argparse
import json
import shutil
import socket
import subprocess
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import operating_preflight

MIN_FREE_BYTES = 5 * 1024 * 1024 * 1024


def _run(command, root):
    try:
        return subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _port_available(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def inspect(root, candidate=None, port=8787, runner=_run, disk_usage=shutil.disk_usage):
    root = Path(root).resolve()
    candidate = candidate or _candidate_from_plan(root)
    checks, blocked, actions = {}, [], []

    head = runner(["git", "rev-parse", "HEAD"], root)
    checks["candidate_checkout"] = bool(head and head.returncode == 0 and head.stdout.strip() == candidate)
    if not checks["candidate_checkout"]:
        blocked.append("candidate-checkout-mismatch")
        actions.append("git checkout " + candidate)
    dirty = runner(["git", "status", "--porcelain"], root)
    checks["clean_checkout"] = bool(dirty and dirty.returncode == 0 and not dirty.stdout.strip())
    if not checks["clean_checkout"]:
        blocked.append("checkout-has-uncommitted-changes")
        actions.append("commit, stash, or discard only your own checkout changes before setup")

    docker = runner(["docker", "version", "--format", "{{.Server.Version}}"], root)
    checks["docker_daemon"] = bool(docker and docker.returncode == 0 and docker.stdout.strip())
    if not checks["docker_daemon"]:
        blocked.append("docker-daemon-unavailable")
        actions.append("start Docker Desktop, then rerun agentos_doctor.py")
    compose = runner(["docker", "compose", "version"], root)
    checks["compose_plugin"] = bool(compose and compose.returncode == 0)
    if not checks["compose_plugin"]:
        blocked.append("docker-compose-plugin-unavailable")
        actions.append("install or enable the Docker Compose plugin")
    if checks["docker_daemon"] and checks["compose_plugin"]:
        config = runner(["docker", "compose", "-f", "compose.yaml", "config", "--quiet"], root)
        checks["compose_config"] = bool(config and config.returncode == 0)
        if not checks["compose_config"]:
            blocked.append("compose-config-invalid")
            actions.append("inspect compose.yaml and rerun doctor; do not start the stack")
    else:
        checks["compose_config"] = False

    checks["loopback_port_available"] = _port_available(port)
    if not checks["loopback_port_available"]:
        blocked.append("loopback-port-in-use")
        actions.append(f"choose an unused local AGENTOS_PORT instead of {port}")
    free = disk_usage(root).free
    checks["sufficient_disk_space"] = free >= MIN_FREE_BYTES
    if not checks["sufficient_disk_space"]:
        blocked.append("insufficient-disk-space")
        actions.append("free at least 5 GiB before building local images")

    preflight = operating_preflight.inspect(root)
    checks["agentos_preflight"] = preflight["state"] == "ready"
    if not checks["agentos_preflight"]:
        blocked.extend(preflight["recovery_actions"])
        actions.append("run python3 scripts/operating_preflight.py --root . for structural recovery details")
    return {
        "state": "ready" if not blocked else "blocked",
        "candidate": candidate,
        "port": port,
        "checks": checks,
        "blocked": blocked,
        "safe_next_commands": actions,
        "deferred_owner_actions": [
            "explicit operating-deployment approval",
            "set approved exact provider DNS allowlist",
            "run docker compose up -d --build after explicit approval",
            "claim the local runtime",
            "complete official engine login",
            "optionally enter Telegram token and OAuth settings",
            "observe health and one live task",
        ],
        "security_note": "No credential, Docker credential helper, owner-home file, provider, Telegram, OAuth, DNS, or TLS endpoint was read or contacted.",
    }


def _candidate_from_plan(root):
    plan = json.loads((root / "delivery-plan.yaml").read_text(encoding="utf-8"))
    return plan["completion_claims"]["TOP"]["deployment_candidate"]["commit"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--candidate")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)
    report = inspect(args.root, args.candidate, args.port)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["state"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
