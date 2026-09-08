import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location("agentos_doctor", ROOT / "scripts" / "agentos_doctor.py")
DOCTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DOCTOR)


class Runner:
    def __init__(self, values):
        self.calls = []
        self.values = values

    def __call__(self, command, root, env=None):
        command = tuple(command)
        self.calls.append((command, env))
        if command in self.values:
            return SimpleNamespace(returncode=0, stdout=self.values[command], stderr="")
        if (
            command[:2] == ("docker", "compose")
            and command[-2:] == ("config", "--quiet")
        ):
            return SimpleNamespace(returncode=0, stdout=self.values.get("compose_config", ""), stderr="")
        return None


def disk(free=10 * 1024 * 1024 * 1024):
    return SimpleNamespace(free=free)


def ready_preflight(_root):
    return {"state": "ready", "recovery_actions": []}


def test_doctor_reports_ready_without_external_configuration(monkeypatch):
    monkeypatch.setattr(DOCTOR.operating_preflight, "inspect", ready_preflight)
    monkeypatch.setattr(DOCTOR, "_port_available", lambda _: True)
    runner = Runner({
        ("git", "rev-parse", "HEAD"): "a" * 40 + "\n",
        ("git", "status", "--porcelain"): "",
        ("docker", "version", "--format", "{{.Server.Version}}"): "29.0\n",
        ("docker", "compose", "version"): "Docker Compose v2\n",
    })
    report = DOCTOR.inspect(ROOT, "a" * 40, runner=runner, disk_usage=lambda _: disk())
    assert report["state"] == "ready"
    assert not report["safe_next_commands"]
    _, env = next((call for call in runner.calls if call[0] == ("docker", "version", "--format", "{{.Server.Version}}"))
    )
    assert "DOCKER_HOST" not in env
    assert "DOCKER_CONTEXT" not in env
    assert "COMPOSE_PROFILES" not in env
    assert "COMPOSE_FILE" not in env


def test_doctor_reports_diagnostic_failures_without_remediation(monkeypatch):
    monkeypatch.setattr(DOCTOR.operating_preflight, "inspect", lambda _: {"state": "not-ready", "recovery_actions": ["missing-local-health-check"]})
    monkeypatch.setattr(DOCTOR, "_port_available", lambda _: False)
    report = DOCTOR.inspect(ROOT, "a" * 40, runner=Runner({}), disk_usage=lambda _: disk(1))
    assert report["state"] == "blocked"
    assert {
        "candidate-checkout-mismatch",
        "docker-daemon-unavailable",
        "docker-compose-plugin-unavailable",
        "loopback-port-in-use",
        "insufficient-disk-space",
        "missing-local-health-check",
    } <= set(report["blocked"])
    assert all("docker compose up" not in command for command in report["safe_next_commands"])


def test_candidate_is_loaded_from_current_top_completion_claim():
    candidate = DOCTOR._candidate_from_plan(ROOT)
    assert len(candidate) == 40
    assert all(character in "0123456789abcdef" for character in candidate)


def test_doctor_defaults_port_from_agentos_port(monkeypatch):
    monkeypatch.setattr(DOCTOR.operating_preflight, "inspect", ready_preflight)
    monkeypatch.setenv("AGENTOS_PORT", "9911")
    monkeypatch.setattr(DOCTOR, "_port_available", lambda _: True)
    runner = Runner({
        ("git", "rev-parse", "HEAD"): "a" * 40 + "\n",
        ("git", "status", "--porcelain"): "",
        ("docker", "version", "--format", "{{.Server.Version}}"): "29.0\n",
        ("docker", "compose", "version"): "Docker Compose v2\n",
    })
    report = DOCTOR.inspect(ROOT, "a" * 40, runner=runner, disk_usage=lambda _: disk())
    assert report["state"] == "ready"
    assert report["port"] == 9911


def test_doctor_recommends_safe_candidate_checkout_when_mismatched(monkeypatch):
    monkeypatch.setattr(DOCTOR.operating_preflight, "inspect", ready_preflight)
    monkeypatch.setattr(DOCTOR, "_candidate_from_plan", lambda _root: "a" * 40)
    monkeypatch.setattr(DOCTOR, "_port_available", lambda _: True)
    runner = Runner({
        ("git", "rev-parse", "HEAD"): "b" * 40 + "\n",
        ("git", "status", "--porcelain"): "",
        ("docker", "version", "--format", "{{.Server.Version}}"): "29.0\n",
        ("docker", "compose", "version"): "Docker Compose v2\n",
    })
    report = DOCTOR.inspect(ROOT, "a" * 40, runner=runner, disk_usage=lambda _: disk())
    assert report["state"] == "blocked"
    assert report["checks"]["candidate_checkout"] is False
    assert any("git worktree add --detach" in cmd for cmd in report["safe_next_commands"])


def test_candidate_request_rejects_non_plan_immutable_candidate(monkeypatch):
    monkeypatch.setattr(DOCTOR.operating_preflight, "inspect", ready_preflight)
    monkeypatch.setattr(DOCTOR, "_candidate_from_plan", lambda _root: "c" * 40)
    monkeypatch.setattr(DOCTOR, "_port_available", lambda _: True)
    runner = Runner({
        ("git", "rev-parse", "HEAD"): "a" * 40 + "\n",
        ("git", "status", "--porcelain"): "",
        ("docker", "version", "--format", "{{.Server.Version}}"): "29.0\n",
        ("docker", "compose", "version"): "Docker Compose v2\n",
    })
    report = DOCTOR.inspect(ROOT, "a" * 40, runner=runner, disk_usage=lambda _: disk())
    assert report["state"] == "blocked"
    assert "candidate-not-top-supported" in report["blocked"]
    assert report["checks"]["candidate_supported"] is False


def test_supported_candidate_is_accepted_when_matching_plan(monkeypatch):
    monkeypatch.setattr(DOCTOR.operating_preflight, "inspect", ready_preflight)
    monkeypatch.setattr(DOCTOR, "_candidate_from_plan", lambda _root: "a" * 40)
    monkeypatch.setattr(DOCTOR, "_port_available", lambda _: True)
    runner = Runner({
        ("git", "rev-parse", "HEAD"): "a" * 40 + "\n",
        ("git", "status", "--porcelain"): "",
        ("docker", "version", "--format", "{{.Server.Version}}"): "29.0\n",
        ("docker", "compose", "version"): "Docker Compose v2\n",
    })
    report = DOCTOR.inspect(ROOT, "a" * 40, runner=runner, disk_usage=lambda _: disk())
    assert report["state"] == "ready"
    assert report["checks"]["candidate_supported"] is True
