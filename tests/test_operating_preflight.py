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
        compose=f'''services:\n  agentos:\n    ports:\n      - "{binding}"\n    volumes:\n      - agentos-data:/state\n    environment:\n      AGENTOS_ISOLATED_ENGINE_URL: http://engine:8766/execute\n'''
        if health: compose+='    healthcheck:\n      test: ["CMD", "/healthz"]\n'
        compose+='''  engine:\n    command: ["python", "-m", "personal_agent.isolated_engine_sidecar", "--callback", "http://agentos:8787/internal/isolated-engine/mcp"]\n    volumes:\n      - agentos-engine-profile:/engine-profile\n    networks:\n      - engine-internal\n    read_only: true\nnetworks:\n  engine-internal:\n    internal: true\nvolumes:\n  agentos-data:\n  agentos-engine-profile:\n'''; (root/"compose.yaml").write_text(compose)
        (root/"Dockerfile").write_text("FROM python\n"+("USER agentos\n" if nonroot else ""))
        for name in PREFLIGHT.REQUIRED_SCRIPTS:(root/"scripts"/name).write_text("#!/bin/sh\n")

    def test_isolated_structure_still_fails_closed_on_missing_egress_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder); report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertEqual(report["state"],"not-ready")
        self.assertEqual(report["recovery_actions"],["isolated-engine-egress-policy-required"])
        self.assertTrue(report["checks"]["separate_engine_profile_volume"])
        self.assertTrue(report["checks"]["subscription_engine_isolated"])
        self.assertFalse(report["checks"]["isolated_engine_external_egress_policy"])

    def test_real_product_probe_exercises_runtime_and_restore(self):
        result=PREFLIGHT._product_probe(); self.assertTrue(all(result.values()),result)
        self.assertIn("isolated_engine_gateway_sidecar_mcp_round_trip",result); self.assertIn("restored_request_is_duplicate_safe",result)
        self.assertTrue(result["restore_quarantines_incomplete_work"])
        self.assertTrue(result["engine_profile_excluded_from_restore"])

    def test_engine_owner_state_mount_remains_an_isolation_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder); compose=Path(folder)/"compose.yaml"
            compose.write_text(compose.read_text().replace(
                "      - agentos-engine-profile:/engine-profile\n",
                "      - agentos-engine-profile:/engine-profile\n      - agentos-data:/state\n",
            ))
            report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertIn("subscription-engine-isolation-design-required",report["recovery_actions"])
        self.assertIn("isolated-engine-egress-policy-required",report["recovery_actions"])

    def test_command_reports_named_blocker(self):
        run=subprocess.run(["python3",str(ROOT/"scripts"/"operating_preflight.py"),"--root",str(ROOT)],text=True,capture_output=True)
        self.assertEqual(run.returncode,1); report=json.loads(run.stdout)
        self.assertIn("isolated-engine-egress-policy-required",report["recovery_actions"])
        self.assertNotIn("subscription-engine-isolation-design-required",report["recovery_actions"])
        self.assertEqual(report["execution_path"],"isolated-subscription-engine-pending-egress-policy")
