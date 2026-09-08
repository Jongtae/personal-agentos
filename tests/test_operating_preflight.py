import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("operating_preflight", ROOT / "scripts" / "operating_preflight.py")
PREFLIGHT = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(PREFLIGHT)


class OperatingPreflightTests(unittest.TestCase):
    def fixture(self, root, binding="127.0.0.1:${AGENTOS_PORT:-8787}:8787", health=True, nonroot=True, egress=False):
        root=Path(root); (root/"scripts").mkdir(); (root/"pyproject.toml").write_text('[project]\nversion = "1.0.4"\n')
        compose=f'''services:\n  agentos:\n    ports:\n      - "{binding}"\n    volumes:\n      - agentos-data:/state\n    environment:\n      AGENTOS_ISOLATED_ENGINE_URL: http://engine:8766/execute\n'''
        if health: compose+='    healthcheck:\n      test: ["CMD", "/healthz"]\n'
        compose+='''  engine:\n    command: ["python", "-m", "personal_agent.isolated_engine_sidecar", "--callback", "http://agentos:8787/internal/isolated-engine/mcp"]\n    volumes:\n      - agentos-engine-profile:/engine-profile\n'''
        if egress:
            compose+='''    environment:\n      HTTPS_PROXY: http://egress-proxy:3128\n      HTTP_PROXY: http://egress-proxy:3128\n      NO_PROXY: agentos,localhost,127.0.0.1\n'''
        compose+='''    networks:\n      - engine-internal\n    read_only: true\n'''
        if egress:
            compose+='''  egress-proxy:\n    build:\n      context: .\n      dockerfile: Dockerfile.egress\n    environment:\n      AGENTOS_PROVIDER_EGRESS_ALLOWLIST: ${AGENTOS_PROVIDER_EGRESS_ALLOWLIST:-}\n    networks:\n      - engine-internal\n      - provider-egress\n    read_only: true\n'''
        compose+='''networks:\n  engine-internal:\n    internal: true\n'''
        if egress: compose+='''  provider-egress:\n'''
        compose+='''volumes:\n  agentos-data:\n  agentos-engine-profile:\n'''; (root/"compose.yaml").write_text(compose)
        (root/"Dockerfile").write_text("FROM python\n"+("USER agentos\n" if nonroot else ""))
        if egress:
            (root/"Dockerfile.egress").write_text(
                'FROM python\nUSER egress\nCMD ["python", "-m", "personal_agent.limited_egress_proxy"]\n'
            )
            (root/"personal_agent").mkdir()
            (root/"personal_agent"/"limited_egress_proxy.py").write_text(
                "parse_allowlist = None\n# hostname not in self.server.allowed_hosts\n"
            )
        for name in PREFLIGHT.REQUIRED_SCRIPTS:(root/"scripts"/name).write_text("#!/bin/sh\n")

    def test_isolated_structure_still_fails_closed_on_missing_egress_policy(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder); report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertEqual(report["state"],"not-ready")
        self.assertEqual(report["recovery_actions"],["isolated-engine-egress-policy-required"])
        self.assertTrue(report["checks"]["separate_engine_profile_volume"])
        self.assertTrue(report["checks"]["subscription_engine_isolated"])
        self.assertFalse(report["checks"]["isolated_engine_external_egress_policy"])

    def test_policy_proxy_satisfies_architecture_while_empty_allowlist_is_deferred(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder, egress=True)
            with patch.dict("os.environ", {"AGENTOS_PROVIDER_EGRESS_ALLOWLIST": ""}):
                report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertEqual(report["state"], "ready")
        self.assertTrue(report["checks"]["isolated_engine_external_egress_policy"])
        self.assertFalse(report["checks"]["provider_egress_allowlist_configured"])
        self.assertFalse(report["checks"]["provider_egress_reachable"])
        self.assertIn(
            "owner provider egress allowlist operating configuration",
            report["deferred_owner_gates"],
        )
        self.assertNotIn("isolated-engine-egress-policy-required",report["recovery_actions"])

    def test_nonempty_owner_allowlist_removes_only_the_configuration_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder, egress=True)
            with patch.dict("os.environ", {"AGENTOS_PROVIDER_EGRESS_ALLOWLIST": "api.example.test"}):
                report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertTrue(report["checks"]["provider_egress_allowlist_configured"])
        self.assertFalse(report["checks"]["provider_egress_reachable"])
        self.assertNotIn(
            "owner provider egress allowlist operating configuration",
            report["deferred_owner_gates"],
        )

    def test_comma_only_and_invalid_allowlists_never_claim_owner_configuration(self):
        with tempfile.TemporaryDirectory() as folder:
            self.fixture(folder, egress=True)
            with patch.dict("os.environ", {"AGENTOS_PROVIDER_EGRESS_ALLOWLIST": ",,,"}):
                comma_only=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
            with patch.dict("os.environ", {"AGENTOS_PROVIDER_EGRESS_ALLOWLIST": "*.example.test"}):
                invalid=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
        self.assertFalse(comma_only["checks"]["provider_egress_allowlist_configured"])
        self.assertIn("owner provider egress allowlist operating configuration",comma_only["deferred_owner_gates"])
        self.assertFalse(invalid["checks"]["provider_egress_allowlist_configured"])
        self.assertIn("invalid-provider-egress-allowlist",invalid["recovery_actions"])

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

    def test_engine_host_port_or_extra_host_mount_never_reports_ready(self):
        for addition in ('    ports:\n      - "8766:8766"\n', '    volumes:\n      - /Users/example:/host\n'):
            with self.subTest(addition=addition), tempfile.TemporaryDirectory() as folder:
                self.fixture(folder, egress=True); compose=Path(folder)/"compose.yaml"
                compose.write_text(compose.read_text().replace("    read_only: true\n", addition+"    read_only: true\n",1))
                report=PREFLIGHT.inspect(folder,product_probe=lambda:{"runtime_path":True})
            self.assertEqual(report["state"],"not-ready")
            self.assertIn("subscription-engine-isolation-design-required",report["recovery_actions"])

    def test_command_reports_named_blocker(self):
        environment = dict(os.environ)
        environment.pop("AGENTOS_PROVIDER_EGRESS_ALLOWLIST", None)
        run=subprocess.run(["python3",str(ROOT/"scripts"/"operating_preflight.py"),"--root",str(ROOT)],text=True,capture_output=True,env=environment)
        self.assertEqual(run.returncode,0); report=json.loads(run.stdout)
        self.assertNotIn("isolated-engine-egress-policy-required",report["recovery_actions"])
        self.assertNotIn("subscription-engine-isolation-design-required",report["recovery_actions"])
        self.assertEqual(report["execution_path"],"isolated-subscription-engine-policy-proxy-owner-configuration-deferred")
        self.assertFalse(report["checks"]["provider_egress_reachable"])
