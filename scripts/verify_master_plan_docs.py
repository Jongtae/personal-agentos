#!/usr/bin/env python3
"""Verify the bilingual Master Plan documents remain structurally equivalent."""
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PAIRS = (
    ("personal-ai-assistant-vision.ko.md", "personal-ai-assistant-vision.en.md"),
    ("master-plan-01-personal-assistant-core.ko.md", "master-plan-01-personal-assistant-core.en.md"),
    ("master-plan-02-proposal.ko.md", "master-plan-02-proposal.en.md"),
)
PHASE_IDS = ("D-01", "I-01", "D-02", "I-02", "D-03", "I-03", "D-04", "I-04", "D-05", "I-05", "D-06", "I-06")


def links(text):
    return re.findall(r"\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)", text)


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
    for phase in PHASE_IDS:
        if mp1_ko.count(phase) != mp1_en.count(phase) or not mp1_ko.count(phase):
            raise SystemExit(f"MP1 phase parity failure: {phase}")
    print("Master Plan bilingual documents verified")


if __name__ == "__main__":
    main()
