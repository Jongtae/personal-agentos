import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_master_plan_docs", ROOT / "scripts" / "verify_master_plan_docs.py"
)
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


def plan():
    return json.loads((ROOT / "delivery-plan.yaml").read_text(encoding="utf-8"))


def test_every_master_plan_design_has_a_named_implementation_contract_and_evidence():
    VERIFIER.verify_traceability(plan())


def test_design_only_work_cannot_be_promoted_to_development_complete():
    incomplete = copy.deepcopy(plan())
    incomplete["history"]["documented_completed_iterations"].remove("I-MP2-03")
    incomplete["completion_claims"]["MP2"]["status"] = "development_complete"
    with pytest.raises(SystemExit, match="completion claim lacks implemented automated evidence: MP2"):
        VERIFIER.verify_traceability(incomplete)
