import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def _assert_all(text: str, *markers: str) -> None:
    normalized = _normalize(text)
    missing = [marker for marker in markers if _normalize(marker) not in normalized]
    assert not missing, f"missing governance contract markers: {missing}"


def _assert_any(text: str, *alternatives: str) -> None:
    normalized = _normalize(text)
    assert any(_normalize(marker) in normalized for marker in alternatives), (
        f"missing every governance contract alternative: {alternatives}"
    )


def test_agents_declares_permanent_autonomous_delivery_guards() -> None:
    agents = _read("AGENTS.md")

    _assert_all(
        agents,
        "## Autonomous goal execution",
        "requested model",
        "observed execution result",
        "requirement-to-evidence audit",
        "enumerated, dependency-satisfied substep",
        "top-level goal",
        "declared authority",
        "non-goals",
    )
    _assert_any(agents, "must not select an unlisted", "may advance only")
    _assert_any(agents, "accepted setting", "tool-accepted setting")


def test_bilingual_goal_contracts_define_equivalent_delegation_guards() -> None:
    english = _read("docs/goal-execution-contract.en.md")
    korean = _read("docs/goal-execution-contract.ko.md")

    _assert_all(
        english,
        "## Delegation and independent review",
        "requested, accepted, and observed",
        "already enumerated, dependency-satisfied substep",
        "top-level goal",
        "requirement-to-evidence audit",
    )
    _assert_all(
        korean,
        "## 위임 및 독립 검토",
        "요청·수락·관찰",
        "이미 열거되고 dependency가 충족된 substep",
        "최상위 Goal",
        "요구사항-증거 audit",
    )

    # Stable lifecycle concepts must remain present in both translations even if
    # surrounding prose is edited independently.
    for document in (english, korean):
        _assert_all(
            document,
            "goal-ready",
            "allowed authority",
            "non-goals",
            "evidence",
            "completion",
            "blocked",
            "automation",
        )


def test_iteration_issue_template_collects_the_execution_contract() -> None:
    template = _read(".github/ISSUE_TEMPLATE/iteration.md")

    _assert_all(
        template,
        "## Goal-ready activation",
        "## Allowed authority",
        "## Evidence and completion audit",
        "## Delegation and independent review",
        "## Blocked / restart rule",
        "## Top-level goal / substep",
        "## Non-goals",
        "codex/",
    )


def test_ci_runs_the_governance_contract_test_as_part_of_full_pytest() -> None:
    workflow = _read(".github/workflows/validate.yml")

    # Running the whole tests directory keeps this guard in the required CI job
    # without maintaining a second, drift-prone governance-only command.
    _assert_all(workflow, "python3 -m pytest -q tests")
