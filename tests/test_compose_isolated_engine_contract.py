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
        cls.egress = service_block(cls.compose_text, "egress-proxy")
        cls.engine_dockerfile = (ROOT / "Dockerfile.engine").read_text(encoding="utf-8")
        cls.egress_dockerfile = (ROOT / "Dockerfile.egress").read_text(encoding="utf-8")
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

    def test_engine_has_only_an_internal_service_network_and_uses_proxy(self):
        self.assertEqual(list_items(self.engine, "networks"), ["engine-internal"])
        self.assertRegex(
            self.compose_text,
            r"(?m)^  engine-internal:\n    internal: true$",
        )
        self.assertNotRegex(self.engine, r"(?m)^    network_mode:")
        self.assertRegex(self.engine, r"(?m)^      HTTPS_PROXY: http://egress-proxy:3128$")
        self.assertRegex(self.engine, r"(?m)^      HTTP_PROXY: http://egress-proxy:3128$")
        self.assertRegex(self.engine, r"(?m)^      NO_PROXY: agentos,localhost,127\.0\.0\.1$")

    def test_only_policy_proxy_joins_the_noninternal_provider_network(self):
        self.assertEqual(
            list_items(self.egress, "networks"),
            ["engine-internal", "provider-egress"],
        )
        self.assertNotIn("provider-egress", list_items(self.engine, "networks"))
        self.assertNotIn("provider-egress", list_items(self.agentos, "networks"))
        self.assertRegex(self.compose_text, r"(?m)^  provider-egress:$")
        self.assertNotRegex(self.egress, r"(?m)^    (?:ports|volumes|network_mode):")
        self.assertRegex(self.egress, r"(?m)^    read_only: true$")
        self.assertEqual(list_items(self.egress, "cap_drop"), ["ALL"])

    def test_policy_proxy_is_default_deny_and_has_no_owner_data(self):
        self.assertRegex(
            self.egress,
            r"(?m)^      AGENTOS_PROVIDER_EGRESS_ALLOWLIST: "
            r"\$\{AGENTOS_PROVIDER_EGRESS_ALLOWLIST:-\}$",
        )
        self.assertNotIn("agentos-data", self.egress)
        self.assertNotIn("agentos-engine-profile", self.egress)
        self.assertIn("personal_agent.limited_egress_proxy", self.egress_dockerfile)
        self.assertIn("USER egress", self.egress_dockerfile)

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
