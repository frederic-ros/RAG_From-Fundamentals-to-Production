# -*- coding: utf-8 -*-
"""
Lab 7-1 — The manual rework of a hostile document: Julien's case

Learning objective
------------------
Get a feel for the gap between a layout that pleases the human eye and a
semantic structure a machine can use. The heart of this lab is MANUAL: you
rewrite a hostile sheet according to the AI-ready standard, in Word,
LibreOffice or Markdown. This script does not do the rework for you; it serves
as a guide and as a check. It:

  - shows the hostile sheet and the AI-ready reference sheet;
  - lists, principle by principle, what changed (the rework checklist);
  - checks automatically that your rework meets the standard, using the linter
    of Lab 7-3.

No external dependency, no API key.
Run generate_sample_docs.py first.
"""

import json
from pathlib import Path
from typing import Dict

DOCS = Path(__file__).resolve().parent / "sample_docs"

# Reuse the linter of Lab 7-3, if it sits alongside.
try:
    import importlib.util

    _lab73 = Path(__file__).resolve().parent / "lab7-3_ai_ready_linter.py"
    _spec = importlib.util.spec_from_file_location("lab73", _lab73)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    score_document = _mod.score_document
    verdict = _mod.verdict
except Exception:  # pragma: no cover
    score_document = verdict = None


CHECKLIST = [
    ("Hierarchical headings",
     "The single \"MX-200\" block becomes three titled sections: Preliminary "
     "procedure, Technical parameters, Closing the intervention."),
    ("Normalised tables",
     "The run \"MX-200 12.5 180 60 400 MX-201 16 ...\" is unfolded into a "
     "readable table, one row per model and one column per parameter."),
    ("Metadata present",
     "Author, date and version are added: Julien Bauer, 2025-03-02, v2.1."),
    ("One document, one truth",
     "The \"14 bar peak tolerated\" pressure, which contradicted the 12.5 bar, "
     "is removed: one reference value per model."),
    ("Acronyms spelled out",
     "RAMS becomes \"Risk Assessment and Method Statement (RAMS)\", CMMS becomes "
     "\"Computerised Maintenance Management System (CMMS)\"."),
]


def show_document(heading: str, pivot: Dict) -> None:
    print(f"\n{heading}")
    print("-" * 78)
    print(f"Title: {pivot.get('title', '')}")
    meta = pivot.get("metadata", {})
    shown = ", ".join(f"{k}={v}" for k, v in meta.items() if k != "source_format")
    print(f"Metadata: {shown or '(none)'}")
    for s in pivot.get("sections", []):
        t = s.get("title", "") or "(section with no title)"
        print(f"  - {t}")
        print(f"    {s.get('content', '')[:120]}")


def main() -> None:
    print("=" * 78)
    print("Lab 7-1 — The manual rework of a hostile document (Julien)")
    print("=" * 78)

    if not (DOCS / "julien_hostile_sheet.json").exists():
        print("\nDocuments not found. Run this first: python generate_sample_docs.py")
        return

    hostile = json.loads((DOCS / "julien_hostile_sheet.json").read_text(encoding="utf-8"))
    ai_ready = json.loads((DOCS / "julien_ai_ready_sheet.json").read_text(encoding="utf-8"))

    show_document("BEFORE — the hostile sheet, as extracted", hostile)
    show_document("AFTER — the AI-ready sheet, the target of your rework", ai_ready)

    print("\n" + "=" * 78)
    print("THE REWORK CHECKLIST (the five principles)")
    print("=" * 78)
    for i, (principle, action) in enumerate(CHECKLIST, start=1):
        print(f"{i}. {principle}")
        print(f"   -> {action}")

    # The automatic check, through the linter.
    if score_document is not None:
        print("\n" + "=" * 78)
        print("THE AUTOMATIC CHECK (the Lab 7-3 linter)")
        print("=" * 78)
        s_hostile, _ = score_document(hostile)
        s_ready, _ = score_document(ai_ready)
        print(f"Hostile sheet  : {s_hostile}/5 — {verdict(s_hostile)}")
        print(f"AI-ready sheet : {s_ready}/5 — {verdict(s_ready)}")
        print("\nYour turn: rewrite the hostile sheet by hand, in Word, LibreOffice or")
        print("Markdown, export its JSON pivot, then run it through the Lab 7-3 linter.")
        print("The goal is 5/5. The file julien_ai_ready_sheet.md is the model.")

    print("\n" + "=" * 78)
    print("WHAT TO REMEMBER")
    print("=" * 78)
    print("- A handsome layout is not a good structure: the eye and the machine do not")
    print("  read the same thing.")
    print("- The AI-ready rework is mostly editorial common sense, principle by principle.")
    print("- The same content, well structured, becomes usable without changing the model.")


if __name__ == "__main__":
    main()
