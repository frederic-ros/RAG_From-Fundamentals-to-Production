# -*- coding: utf-8 -*-
"""
generate_corpus.py — the corpus and queries of Chapter 18 (hybrid search).

To demonstrate that lexical and dense search complement each other, the corpus
must hold both:

  - exact CODES and REFERENCES (E-204, P-42, s.172, version 535.86) — BM25's
    territory, and the dense search's blind spot;
  - SEMANTIC reformulations ("a motor that runs hot" against "overheating") —
    the dense search's territory, and BM25's blind spot.

A list of LABELLED QUERIES is also supplied: each query knows which document is
the relevant one, by its identifier. That lets the labs MEASURE the rank of the
right document under each method (BM25 alone, dense alone, hybrid).

A NOTE ON THE SEMANTIC QUERIES. Their whole point is to share as few words as
possible with the document they should retrieve. "A motor that runs hot" must
find the sheet on "overheating"; "a drop in efficiency" must find the one on
"consumes too much power". If a translation brings the wording of a query and its
target closer together, BM25 starts to succeed and the chapter's demonstration
collapses. Check the overlap before editing either side.

Two outputs:
    corpus/documents.tsv — id <TAB> text
    corpus/queries.tsv   — query <TAB> relevant_id <TAB> type (exact|semantic)

Deterministic. Run before the labs: python generate_corpus.py
"""

from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent / "corpus"

# Each document is (identifier, text). The identifiers serve as labels.
DOCUMENTS = [
    # --- Documents with exact CODES and REFERENCES (BM25's territory) --------
    ("doc_E204",
     "Troubleshooting sheet. Fault E-204 signals a loss of priming on the pumping "
     "unit. Check the non-return valve and restart the priming sequence. Then "
     "reset the controller."),
    ("doc_E205",
     "Troubleshooting sheet. Fault E-205 indicates an overpressure at the "
     "discharge. Check the relief valve before restarting the installation."),
    ("doc_E311",
     "Troubleshooting sheet. Fault E-311 corresponds to a communication failure "
     "with the drive. Check the fieldbus wiring."),
    ("doc_P42",
     "Equipment sheet for pump P-42. Corrective and preventive maintenance of the "
     "centrifugal pump. Stripping the pump casing and replacing the mechanical "
     "seals."),
    ("doc_law",
     "The board draws up a report under section 172 of the Companies Act, "
     "concerning the governance of the company."),
    ("doc_driver",
     "Installation note. The NVIDIA graphics driver version 535.86 fixes several "
     "incompatibilities. Uninstall the old driver before the update."),
    # --- SEMANTIC documents (the dense search's territory, reformulations) ----
    # Each of these is written so that its wording does NOT overlap the query
    # that should retrieve it. That gap is the whole demonstration.
    ("doc_overheating",
     "Overheating in an electric motor: diagnosis and remedies. Common causes of "
     "excessive heating: obstructed ventilation, mechanical overload, worn "
     "bearings. Cooling procedure and thermal checks."),
    ("doc_consumption",
     "Why a rotating machine draws too much power. A falling output often betrays "
     "a misalignment or a build-up of dirt. Measure the current drawn and compare "
     "it with the rated values."),
    ("doc_motivation",
     "Leading a team that has lost its momentum. Restoring a sense of purpose, "
     "acknowledging effort, setting reachable targets: levers for re-engaging "
     "demotivated staff."),
    ("doc_remote_work",
     "Working away from the office is built on trust and on the right tools. "
     "Working from home assumes clear windows of availability and a respected "
     "right to disconnect."),
    # --- Distractors: close on the theme, but not the right answer ------------
    ("doc_general_codes",
     "General list of the controller fault codes. The E series covers priming, "
     "pressure and communication failures. Refer to the troubleshooting sheet "
     "matching each code."),
    ("doc_maintenance",
     "Maintenance plan for the pumps and motors. Inspection intervals, electrical "
     "lockout, wearing of personal protective equipment."),
]

# Labelled queries: (query, relevant_id, type).
# type = "exact"    -> a code or reference query, which should favour BM25
# type = "semantic" -> a query of intent, which should favour the dense search
QUERIES = [
    ("E-204", "doc_E204", "exact"),
    ("fault E-311 drive failure", "doc_E311", "exact"),
    ("section 172 Companies Act", "doc_law", "exact"),
    ("NVIDIA driver version 535.86", "doc_driver", "exact"),
    ("how to fix a motor that runs hot", "doc_overheating", "semantic"),
    ("drop in the energy efficiency of a machine", "doc_consumption", "semantic"),
    ("how to re-engage demotivated staff", "doc_motivation", "semantic"),
    # The star failure of BM25: "telecommuting" appears NOWHERE in the document,
    # which speaks of "working away from the office" and "working from home".
    # Zero lexical overlap, so only the dense search can bridge the gap. This
    # mirrors the French pair "teletravail" against "travail a distance".
    ("company telecommuting policy", "doc_remote_work", "semantic"),
]


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)

    doc_lines = ["# id\ttext"]
    for ident, text in DOCUMENTS:
        doc_lines.append(f"{ident}\t{text}")
    (BASE / "documents.tsv").write_text("\n".join(doc_lines) + "\n", encoding="utf-8")

    query_lines = ["# query\trelevant_id\ttype"]
    for query, ident, type_ in QUERIES:
        query_lines.append(f"{query}\t{ident}\t{type_}")
    (BASE / "queries.tsv").write_text("\n".join(query_lines) + "\n", encoding="utf-8")

    print("Chapter 18 corpus generated in:", BASE)
    print(f"  - {len(DOCUMENTS)} documents -> corpus/documents.tsv")
    print(f"  - {len(QUERIES)} labelled queries -> corpus/queries.tsv")
    print("\nThe key point: the 'exact' queries (E-204, section 172...) are the dense")
    print("search's blind spot; the 'semantic' ones are BM25's.")


if __name__ == "__main__":
    main()
