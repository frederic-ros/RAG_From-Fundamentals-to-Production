# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 21 (query transformation).

A deterministic corpus of technical fragments, built to reveal the gap between
the language of the PROBLEM (the user's words) and the language of the SOLUTION
(the words of the documents). Each "good" document is written in the language of
the solution; the questions are written in the language of the problem.

The content each lab needs:

  - Lab 21-1: a "bearing defect / vibration signature" document that the question
    "an odd noise at start-up" does not find directly;
  - Lab 21-2: an "overheating of motor M-18" document, for HyDE;
  - Lab 21-3: two maintenance documents (pump A, pump B), for the decomposition;
  - Lab 21-4: a "safety procedure for pump P-42" document, for the rewriting;
  - Labs 21-5 and 21-6: all of the above, plus a "rules for awarding the bonus"
    document for the step-back, and assorted decoys.

Run before the labs: python generate_corpus.py
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


FRAGMENTS = [
    # --- The good documents, in the language of the SOLUTION -----------------
    # NOTE. This fragment must NOT contain the surface words of the question
    # that should find it ("noise", "odd", "start-up"). The whole chapter opens
    # on that gap: the user says "an odd noise at start-up", the document says
    # "vibration signature" and "commissioning". A first translation left
    # "start-up phase" here, the raw question matched it directly at rank 1, and
    # Lab 21-1 had no failure left to demonstrate.
    {"id": 0, "subject": "bearing",
     "text": "Diagnosis of bearing defects: vibration signature and acoustic "
             "signature. Spectral analysis during commissioning reveals "
             "bearing anomalies and imbalance."},
    {"id": 1, "subject": "overheating-M18",
     "text": "Abnormal temperature rise on the M-18 drive unit: cooling failure, "
             "bearing wear or mechanical overload. Check the ventilation flow "
             "and the condition of the bearings."},
    {"id": 2, "subject": "pump-A",
     "text": "Maintenance of pump A: lubrication every 100 hours, inspection of "
             "the sealing gaskets and a check on the alignment of the shaft."},
    {"id": 3, "subject": "pump-B",
     "text": "Maintenance of pump B: monthly cleaning, replacement of the "
             "filters and a check on the discharge pressure."},
    {"id": 4, "subject": "safety-P42",
     "text": "Safety procedure for pump P-42: lock off the equipment, check that "
             "the valves are closed before any start-up and wear the required "
             "protective gear."},
    {"id": 5, "subject": "bonus-rules",
     "text": "Rules for awarding the long-service bonus: eligibility conditions, "
             "the minimum period of service and the method of calculation under "
             "the applicable collective agreement."},

    # --- Decoys, thematically close: neighbouring language, wrong subject ----
    {"id": 6, "subject": "decoy-electrical-noise",
     "text": "The noises of an electric motor in normal operation come from the "
             "fan and indicate no anomaly."},
    {"id": 7, "subject": "decoy-slow-start",
     "text": "A slow start of the system may be due to a weak battery or to "
             "faulty wiring in the control circuit."},
    {"id": 8, "subject": "decoy-overheating-M17",
     "text": "Overheating of motor M-17 (the older generation) is dealt with by "
             "replacing the heat sink."},
    {"id": 9, "subject": "decoy-cooling",
     "text": "The general cooling circuit of the workshop is purged every "
             "quarter, to prevent the formation of deposits."},
    {"id": 10, "subject": "decoy-general-maintenance",
     "text": "A general comparison of pump maintenance: intervals, costs and the "
             "availability of the models in service, with no detail per "
             "individual item of equipment."},
    {"id": 11, "subject": "decoy-lubrication",
     "text": "Lubricating the bearings reduces wear; choose the lubricant "
             "according to the rotation speed and the load."},
    {"id": 12, "subject": "decoy-general-safety",
     "text": "General workshop safety procedure: wearing protective equipment "
             "and respecting the access instructions."},
    {"id": 13, "subject": "decoy-valves",
     "text": "The isolation valves must be checked annually, to guarantee their "
             "sealing and their operability."},
    {"id": 14, "subject": "decoy-bonus-payslip",
     "text": "The payslip details the bonuses paid, but does not state the "
             "conditions for awarding each bonus."},
    {"id": 15, "subject": "decoy-leave",
     "text": "The rules for booking paid leave depend on length of service and "
             "on the reference period defined by the company."},
    {"id": 16, "subject": "decoy-filters",
     "text": "Replacing the air filters improves the output and prevents the "
             "fouling of the ventilation ducts."},
    {"id": 17, "subject": "decoy-general-vibration",
     "text": "Excessive vibration in a machine signals a problem of balancing or "
             "of fixing to the floor."},
    {"id": 18, "subject": "decoy-motor-M18-generic",
     "text": "Nominal characteristics of the M-18: a three-phase asynchronous "
             "machine installed on several lines; see the manufacturer's "
             "catalogue for the dimensions and the torques."},
    {"id": 19, "subject": "decoy-shutdown-procedure",
     "text": "The emergency shutdown procedure cuts the general supply and must "
             "be known to every operator."},
]


# Annotated queries: type = the ideal transformation, for the router and benchmark.
#
# EACH QUESTION IS CALIBRATED ON A ROUTER BRANCH. Before editing one, check that
# it still triggers the branch named in its "type": run lab21-5, which prints the
# routing decision for all five.
QUERIES = [
    # "noise", "odd" and "start-up" are bridge words; none of them appears in
    # fragment 0, which speaks of "vibration signature" and "bearing defects".
    {"question": "The motor is making an odd noise at start-up.",
     "relevant": [0], "type": "hyde", "history": []},
    # "hot" is a bridge word; fragment 1 says "temperature rise".
    {"question": "Why does motor M-18 run hot?",
     "relevant": [1], "type": "hyde", "history": []},
    {"question": "Compare the maintenance of pump A and pump B.",
     "relevant": [2, 3], "type": "decomposition", "history": []},
    # "its" is the anaphora the rewriting branch keys on. Taken alone the
    # question could match any safety procedure; the history supplies P-42.
    {"question": "What is its safety procedure?",
     "relevant": [4], "type": "rewriting",
     "history": ["Tell me about pump P-42.",
                 "Pump P-42 is used for cooling the reactor."]},
    # "bonus" plus the proper noun "Dupont" trigger the step-back branch.
    {"question": "Is employee Dupont entitled to that bonus in March 2026?",
     "relevant": [5], "type": "step_back", "history": []},
]


def main() -> None:
    data = {"fragments": FRAGMENTS, "queries": QUERIES}
    path = CORPUS / "fragments.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generating the Chapter 21 test corpus:")
    print(f"  + {path.name} : {len(FRAGMENTS)} fragments, "
          f"{len(QUERIES)} annotated queries")
    print("\nEach good document is written in the \"language of the solution\" "
          "(vocabulaire technique) ;")
    print("the decoys are thematically close but off the subject.")
    print("The running thread: Julien (maintenance) — motor M-18, pumps A/B, pump P-42.")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
