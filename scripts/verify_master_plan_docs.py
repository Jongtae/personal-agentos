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
    ("mp1-d04-a2a-delegation-contract.ko.md", "mp1-d04-a2a-delegation-contract.en.md"),
    ("mp1-d05-calendar-contract.ko.md", "mp1-d05-calendar-contract.en.md"),
    ("mp1-d06-react-release-contract.ko.md", "mp1-d06-react-release-contract.en.md"),
    ("mp1-remediation.ko.md", "mp1-remediation.en.md"),
    ("subscription-telegram-stabilization-contract.ko.md", "subscription-telegram-stabilization-contract.en.md"),
    ("operating-deployment-preparation-contract.ko.md", "operating-deployment-preparation-contract.en.md"),
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
        if not isinstance(required, list) or not required or any(ident not in iterations or ident not in completed for ident in required):
            raise SystemExit(f"completion claim lacks implemented automated evidence: {claim_id}")


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
    print("Master Plan bilingual documents verified")


if __name__ == "__main__":
    main()
