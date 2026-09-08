"""Check the credential-free structural prerequisites for the supported Compose path."""
import argparse
import json
import re
from pathlib import Path


REQUIRED_SCRIPTS = ("compose-backup.sh", "compose-restore.sh", "compose-update.sh")


def inspect(root):
    """Return a secret-free, fail-closed readiness report without starting anything."""
    root = Path(root).resolve()
    failures = []
    pyproject = root / "pyproject.toml"
    compose = root / "compose.yaml"
    dockerfile = root / "Dockerfile"
    version = None
    if not pyproject.exists():
        failures.append("missing-project-version")
    else:
        matched = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject.read_text(encoding="utf-8"), re.M)
        if not matched:
            failures.append("missing-project-version")
        else:
            version = matched.group(1)
            if version != "1.0.4":
                failures.append("unsupported-version")
    compose_text = compose.read_text(encoding="utf-8") if compose.exists() else ""
    if not compose_text:
        failures.append("missing-compose-file")
    else:
        if '127.0.0.1:${AGENTOS_PORT:-8787}:8787' not in compose_text:
            failures.append("unsafe-or-missing-loopback-binding")
        if 'agentos-data:/data' not in compose_text or 'agentos-data:' not in compose_text:
            failures.append("missing-named-owner-volume")
        if 'healthcheck:' not in compose_text or '/healthz' not in compose_text:
            failures.append("missing-local-health-check")
    docker_text = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
    if not docker_text or 'USER agentos' not in docker_text:
        failures.append("missing-nonroot-runtime-user")
    for script in REQUIRED_SCRIPTS:
        if not (root / "scripts" / script).is_file():
            failures.append(f"missing-{script}")
    return {
        "state": "ready" if not failures else "not-ready",
        "supported_version": version,
        "execution_path": "released-v1.0.4-docker-compose-loopback",
        "checks": {
            "loopback_binding": "unsafe-or-missing-loopback-binding" not in failures,
            "named_owner_volume": "missing-named-owner-volume" not in failures,
            "nonroot_runtime": "missing-nonroot-runtime-user" not in failures,
            "local_health_check": "missing-local-health-check" not in failures,
            "recovery_scripts": not any(item.startswith("missing-compose-") for item in failures),
        },
        "recovery_actions": failures,
        "deferred_owner_gates": [
            "explicit operating-deployment approval",
            "local runtime claim",
            "owner-confirmed subscription CLI login",
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
