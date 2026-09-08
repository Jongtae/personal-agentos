import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("operating_preflight", ROOT / "scripts" / "operating_preflight.py")
PREFLIGHT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREFLIGHT)


class OperatingPreflightTests(unittest.TestCase):
    def fixture(self, root, *, version="1.0.4", binding="127.0.0.1:${AGENTOS_PORT:-8787}:8787", health=True, nonroot=True, scripts=True):
        root = Path(root)
        (root / "scripts").mkdir()
        (root / "pyproject.toml").write_text(f'[project]\nversion = "{version}"\n')
        compose = f"services:\n  agentos:\n    ports:\n      - \"{binding}\"\n    volumes:\n      - agentos-data:/data\n"
        if health:
            compose += "    healthcheck:\n      test: [\"CMD\", \"/healthz\"]\n"
        compose += "volumes:\n  agentos-data:\n"
        (root / "compose.yaml").write_text(compose)
        (root / "Dockerfile").write_text("FROM python\n" + ("USER agentos\n" if nonroot else ""))
        if scripts:
            for name in PREFLIGHT.REQUIRED_SCRIPTS:
                (root / "scripts" / name).write_text("#!/bin/sh\n")

    def test_ready_fixture_is_credential_free_and_names_owner_gates(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder)
            report = PREFLIGHT.inspect(folder)
        self.assertEqual(report["state"], "ready")
        self.assertEqual(report["supported_version"], "1.0.4")
        self.assertIn("optional Telegram token entry and owner pairing", report["deferred_owner_gates"])
        self.assertNotIn("token", str(report["checks"]).lower())

    def test_unsafe_or_incomplete_fixture_fails_closed_with_named_recovery(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder, version="9.9.9", binding="0.0.0.0:8787:8787", health=False, nonroot=False, scripts=False)
            report = PREFLIGHT.inspect(folder)
        self.assertEqual(report["state"], "not-ready")
        self.assertEqual(report["recovery_actions"], [
            "unsupported-version", "unsafe-or-missing-loopback-binding", "missing-local-health-check",
            "missing-nonroot-runtime-user", "missing-compose-backup.sh", "missing-compose-restore.sh", "missing-compose-update.sh",
        ])

    def test_command_returns_nonzero_for_non_ready_fixture(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder, health=False)
            run = subprocess.run(["python3", str(ROOT / "scripts" / "operating_preflight.py"), "--root", folder], text=True, capture_output=True)
        self.assertEqual(run.returncode, 1)
        self.assertIn('"state": "not-ready"', run.stdout)
