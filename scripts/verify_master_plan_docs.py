#!/usr/bin/env python3
"""Verify the bilingual Master Plan documents remain structurally equivalent."""
from pathlib import Path
import re
import json


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAIRS = (
    ("personal-ai-assistant-vision.ko.md", "personal-ai-assistant-vision.en.md"),
    ("master-plan-01-personal-assistant-core.ko.md", "master-plan-01-personal-assistant-core.en.md"),
    ("master-plan-02-proposal.ko.md", "master-plan-02-proposal.en.md"),
    ("mp1-d01-personal-space-contract.ko.md", "mp1-d01-personal-space-contract.en.md"),
    ("development-governance.ko.md", "development-governance.en.md"),
    ("goal-execution-contract.ko.md", "goal-execution-contract.en.md"),
    ("top-level-specification-completion.ko.md", "top-level-specification-completion.en.md"),
    ("mp1-d04-a2a-delegation-contract.ko.md", "mp1-d04-a2a-delegation-contract.en.md"),
    ("mp1-d05-calendar-contract.ko.md", "mp1-d05-calendar-contract.en.md"),
    ("mp1-d06-react-release-contract.ko.md", "mp1-d06-react-release-contract.en.md"),
    ("mp1-remediation.ko.md", "mp1-remediation.en.md"),
    ("subscription-telegram-stabilization-contract.ko.md", "subscription-telegram-stabilization-contract.en.md"),
    ("operating-deployment-preparation-contract.ko.md", "operating-deployment-preparation-contract.en.md"),
    ("op-02-operating-readiness-remediation-contract.ko.md", "op-02-operating-readiness-remediation-contract.en.md"),
    ("scn-d01-first-live-use-scenarios-contract.ko.md", "scn-d01-first-live-use-scenarios-contract.en.md"),
    ("drive-telegram-web-oauth-contract.ko.md", "drive-telegram-web-oauth-contract.en.md"),
    ("file-workspace-first-experience-contract.ko.md", "file-workspace-first-experience-contract.en.md"),
)
PHASE_IDS = ("D-01", "I-01", "D-02", "I-02", "D-03", "I-03", "D-04", "I-04", "D-05", "I-05", "D-06", "I-06")


def links(text):
    return re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", text)


def phase_table_ids(text):
    rows = re.findall(r"^\| [1-6]\. .*\|.*\|.*\|$", text, flags=re.MULTILINE)
    return tuple(re.findall(r"\b[DI]-\d{2}\b", "\n".join(rows)))


def verify_traceability(plan):
    iterations={item["id"]:item for item in plan["iterations"]}
    for ident, item in iterations.items():
        if item.get("kind") != "design":
            continue
        implementation=item.get("implementation_id")
        contract=item.get("contract")
        if not isinstance(implementation,str) or implementation not in iterations or not isinstance(contract,str) or not (DOCS / contract).is_file():
            raise SystemExit(f"design traceability failure: {ident}")
        delivery=iterations[implementation]
        if delivery.get("kind") not in {"implementation", "release"} or delivery.get("design_id") != ident or delivery.get("contract") != contract or not delivery.get("automated_evidence"):
            raise SystemExit(f"implementation traceability failure: {implementation}")
    claims=plan.get("completion_claims", {})
    completed=set(plan.get("history", {}).get("documented_completed_iterations", []))
    for claim_id, claim in claims.items():
        if not isinstance(claim, dict) or claim.get("status") != "development_complete":
            continue
        required=claim.get("required_implementation_ids", [])
        if claim_id != "TOP" and (not isinstance(required, list) or not required or any(ident not in iterations or ident not in completed for ident in required)):
            raise SystemExit(f"completion claim lacks implemented automated evidence: {claim_id}")
        if claim_id != "TOP":
            continue
        required_top = ("TOP-00", "TOP-01", "TOP-02", "TOP-03")
        if (tuple(required) != required_top or any(ident not in iterations for ident in required_top) or
                any(ident not in completed for ident in required_top)):
            raise SystemExit("TOP completion claim lacks every ordered substep")
        requirements = claim.get("requirements")
        if not isinstance(requirements, dict):
            raise SystemExit("TOP completion claim lacks requirement evidence")
        implementation_ids = set(claim.get("implementation_requirement_ids", []))
        owner_ids = set(claim.get("owner_operating_requirement_ids", []))
        decision_ids = set(claim.get("separate_owner_product_decision_ids", []))
        required_implementation_ids = {"CORE-01", "CORE-02", "MP2-01", "STAB-01", "DEPLOY-01", "GOV-01", "STATUS-01"}
        required_owner_ids = {"OWNER-01"}
        required_decision_ids = {"LEGACY-01"}
        if (implementation_ids != required_implementation_ids or owner_ids != required_owner_ids or
                decision_ids != required_decision_ids):
            raise SystemExit("TOP completion claim misclassifies a requirement")
        if (not implementation_ids or not owner_ids or not decision_ids or implementation_ids & owner_ids or
                implementation_ids & decision_ids or owner_ids & decision_ids):
            raise SystemExit("TOP completion claim has invalid requirement ownership")
        if set(requirements) != implementation_ids | owner_ids | decision_ids:
            raise SystemExit("TOP completion claim omits a requirement")
        for ident in implementation_ids:
            evidence = requirements.get(ident)
            references = evidence.get("evidence") if isinstance(evidence, dict) else None
            if (not isinstance(evidence, dict) or evidence.get("status") != "merged-current-evidence" or
                    not isinstance(references, list) or not references or
                    any(not isinstance(reference, str) or not reference.strip() for reference in references)):
                raise SystemExit(f"TOP implementation requirement is not evidenced: {ident}")
        for ident in owner_ids:
            action = requirements.get(ident)
            if not isinstance(action, dict) or action.get("status") != "owner-operating-action" or not isinstance(action.get("action"), str) or not action["action"]:
                raise SystemExit(f"TOP owner requirement is misclassified: {ident}")
        for ident in decision_ids:
            decision = requirements.get(ident)
            if not isinstance(decision, dict) or decision.get("status") != "separate-owner-product-decision" or not isinstance(decision.get("decision"), str) or not decision["decision"]:
                raise SystemExit(f"TOP product decision is not recorded: {ident}")
        candidate = claim.get("deployment_candidate")
        if not isinstance(candidate, dict) or not isinstance(candidate.get("commit"), str) or not re.fullmatch(r"[0-9a-f]{40}", candidate["commit"]):
            raise SystemExit("TOP completion claim lacks an immutable deployment candidate")
        checks = candidate.get("required_ci")
        if (not isinstance(checks, list) or not checks or
                any(not isinstance(check, dict) or not isinstance(check.get("name"), str) or not check["name"].strip() or
                    check.get("conclusion") != "success" or check.get("commit") != candidate["commit"] for check in checks) or
                claim.get("unresolved_review_findings") != []):
            raise SystemExit("TOP completion claim lacks current verification evidence")


def main():
    for korean, english in PAIRS:
        ko = (DOCS / korean).read_text(encoding="utf-8")
        en = (DOCS / english).read_text(encoding="utf-8")
        if ko.count("## ") != en.count("## "):
            raise SystemExit(f"heading mismatch: {korean} / {english}")
        for text, source in ((ko, korean), (en, english)):
            for link in links(text):
                if not (DOCS / link).is_file():
                    raise SystemExit(f"missing local link in {source}: {link}")
    mp1_ko = (DOCS / PAIRS[1][0]).read_text(encoding="utf-8")
    mp1_en = (DOCS / PAIRS[1][1]).read_text(encoding="utf-8")
    for source, text in ((PAIRS[1][0], mp1_ko), (PAIRS[1][1], mp1_en)):
        if phase_table_ids(text) != PHASE_IDS:
            raise SystemExit(f"MP1 phase table sequence failure: {source}")
    if phase_table_ids(mp1_ko) != phase_table_ids(mp1_en):
        raise SystemExit("MP1 phase parity failure")
    plan=json.loads((ROOT / "delivery-plan.yaml").read_text(encoding="utf-8"))
    verify_traceability(plan)
    workspace_contracts = ((DOCS / "file-workspace-first-experience-contract.ko.md").read_text(encoding="utf-8"),
                           (DOCS / "file-workspace-first-experience-contract.en.md").read_text(encoding="utf-8"))
    for contract in workspace_contracts:
        if ("FILE-WS-A-01" not in contract or "FILE-WS-B-01" not in contract or
                "FILE-WS-C-01" not in contract or "FILE-UX-" in contract):
            raise SystemExit("file-workspace contract substep identifiers do not match the delivery plan")
    print("Master Plan bilingual documents verified")


if __name__ == "__main__":
    main()
