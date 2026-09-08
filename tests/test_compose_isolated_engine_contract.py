import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ComposeIsolatedEngineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        cls.compose = yaml.safe_load(cls.compose_text)
        cls.engine_dockerfile = (ROOT / "Dockerfile.engine").read_text(encoding="utf-8")
        cls.agentos_dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    def test_agentos_uses_the_private_engine_endpoint(self):
        agentos = self.compose["services"]["agentos"]
        self.assertEqual(
            agentos["environment"]["AGENTOS_ISOLATED_ENGINE_URL"],
            "http://engine:8766/execute",
        )
        self.assertIn("engine-internal", agentos["networks"])

    def test_engine_has_no_host_port_or_owner_state_mount(self):
        engine = self.compose["services"]["engine"]
        self.assertNotIn("ports", engine)
        self.assertNotIn("expose", engine)
        self.assertEqual(engine["volumes"], ["agentos-engine-profile:/engine-profile"])
        self.assertNotIn("agentos-data", "\n".join(engine["volumes"]))
        self.assertNotIn("/state", "\n".join(engine["volumes"]))
        self.assertNotIn("/var/run/docker.sock", self.compose_text)
        self.assertNotRegex(self.compose_text, r"(?:^|:)\s*(?:~|/home/|/Users/)")

    def test_engine_has_only_an_internal_service_network(self):
        engine = self.compose["services"]["engine"]
        self.assertEqual(engine["networks"], ["engine-internal"])
        self.assertIs(self.compose["networks"]["engine-internal"]["internal"], True)
        self.assertNotIn("network_mode", engine)
        self.assertIn("Runtime egress for Codex is intentionally absent", self.compose_text)
        self.assertIn("explicit owner-approved network design", self.compose_text)

    def test_engine_command_launches_only_the_isolated_sidecar(self):
        engine = self.compose["services"]["engine"]
        self.assertEqual(
            engine["command"],
            [
                "python", "-m", "personal_agent.isolated_engine_sidecar",
                "--host", "0.0.0.0", "--port", "8766", "--callback",
                "http://agentos:8787/internal/isolated-engine/mcp",
            ],
        )
        self.assertTrue(engine["read_only"])
        self.assertEqual(engine["cap_drop"], ["ALL"])
        self.assertIn("no-new-privileges:true", engine["security_opt"])

    def test_codex_cli_is_pinned_in_the_dedicated_nonroot_image(self):
        self.assertIn("npm install --global @openai/codex@0.153.4", self.engine_dockerfile)
        self.assertNotIn("CODEX_CLI_VERSION", self.engine_dockerfile)
        self.assertNotRegex(self.engine_dockerfile, r"@openai/codex@(?:latest|next)\b")
        self.assertIn("CODEX_HOME=/engine-profile", self.engine_dockerfile)
        self.assertIn("USER engine", self.engine_dockerfile)

    def test_agentos_image_no_longer_contains_the_engine_profile(self):
        self.assertNotIn("CODEX_HOME", self.agentos_dockerfile)
        self.assertNotIn("/engine-profile", self.agentos_dockerfile)
        self.assertEqual(
            self.compose["services"]["agentos"]["volumes"],
            ["agentos-data:/state"],
        )


if __name__ == "__main__":
    unittest.main()
