# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 23 (retrieval becomes a tool).

A deterministic corpus, cut for the LOOP: single-pass questions, where one turn
is enough, and multi-facet questions, where the loop triggers successive searches
by itself. A question with NO answer in the corpus is added too, to illustrate
the loop that would run forever — hence the budget and the stopping condition.

The running thread: Julien (maintenance) — pumps P-12 / P-42 / P-88, motor M-18.

A NOTE ON THE FACETS. The "facets" of a question are equipment CODES (P-12,
P-42), not words. The rule brain checks coverage with a plain substring test on
the context, so the mechanism survives translation unchanged — which is why this
chapter is safer than most. Keep the facets as codes if you edit the queries.

Written to `corpus/fragments.json`:
    { "fragments": [ {"id","text","subject"} ... ],
      "queries":   [ {"question","relevant","facets","type"} ... ] }

Run before the labs: python generate_corpus.py
No API key, no network.
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


FRAGMENTS = [
    {"id": 0, "subject": "stop-P12",
     "text": "Emergency stop procedure for pump P-12: cut the supply at the main "
             "isolator, close the suction valve, then purge the circuit. Complete "
             "immobilisation in thirty seconds."},
    {"id": 1, "subject": "stop-P42",
     "text": "Emergency stop procedure for pump P-42: hit the mushroom button, "
             "isolate the discharge circuit and lock off the equipment. A "
             "hydraulic brake stops the shaft in five seconds."},
    {"id": 2, "subject": "stop-P88",
     "text": "Emergency stop procedure for pump P-88: trigger the automatic stop "
             "through the overpressure sensor, then close the upstream and "
             "downstream valves by hand. Immobilisation in ten seconds."},
    {"id": 3, "subject": "overheating-M18",
     "text": "Overheating of motor M-18: check the ventilation flow, the condition "
             "of the bearings and the mechanical load; clean the fins of the heat "
             "sink."},
    {"id": 4, "subject": "decoy-general-stop",
     "text": "The general emergency stop procedure for the workshop cuts the main "
             "supply and must be known to every operator."},
    {"id": 5, "subject": "decoy-maintenance",
     "text": "A general comparison of pump maintenance: lubrication intervals and "
             "costs, with no detail per individual item of equipment."},
    {"id": 6, "subject": "decoy-valves",
     "text": "The isolation valves are checked annually, to guarantee their "
             "sealing and their operability."},
    {"id": 7, "subject": "decoy-safety",
     "text": "General workshop safety: wearing protective equipment and "
             "respecting the access instructions before any intervention."},
    {"id": 8, "subject": "decoy-cooling",
     "text": "The general cooling circuit of the workshop is purged every quarter, "
             "to prevent the formation of deposits."},
    {"id": 9, "subject": "decoy-vibration",
     "text": "Excessive vibration in a machine signals a problem of balancing or "
             "of fixing to the floor."},
    {"id": 10, "subject": "decoy-bearings",
     "text": "Lubricating the bearings reduces wear; choose the lubricant "
             "according to the rotation speed and the applied load."},
    {"id": 11, "subject": "decoy-filters",
     "text": "Replacing the air filters prevents the fouling of the workshop "
             "ventilation ducts."},
]


QUERIES = [
    {"question": "What is the emergency stop procedure for pump P-42?",
     "relevant": [1], "facets": ["P-42"], "type": "single-pass"},
    {"question": "Compare the emergency stop procedures of pumps "
                 "P-12, P-42 and P-88.",
     "relevant": [0, 1, 2], "facets": ["P-12", "P-42", "P-88"],
     "type": "multi-facet"},
    # A question with NO answer in the corpus: the loop would run forever.
    {"question": "What is the emergency stop procedure for pump P-99?",
     "relevant": [], "facets": ["P-99"], "type": "no-answer"},
]


def main() -> None:
    data = {"fragments": FRAGMENTS, "queries": QUERIES}
    path = CORPUS / "fragments.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generating the Chapter 23 test corpus:")
    print(f"  + {path.name}: {len(FRAGMENTS)} fragments, "
          f"{len(QUERIES)} annotated queries")
    print("  (single-pass, multi-facet, and a question with NO answer, for the loop"
          " with no brake)")
    print("The running thread: Julien — pumps P-12 / P-42 / P-88, motor M-18.")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
