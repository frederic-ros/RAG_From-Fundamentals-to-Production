# -*- coding: utf-8 -*-
"""
generate_sample_docs.py — the test documents of Chapter 7.

Builds a PAIR of documents around Julien (industrial maintenance):

    julien_hostile_sheet.json — the pivot of a sheet HOSTILE to machines: no
        real hierarchy, a flattened table, no metadata, raw acronyms never
        spelled out, and two "truths" that contradict each other.

    julien_ai_ready_sheet.json — the pivot of the SAME sheet, in its AI-ready
        version: hierarchical sections, the table unfolded into key/value pairs,
        complete metadata, acronyms spelled out, a single truth.

Readable Markdown versions (.md) are also produced for Lab 7-1 (the manual
rework), together with a small corpus of Sophie's for Lab 7-3 (the linter at
scale).

A note on the acronyms. The French edition used PPR, GMAO, VduC, RIFSEEP, CIA
and CET. They have been replaced by their genuine English-language equivalents —
RAMS, CMMS, MRV, NJC, PRP, TOIL — rather than translated literally. The point of
the exercise is an acronym that is opaque to an outsider and obvious to the
department that wrote it, and that only works with acronyms a reader would
actually meet at work.

Everything is deterministic and free of external dependencies (JSON plus text).
Run once before the labs: python generate_sample_docs.py
"""

import json
from pathlib import Path

DOCS = Path(__file__).resolve().parent / "sample_docs"
DOCS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. The HOSTILE version (JSON pivot)
# ---------------------------------------------------------------------------
# The hostile characteristics, faithful to the chapter:
#   - a single catch-all "section", with no hierarchy;
#   - a table flattened into a run of numbers (merged cells originally);
#   - empty metadata;
#   - raw acronyms (RAMS, CMMS, MRV) never spelled out;
#   - two contradictory maximum pressures, so no single truth.
HOSTILE_SHEET = {
    "title": "MX-200",  # a poor title
    "sections": [
        {
            "title": "",  # no section title
            "content": (
                "MX-200 maintenance sheet. See RAMS before work. "
                "CMMS ticket mandatory. Max pressure 12.5 bar. "
                "Param: MX-200 12.5 180 60 400 MX-201 16 240 85 400. "
                "Note max pressure 14 bar peak tolerated per MRV. "
                "Torque see table. Reset CMMS after."
            ),
        }
    ],
    "metadata": {"source_format": "docx"},  # no date, no author, no version
}


# ---------------------------------------------------------------------------
# 2. The AI-READY version (JSON pivot)
# ---------------------------------------------------------------------------
AI_READY_SHEET = {
    "title": "Maintenance sheet — MX-200 compressor",
    "sections": [
        {
            "title": "Preliminary procedure",
            "content": (
                "Before any work, consult the Risk Assessment and Method "
                "Statement (RAMS). Opening a ticket in the Computerised "
                "Maintenance Management System (CMMS) is mandatory."
            ),
        },
        {
            "title": "Technical parameters",
            "content": (
                "Model MX-200: maximum pressure 12.5 bar; flow 180 m3/h; "
                "tightening torque 60 N.m; voltage 400 V. "
                "Model MX-201: maximum pressure 16 bar; flow 240 m3/h; "
                "tightening torque 85 N.m; voltage 400 V."
            ),
        },
        {
            "title": "Closing the intervention",
            "content": (
                "After the work, reset the counter in the CMMS and close the "
                "ticket."
            ),
        },
    ],
    "metadata": {
        "source_format": "docx",
        "author": "Design office — Julien Bauer",
        "date": "2025-03-02",
        "version": "2.1",
        "status": "in_force",
    },
}


# ---------------------------------------------------------------------------
# 3. Sophie's corpus, for the linter at scale (Lab 7-3)
# ---------------------------------------------------------------------------
SOPHIE_CORPUS = [
    {
        "name": "contract_mp014_clean",
        "pivot": {
            "title": "Public contract 2025-MP-014",
            "sections": [
                {"title": "Article 1 - Purpose", "content":
                    "The purpose of this contract is the supply of equipment."},
                {"title": "Article 2 - Duration", "content":
                    "The contract is concluded for a period of twenty-four months."},
            ],
            "metadata": {"date": "2025-02-10", "author": "Procurement department",
                         "version": "1.0", "source_format": "pdf"},
        },
    },
    {
        "name": "hr_note_raw",
        "pivot": {
            "title": "note",
            "sections": [
                {"title": "", "content":
                    "See NJC and PRP. HR approves. TOIL deadline not stated. "
                    "Contact HR. See also NS-2024-12 and NS-2025-03."},
            ],
            "metadata": {"source_format": "pdf"},
        },
    },
    {
        "name": "partial_procedure",
        "pivot": {
            "title": "Reimbursement procedure",
            "sections": [
                {"title": "Purpose", "content":
                    "This procedure describes the reimbursement of expenses."},
                {"title": "Scale", "content":
                    "Expenses 0.5 12 25 ceiling 60 by zone A B C."},  # a flattened table
            ],
            "metadata": {"date": "2023-01-01", "source_format": "docx"},
        },
    },
]


# ---------------------------------------------------------------------------
# Readable Markdown renderings (for Lab 7-1, the manual rework)
# ---------------------------------------------------------------------------
HOSTILE_MD = """MX-200

MX-200 maintenance sheet. See RAMS before work. CMMS ticket mandatory.
Max pressure 12.5 bar. Param: MX-200 12.5 180 60 400 MX-201 16 240 85 400.
Note max pressure 14 bar peak tolerated per MRV. Torque see table.
Reset CMMS after.
"""

AI_READY_MD = """# Maintenance sheet — MX-200 compressor

Metadata: author Design office (Julien Bauer) — date 2025-03-02 —
version 2.1 — status in force.

## Preliminary procedure

Before any work, consult the Risk Assessment and Method Statement (RAMS).
Opening a ticket in the Computerised Maintenance Management System (CMMS) is
mandatory.

## Technical parameters

| Model  | Max pressure (bar) | Flow (m3/h) | Torque (N.m) | Voltage (V) |
|--------|--------------------|-------------|--------------|-------------|
| MX-200 | 12.5               | 180         | 60           | 400         |
| MX-201 | 16                 | 240         | 85           | 400         |

## Closing the intervention

After the work, reset the counter in the CMMS and close the ticket.
"""


def write_json(name: str, data) -> None:
    path = DOCS / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  + {name}")


def main() -> None:
    print("Generating the Chapter 7 test documents:")
    write_json("julien_hostile_sheet.json", HOSTILE_SHEET)
    write_json("julien_ai_ready_sheet.json", AI_READY_SHEET)
    write_json("sophie_corpus.json", SOPHIE_CORPUS)

    (DOCS / "julien_hostile_sheet.md").write_text(HOSTILE_MD, encoding="utf-8")
    print("  + julien_hostile_sheet.md")
    (DOCS / "julien_ai_ready_sheet.md").write_text(AI_READY_MD, encoding="utf-8")
    print("  + julien_ai_ready_sheet.md")

    print(f"\nDone. Documents available in: {DOCS}")


if __name__ == "__main__":
    main()
