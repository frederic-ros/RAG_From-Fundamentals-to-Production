# -*- coding: utf-8 -*-
"""
generate_corpus.py — test corpus for Chapter 15 (metadata).

The chapter unfolds an underestimated idea: a piece of metadata does not improve
the search, it improves the DECISION. To show that, the corpus needs several
documents that are equally relevant to the same question, of which only one is
valid — and where a piece of metadata, not the text, decides.

  corpus/documents.json
      A list of documents, each with its text AND its metadata (date, version,
      status, source, criticality, profile). The running example brings
      together Sophie (regulatory) and Julien (technical).

The documents are built to expose the traps of the chapter:
  - two editions of the same rate, 2021 repealed and 2024 in force  -> Lab 15-1;
  - several versions and sources of the same procedure              -> Lab 15-2;
  - a VERBOSE obsolete document that outscores the concise official -> Lab 15-3;
  - heterogeneous levels of trust: official, draft, blog            -> Lab 15-4;
  - a still-valid fact hidden behind a date filter                  -> Lab 15-5;
  - documents typed for Sophie and for Julien                       -> Lab 15-6.

Note on the wording: the repealed documents are deliberately WORDY, repeating
the key terms of the question. That is what makes them outscore the current
ones on similarity — which is precisely the thesis of the chapter. Do not
shorten them.

Deterministic. No API key. Run before the labs: python generate_corpus.py
"""

from pathlib import Path
import json

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


DOCUMENTS = [
    # --- The regulatory rate, two editions (Sophie) -------------------------
    {
        "id": "rate-2021",
        "text": (
            "Financial regulations, 2021 edition. What is the applicable rate? "
            "The applicable rate for the charge is a rate of five per cent of "
            "the amount before tax. This applicable rate is understood to cover "
            "every file: the applicable rate depends on no threshold, and the "
            "applicable rate remains valid until the present regulations are "
            "revised."
        ),
        "metadata": {
            "date": "2021-03-15", "version": "2021", "status": "repealed",
            "source": "regulatory", "criticality": "high", "profile": "sophie",
        },
    },
    {
        "id": "rate-2024",
        "text": (
            "Financial regulations 2024. The applicable rate is eight per "
            "cent. This edition repeals and replaces the 2021 edition."
        ),
        "metadata": {
            "date": "2024-01-20", "version": "2024", "status": "in force",
            "source": "regulatory", "criticality": "high", "profile": "sophie",
        },
    },

    # --- Remote work procedure, several versions and sources (Lab 15-2) -----
    {
        "id": "remote-work-v1",
        "text": (
            "Remote work procedure, version 1. Remote work is authorised up "
            "to one day per week, with the manager's agreement."
        ),
        "metadata": {
            "date": "2021-06-01", "version": "v1", "status": "repealed",
            "source": "official", "criticality": "normal", "profile": "sophie",
        },
    },
    {
        "id": "remote-work-v2",
        "text": (
            "Remote work procedure, version 2. Remote work is authorised up "
            "to two days per week, with the manager's agreement."
        ),
        "metadata": {
            "date": "2022-09-01", "version": "v2", "status": "repealed",
            "source": "official", "criticality": "normal", "profile": "sophie",
        },
    },
    {
        "id": "remote-work-v3",
        "text": (
            "Remote work procedure, version 3, in force. Remote work is "
            "authorised up to two days per week, and up to three days for "
            "employees who are carers."
        ),
        "metadata": {
            "date": "2023-11-01", "version": "v3", "status": "in force",
            "source": "official", "criticality": "normal", "profile": "sophie",
        },
    },
    {
        "id": "remote-work-draft",
        "text": (
            "Draft revision of the remote work procedure. Proposal to extend "
            "remote work to four days per week. To be discussed."
        ),
        "metadata": {
            "date": "2023-12-10", "version": "draft", "status": "draft",
            "source": "internal", "criticality": "normal", "profile": "sophie",
        },
    },
    {
        "id": "remote-work-blog",
        "text": (
            "Internal blog post: everything you need to know about remote "
            "work here. In practice, many teams do two to three days."
        ),
        "metadata": {
            "date": "2023-10-05", "version": "—", "status": "published",
            "source": "blog", "criticality": "normal", "profile": "sophie",
        },
    },

    # --- Safety: the wordy obsolete against the concise official (Lab 15-3) -
    {
        "id": "safety-2021-wordy",
        "text": (
            "Safety instructions, 2021 edition. The safety rules applicable on "
            "site comprise the wearing of a safety helmet, the wearing of "
            "safety footwear, the wearing of safety gloves, respect for the "
            "traffic zones, verification of the equipment before use, "
            "inspection of the fire extinguishers, signage of the risk zones, "
            "and strict respect for the posted safety instructions. These "
            "safety rules apply to every person on site."
        ),
        "metadata": {
            "date": "2021-02-01", "version": "2021", "status": "obsolete",
            "source": "official", "criticality": "high", "profile": "julien",
        },
    },
    {
        "id": "safety-2024-concise",
        "text": (
            "Safety instructions 2024, in force. Personal protective equipment "
            "is mandatory; work is carried out with the power off; every "
            "operation is logged."
        ),
        "metadata": {
            "date": "2024-03-01", "version": "2024", "status": "in force",
            "source": "official", "criticality": "high", "profile": "julien",
        },
    },

    # --- The lasting fact hidden behind a date filter (Lab 15-5) ------------
    {
        "id": "standard-2023-permanent",
        "text": (
            "Specification of the flange tightening torque: 40 newton-metres. "
            "This value is a mechanical constant of the equipment, valid for "
            "as long as the machine is in service."
        ),
        "metadata": {
            "date": "2023-12-15", "version": "2023", "status": "in force",
            "source": "supplier", "criticality": "high", "profile": "julien",
            "permanence": "permanent",
        },
    },

    # --- Julien's technical manuals (Lab 15-6) ------------------------------
    {
        "id": "pump-manual-2024",
        "text": (
            "Manufacturer's manual for the P-200 pump, 2024 revision. "
            "Maintenance procedure: oil change every six months, seal "
            "inspection, filter replacement."
        ),
        "metadata": {
            "date": "2024-02-01", "version": "2024", "status": "in force",
            "source": "supplier", "criticality": "high", "profile": "julien",
            "type": "technical manual",
        },
    },
    {
        "id": "pump-manual-2019-historical",
        "text": (
            "Manufacturer's manual for the P-200 pump, 2019 revision. "
            "Historical maintenance procedure, kept for older machines still "
            "in service: oil change every three months."
        ),
        "metadata": {
            "date": "2019-05-01", "version": "2019", "status": "historical",
            "source": "supplier", "criticality": "normal", "profile": "julien",
            "type": "technical manual",
        },
    },
]


def main() -> None:
    payload = {"documents": DOCUMENTS}
    (CORPUS / "documents.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("Generating the Chapter 15 test corpus:")
    print(f"  + documents.json  ({len(DOCUMENTS)} documents with metadata)")
    # A short summary of the statuses present.
    statuses = {}
    for d in DOCUMENTS:
        s = d["metadata"]["status"]
        statuses[s] = statuses.get(s, 0) + 1
    inventory = ", ".join(f"{k}: {v}" for k, v in sorted(statuses.items()))
    print(f"  statuses: {inventory}")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
