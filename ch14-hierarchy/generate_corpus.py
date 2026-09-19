# -*- coding: utf-8 -*-
"""
generate_corpus.py — test corpus for Chapter 14.

This chapter tackles a paradox: a fragment can be PERFECTLY EXACT and still
produce a WRONG answer, as soon as it has been cut off from what qualified it.
The corpus is therefore built around that trap.

  corpus/remote_work_agreement.json
      Claire's HR document, structured as a TREE (document > section >
      subsection > paragraphs). The sensitive point: the general rule
      ("two days") and the exception ("three days for employees who are
      carers") live in two different subsections. The "three days" fragment
      is exact — but silent about the fact that it is an exception.

  corpus/procurement_thresholds.json
      A regulatory extract (Sophie), the same trap transposed to law: a general
      threshold, and a derogation that raises it for certain municipalities.
      Used by Lab 14-5, where the hierarchy is removed.

Each JSON carries, on every node, an identifier and the parent-to-child link,
so that the labs can "climb" from a leaf towards its parent.

Deterministic. No API key. Run before the labs: python generate_corpus.py
"""

from pathlib import Path
import json

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Document 1 — Remote work agreement (Claire). The tree that holds the trap.
# ---------------------------------------------------------------------------
REMOTE_WORK_AGREEMENT = {
    "id": "doc-hr",
    "title": "HR agreement",
    "type": "document",
    "children": [
        {
            "id": "sec-remote-work",
            "title": "Remote work",
            "type": "section",
            "children": [
                {
                    "id": "sub-rule",
                    "title": "General rule",
                    "type": "subsection",
                    "paragraphs": [
                        "Remote work is authorised up to a limit of two days "
                        "per week.",
                    ],
                },
                {
                    "id": "sub-exception",
                    "title": "Exceptional provisions",
                    "type": "subsection",
                    "paragraphs": [
                        "By way of exception, three days per week are granted "
                        "to employees who are carers.",
                    ],
                },
            ],
        }
    ],
}


# ---------------------------------------------------------------------------
# Document 2 — Procurement thresholds (Sophie). The same trap, in law.
# ---------------------------------------------------------------------------
PROCUREMENT_THRESHOLDS = {
    "id": "doc-reg",
    "title": "Procurement regulations",
    "type": "document",
    "children": [
        {
            "id": "sec-thresholds",
            "title": "Procedure thresholds",
            "type": "section",
            "children": [
                {
                    "id": "sub-rule-threshold",
                    "title": "General rule",
                    "type": "subsection",
                    "paragraphs": [
                        "The formal procedure applies above a threshold of "
                        "forty thousand euros.",
                    ],
                },
                {
                    "id": "sub-derogation",
                    "title": "Derogations",
                    "type": "subsection",
                    "paragraphs": [
                        "By way of derogation, the threshold is raised to "
                        "eighty thousand euros for municipalities of fewer "
                        "than one thousand inhabitants.",
                    ],
                },
            ],
        }
    ],
}


def main() -> None:
    print("Generating the Chapter 14 test corpus:")
    for name, doc in [
        ("remote_work_agreement.json", REMOTE_WORK_AGREEMENT),
        ("procurement_thresholds.json", PROCUREMENT_THRESHOLDS),
    ]:
        (CORPUS / name).write_text(
            json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  + {name}")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
