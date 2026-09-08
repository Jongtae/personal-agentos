import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def service_block(compose_text, name):
    matched = re.search(
        rf"(?ms)^  {re.escape(name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_.-]+:\n|^[A-Za-z])",
        compose_text,
    )
    if not matched:
        raise AssertionError(f"missing Compose service: {name}")
    return matched.group("body")


def list_items(service_text, key):
    matched = re.search(
        rf"(?m)^    {re.escape(key)}:\n(?P<items>(?:      - .*\n)+)",
        service_text,
    )
    if not matched:
        raise AssertionError(f"missing Compose service list: {key}")
    return [line.removeprefix("      - ").strip().strip('"')
            for line in matched.group("items").splitlines()]


class ComposeIsolatedEngineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.compose_text = (ROOT / "compose.yaml").read_text(encoding="utf-8")
        cls.agentos = service_block(cls.compose_text, "agentos")
        cls.engine = service_block(cls.compose_text, "engine")
        cls.engine_dockerfile = (ROOT / "Dockerfile.engine").read_text(encoding="utf-8")
        cls.agentos_dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    def test_agentos_uses_the_private_engine_endpoint(self):
        self.assertRegex(
            self.agentos,
            r"(?m)^      AGENTOS_ISOLATED_ENGINE_URL: http://engine:8766/execute$",
        )
        self.assertIn("engine-internal", list_items(self.agentos, "networks"))

    def test_engine_has_no_host_port_or_owner_state_mount(self):
        self.assertNotRegex(self.engine, r"(?m)^    (?:ports|expose):")
        volumes = list_items(self.engine, "volumes")
        self.assertEqual(volumes, ["agentos-engine-profile:/engine-profile"])
        self.assertNotIn("agentos-data", "\n".join(volumes))
        self.assertNotIn("/state", "\n".join(volumes))
        self.assertNotIn("/var/run/docker.sock", self.compose_text)
        self.assertNotRegex(self.compose_text, r"(?:^|:)\s*(?:~|/home/|/Users/)")

    def test_engine_has_only_an_internal_service_network(self):
        self.assertEqual(list_items(self.engine, "networks"), ["engine-internal"])
        self.assertRegex(
            self.compose_text,
            r"(?m)^  engine-internal:\n    internal: true$",
        )
        self.assertNotRegex(self.engine, r"(?m)^    network_mode:")
        self.assertIn("Runtime egress for Codex is intentionally absent", self.compose_text)
        self.assertIn("explicit owner-approved network design", self.compose_text)

    def test_engine_command_launches_only_the_isolated_sidecar(self):
        self.assertEqual(
            list_items(self.engine, "command"),
            [
                "python", "-m", "personal_agent.isolated_engine_sidecar",
                "--host", "0.0.0.0", "--port", "8766", "--callback",
                "http://agentos:8787/internal/isolated-engine/mcp",
            ],
        )
        self.assertRegex(self.engine, r"(?m)^    read_only: true$")
        self.assertEqual(list_items(self.engine, "cap_drop"), ["ALL"])
        self.assertIn("no-new-privileges:true", list_items(self.engine, "security_opt"))

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
            list_items(self.agentos, "volumes"),
            ["agentos-data:/state"],
        )


if __name__ == "__main__":
    unittest.main()
