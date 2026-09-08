#!/usr/bin/env python3
"""Report whether this checkout is safe for an owner to begin local setup.

The doctor is diagnostic only: it never starts Compose, changes Docker state,
reads credentials, or contacts a provider.
"""
import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import operating_preflight

MIN_FREE_BYTES = 5 * 1024 * 1024 * 1024


def _run(command, root, env=None):
    try:
        return subprocess.run(
            command, cwd=root, text=True, capture_output=True, timeout=10, env=env
        )
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


def _candidate_from_plan(root):
    plan = json.loads((root / "delivery-plan.yaml").read_text(encoding="utf-8"))
    return plan["completion_claims"]["TOP"]["deployment_candidate"]["commit"]


def _git_head(runner, root, env):
    head = runner(["git", "rev-parse", "HEAD"], root, env=env)
    return head.stdout.strip() if head and head.returncode == 0 else None


def _compose_loopback_port(root):
    compose = root / "compose.yaml"
    if not compose.is_file():
        return None
    text = compose.read_text(encoding="utf-8")
    match = re.search(r'(?m)^    ports:\n(?:      - .*?\n)+', text)
    if not match:
        return None
    block = match.group(0)
    bound = re.search(r'(?m)^      - "127\.0\.0\.1:([^:"]+):8787"\s*$', block)
    if bound:
        raw = bound.group(1).strip()
    else:
        return None
    if raw.startswith("${AGENTOS_PORT:-") and raw.endswith("}"):
        return int(os.environ.get("AGENTOS_PORT", raw.split(":-", 1)[1][:-1]))
    try:
        return int(raw)
    except ValueError:
        return None


def _diagnostic_environment(temporary):
    environment = os.environ.copy()
    environment.pop("HOME", None)
    environment.pop("DOCKER_HOST", None)
    environment.pop("DOCKER_CONTEXT", None)
    environment.pop("COMPOSE_PROFILES", None)
    environment.pop("COMPOSE_FILE", None)
    environment["HOME"] = str(temporary / "home")
    Path(environment["HOME"]).mkdir(parents=True, exist_ok=True)
    docker_config = temporary / "docker-config"
    docker_config.mkdir()
    (docker_config / "config.json").write_text("{}", encoding="utf-8")
    environment["DOCKER_CONFIG"] = str(docker_config)
    return environment


def inspect(root, candidate=None, port=None, runner=_run, disk_usage=shutil.disk_usage):
    root = Path(root).resolve()
    plan_candidate = _candidate_from_plan(root)
    expected_candidate = candidate
    checks, blocked, actions = {}, [], []

    with tempfile.TemporaryDirectory(prefix="agentos-doctor-") as temporary:
        temporary = Path(temporary)
        environment = _diagnostic_environment(temporary)
        env_file = temporary / "agentos-empty.env"
        env_file.write_text("", encoding="utf-8")

        head = _git_head(runner, root, env=environment)
        if candidate is None:
            candidate = head
        checks["candidate_checkout"] = True if candidate is None else bool(head == candidate)
        if not checks["candidate_checkout"]:
            candidate_for_check = expected_candidate or plan_candidate
            blocked.append("candidate-checkout-mismatch")
            actions.append(
                "git worktree add --detach /tmp/agentos-doctor-checkout "
                f"{candidate_for_check} && cp scripts/agentos_doctor.py /tmp/agentos-doctor-checkout/scripts/agentos_doctor.py && "
                f"python3 /tmp/agentos-doctor-checkout/scripts/agentos_doctor.py --root /tmp/agentos-doctor-checkout --candidate {candidate_for_check}"
            )

        dirty = runner(["git", "status", "--porcelain"], root, env=environment)
        checks["clean_checkout"] = bool(
            dirty and dirty.returncode == 0 and not dirty.stdout.strip()
        )
        if not checks["clean_checkout"]:
            blocked.append("checkout-has-uncommitted-changes")
            actions.append("commit, stash, or discard only your own checkout changes before setup")

        docker = runner(
            ["docker", "version", "--format", "{{.Server.Version}}"], root, environment
        )
        checks["docker_daemon"] = bool(docker and docker.returncode == 0 and docker.stdout.strip())
        if not checks["docker_daemon"]:
            blocked.append("docker-daemon-unavailable")
            actions.append("start Docker Desktop, then rerun agentos_doctor.py")

        compose = runner(["docker", "compose", "version"], root, environment)
        checks["compose_plugin"] = bool(compose and compose.returncode == 0)
        if not checks["compose_plugin"]:
            blocked.append("docker-compose-plugin-unavailable")
            actions.append("install or enable the Docker Compose plugin")

        if checks["docker_daemon"] and checks["compose_plugin"]:
            config = runner(
                [
                    "docker",
                    "compose",
                    "--env-file",
                    str(env_file),
                    "-f",
                    "compose.yaml",
                    "config",
                    "--quiet",
                ],
                root,
                environment,
            )
            checks["compose_config"] = bool(config and config.returncode == 0)
            if not checks["compose_config"]:
                blocked.append("compose-config-invalid")
                actions.append("inspect compose.yaml and rerun doctor; do not start the stack")
        else:
            checks["compose_config"] = False

    if port is None:
        port = int(os.environ.get("AGENTOS_PORT", 8787))
    checks["loopback_port_available"] = _port_available(port)
    if not checks["loopback_port_available"]:
        blocked.append("loopback-port-in-use")
        actions.append(f"choose an unused local AGENTOS_PORT instead of {port}")

    compose_port = _compose_loopback_port(root)
    checks["compose_loopback_port_match"] = True if compose_port is None else compose_port == port
    if compose_port is not None and compose_port != port:
        blocked.append("compose-loopback-port-mismatch")
        actions.append(
            f"set --port {compose_port} (or AGENTOS_PORT={compose_port}) to match compose binding"
        )

    free = disk_usage(root).free
    checks["sufficient_disk_space"] = free >= MIN_FREE_BYTES
    if not checks["sufficient_disk_space"]:
        blocked.append("insufficient-disk-space")
        actions.append("free at least 5 GiB before building local images")

    checks["plan_candidate"] = plan_candidate
    checks["configured_candidate"] = candidate
    checks["candidate_requested"] = expected_candidate is not None

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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=ROOT)
    parser.add_argument("--candidate", help="expected immutable deployment candidate SHA")
    parser.add_argument("--port", type=int, default=None)
    args = parser.parse_args(argv)
    report = inspect(args.root, args.candidate, args.port)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["state"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
