import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("operating_preflight", ROOT / "scripts" / "operating_preflight.py")
PREFLIGHT = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(PREFLIGHT)


class OperatingPreflightTests(unittest.TestCase):
    def fixture(self, root, binding="127.0.0.1:${AGENTOS_PORT:-8787}:8787", health=True, nonroot=True):
        root=Path(root); (root/"scripts").mkdir(); (root/"pyproject.toml").write_text('[project]\nversion = "1.0.4"\n')
        compose=f'''services:\n  agentos:\n    ports:\n      - "{binding}"\n    volumes:\n      - agentos-data:/state\n      - agentos-engine-profile:/engine-profile\n'''
        if health: compose+='    healthcheck:\n      test: ["CMD", "/healthz"]\n'
        compose+='volumes:\n  agentos-data:\n  agentos-engine-profile:\n'; (root/"compose.yaml").write_text(compose)
        (root/"Dockerfile").write_text("FROM python\n"+("USER agentos\n" if nonroot else ""))
        for name in PREFLIGHT.REQUIRED_SCRIPTS:(root/"scripts"/name).write_text("#!/bin/sh\n")

    def test_safe_structure_still_fails_closed_on_engine_isolation(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder); report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertEqual(report["state"],"not-ready")
        self.assertEqual(report["recovery_actions"],["subscription-engine-isolation-design-required"])
        self.assertTrue(report["checks"]["separate_engine_profile_volume"])

    def test_real_product_probe_exercises_runtime_and_restore(self):
        result=PREFLIGHT._product_probe(); self.assertTrue(all(result.values()),result)
        self.assertIn("bounded_engine_mcp_round_trip",result); self.assertIn("restored_request_is_duplicate_safe",result)

    def test_command_reports_named_blocker(self):
        run=subprocess.run(["python3",str(ROOT/"scripts"/"operating_preflight.py"),"--root",str(ROOT)],text=True,capture_output=True)
        self.assertEqual(run.returncode,1); report=json.loads(run.stdout)
        self.assertIn("subscription-engine-isolation-design-required",report["recovery_actions"])
        self.assertEqual(report["execution_path"],"unsupported-pending-isolated-subscription-engine")
