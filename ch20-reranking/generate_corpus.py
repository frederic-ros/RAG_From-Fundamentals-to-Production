# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 20 (re-ranking).

A deterministic corpus of maintenance fragments, designed to bring out the
chapter's points:

  - NEIGHBOURING CODES (motors M-17, M-18, M-19; pump P-42): the bi-encoder
    confuses them, the cross-encoder tells them apart (Labs 20-1, 20-2, 20-3);
  - REDUNDANT fragments (several wordings of the same fact about M-18) alongside
    DIVERSE ones (safety, supplier, frequency): the raw material of MMR (Lab 20-4);
  - what is needed to replay Julien's case (the most recent M-18 procedure) on a
    complete pipeline (Lab 20-5);
  - queries annotated with the indices of the relevant fragments, to measure MRR
    and nDCG (Lab 20-6).

TWO PROPERTIES MUST SURVIVE ANY EDIT.

  1. The distractors M-17 and M-19 must stay lexically ALMOST IDENTICAL to the
     M-18 fragment. That resemblance is what makes the bi-encoder rank the right
     fragment badly, and the whole chapter starts from that failure.
  2. Fragments 4, 5 and 6 must say the SAME THING about M-18 — the 100-hour
     interval — in three different wordings. If a translation makes them differ
     in substance, MMR has nothing left to deduplicate and Lab 20-4 measures
     nothing.

The corpus is written to `corpus/fragments.json`:
    { "fragments": [ {"id": int, "text": str, "subject": str}, ... ],
      "queries":   [ {"question": str, "relevant": [ids], "best": id}, ... ] }

Run before the labs: python generate_corpus.py
No API key, no network.
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# Each fragment is a short maintenance text. The "distractors" speak of
# NEIGHBOURING codes (M-17, M-19, P-42) that are very close semantically.
FRAGMENTS = [
    # --- The right fragment for M-18 (the target of several queries) ---------
    {"id": 0, "subject": "M-18",
     "text": "Maintenance procedure for motor M-18: cut the supply, remove the "
             "casing, check the bearings, then reassemble to the prescribed "
             "torque. This procedure is the reference in force."},

    # --- Distractors: neighbouring codes, very close indeed -------------------
    {"id": 1, "subject": "M-17",
     "text": "Maintenance procedure for motor M-17: cut the supply, remove the "
             "casing, check the shaft and the bearings, then reassemble. Motor "
             "M-17 is fitted to the older lines."},
    {"id": 2, "subject": "M-19",
     "text": "Maintenance procedure for motor M-19: isolate the circuit, remove "
             "the cover, inspect the winding and the bearings, then close up. "
             "Motor M-19 is progressively replacing the M-17."},
    {"id": 3, "subject": "P-42",
     "text": "Pump P-42 is driven by a motor of the M series; in the event of a "
             "failure, refer to the procedure for the corresponding motor. Pump "
             "P-42 requires a purge before any intervention."},

    # --- REDUNDANT fragments about M-18: the raw material of MMR --------------
    # All three say the same thing — inspection every 100 hours — in three
    # different wordings. Keep it that way.
    {"id": 4, "subject": "M-18",
     "text": "Motor M-18 must be inspected every 100 hours of operation. This "
             "periodic inspection of the M-18 is mandatory."},
    {"id": 5, "subject": "M-18",
     "text": "Inspection of motor M-18: a check is required every 100 cycles of "
             "use, that is roughly every 100 hours of running."},
    {"id": 6, "subject": "M-18",
     "text": "The inspection interval for motor M-18 is set at 100 hours. "
             "Respecting that interval on the M-18 avoids premature wear."},

    # --- DIVERSE fragments, other facets, useful for diversity ----------------
    {"id": 7, "subject": "M-18-safety",
     "text": "Safety: before any work on motor M-18, lock off the equipment and "
             "wear the protective gear. Failing to do so exposes you to a serious "
             "electrical risk."},
    {"id": 8, "subject": "M-18-supplier",
     "text": "Motor M-18 is supplied by Delta-Meca; spare parts for the M-18 are "
             "ordered under catalogue reference 18-DM."},
    {"id": 9, "subject": "M-18-failure",
     "text": "If motor M-18 overheats, a fault code flashes: let it cool, check "
             "the ventilation, then restart the M-18."},

    # --- The old and the recent M-18 procedure (Julien's case, freshness) -----
    {"id": 10, "subject": "M-18-2019",
     "text": "Procedure M-18 (2019 revision): maintenance of motor M-18, removal "
             "of the casing and inspection of the bearings. A detailed and "
             "complete document, but superseded since."},
    {"id": 11, "subject": "M-18-2025",
     "text": "Procedure M-18 (2025 revision, in force): updated maintenance of "
             "motor M-18, a new tightening torque and an added vibration check. "
             "The most recent version."},

    # --- Distant thematic noise, filling out the corpus -----------------------
    {"id": 12, "subject": "hydraulics",
     "text": "The main hydraulic circuit must be purged every quarter. Check the "
             "pressure and the absence of leaks on the hoses."},
    {"id": 13, "subject": "electrical",
     "text": "The main electrical board is checked annually. Retighten the "
             "terminals and measure the insulation of the outgoing ways."},
    {"id": 14, "subject": "ventilation",
     "text": "The workshop ventilation grilles are cleaned monthly, to avoid the "
             "build-up of dust and the overheating of the cabinets."},
]


# Annotated queries: for each, the genuinely relevant fragment(s).
QUERIES = [
    {"question": "What is the maintenance procedure for motor M-18?",
     "relevant": [0, 11, 10], "best": 0},
    {"question": "What is the most recent procedure for motor M-18?",
     "relevant": [11], "best": 11},
    # NOTE ON THE WORDING OF THESE TWO. They deliberately avoid the words used
    # in the fragments they should retrieve — "checking" against "inspected",
    # "essentials" against "procedure". French inflection did this for free
    # ("inspecter" is not "inspecte"), but English does not: a literal
    # translation put the query's own verb in its answer, the bi-encoder found
    # the right fragment at rank 1, and the re-ranking of Lab 20-6 had nothing
    # left to improve. Check the rank before and after if you edit these.
    {"question": "How often does motor M-18 need checking?",
     "relevant": [4, 5, 6], "best": 4},
    {"question": "What are the essentials on motor M-18 "
                 "(procedure, safety, breakdowns)?",
     "relevant": [0, 7, 9, 4], "best": 0},
]


def main() -> None:
    data = {"fragments": FRAGMENTS, "queries": QUERIES}
    path = CORPUS / "fragments.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generating the Chapter 20 test corpus:")
    print(f"  + {path.name}: {len(FRAGMENTS)} fragments, {len(QUERIES)} annotated queries")
    print("\nThe running thread: motors M-17/M-18/M-19 (neighbouring codes), pump P-42,")
    print("redundant fragments about the M-18 (for MMR), 2019/2025 versions (freshness).")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
