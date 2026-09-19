# -*- coding: utf-8 -*-
"""
generate_corpus.py — test corpus for Chapter 22 (the points of failure).

A deterministic corpus of technical and HR fragments, designed so that the
pipeline can be SABOTAGED one failure at a time (Lab 22-1), the failures
MEASURED (Lab 22-2), a real bad answer DIAGNOSED (Lab 22-3), and so that it can
be shown that some flaws yield only to a LOOP (Lab 22-4).

Two running examples, carried over from the earlier chapters:
  - Julien (maintenance): pumps P-12 / P-42 / P-88, motor M-18;
  - Claire (HR): remote work for apprentices, permanent staff and interns, plus
    the seniority bonus.

Each "good" document is written in the vocabulary of the SOLUTION; around it,
thematically close decoys — and, for the ranking lab, near-duplicates — blur the
search.

Note on the near-duplicates: they repeat the vocabulary of the question
("emergency stop procedure", "P-42 pump") WITHOUT describing the procedure. That
surface overlap is exactly what tips the ranking, and it is the point of the
"missed at ranking" sabotage. Do not shorten them.

Writes to corpus/fragments.json:
  { "fragments": [ {"id", "text", "subject"} ... ],
    "near_duplicates": [ ... ],
    "queries": [ {"question", "relevant", "failure", "parts"?} ... ] }

Run before the labs: python generate_corpus.py
No API key, no network.
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


FRAGMENTS = [
    # --- Good documents — maintenance (Julien) ----------------------------
    {"id": 0, "subject": "stop-P12",
     "text": "Emergency stop procedure for the P-12 pump: cut the supply at the "
             "main isolator, close the suction valve, then purge the circuit. "
             "Full immobilisation time: thirty seconds."},
    {"id": 1, "subject": "stop-P42",
     "text": "Emergency stop procedure for the P-42 pump: hit the mushroom-head "
             "button, isolate the discharge circuit and lock out the equipment. "
             "A hydraulic brake stops the shaft in five seconds."},
    {"id": 2, "subject": "stop-P88",
     "text": "Emergency stop procedure for the P-88 pump: trigger the automatic "
             "stop through the overpressure sensor, then close the upstream and "
             "downstream valves by hand. Immobilisation in ten seconds."},
    {"id": 3, "subject": "overheating-M18",
     "text": "Abnormal temperature rise of the M-18 motor: a cooling fault, worn "
             "bearings or mechanical overload. Check the ventilation flow and "
             "the condition of the bearings."},

    # --- Good documents — HR (Claire) -------------------------------------
    {"id": 4, "subject": "rw-apprentices",
     "text": "Remote work for apprentices: two days per week at most, subject to "
             "the tutor's agreement and to being on site on practical training "
             "days."},
    {"id": 5, "subject": "rw-permanent",
     "text": "Remote work for permanent staff: up to three days per week after "
             "six months of service, on approval by the team manager."},
    {"id": 6, "subject": "rw-interns",
     "text": "Remote work for interns: one day per week at most, supervised by "
             "the placement tutor, and never during the first month of the "
             "agreement."},
    {"id": 7, "subject": "seniority-bonus",
     "text": "Seniority bonus: paid after three years of effective service, "
             "calculated under the collective agreement; apprentices are "
             "excluded from it."},

    # --- Thematically close decoys ----------------------------------------
    {"id": 8, "subject": "decoy-general-stop",
     "text": "The general emergency stop procedure of the workshop cuts the main "
             "supply and must be known to every operator."},
    {"id": 9, "subject": "decoy-pump-maintenance",
     "text": "General comparison of pump maintenance: lubrication intervals, "
             "costs and availability of the models, with no detail per "
             "individual machine."},
    {"id": 10, "subject": "decoy-M17",
     "text": "Overheating of the M-17 motor, the previous generation, is treated "
             "by replacing the heat sink and cleaning the fins."},
    {"id": 11, "subject": "decoy-general-rw",
     "text": "General remote work charter: equipment provided, hours of "
             "availability and confidentiality rules applicable to everyone."},
    {"id": 12, "subject": "decoy-leave",
     "text": "The rules for booking paid leave depend on length of service and "
             "on the reference period defined by the company."},
    {"id": 13, "subject": "decoy-payslip",
     "text": "The payslip itemises the bonuses paid but does not state the "
             "conditions under which each bonus is awarded."},
    {"id": 14, "subject": "decoy-valves",
     "text": "Isolation valves must be inspected annually to guarantee their "
             "tightness and their operability."},
    {"id": 15, "subject": "decoy-ventilation",
     "text": "Replacing the air filters improves efficiency and prevents fouling "
             "of the workshop ventilation ducts."},
    {"id": 16, "subject": "decoy-safety",
     "text": "General safety procedure: wearing protective equipment and "
             "respecting the access rules to the machine zones."},
    {"id": 17, "subject": "decoy-apprenticeship",
     "text": "An apprenticeship contract alternates periods in the company and "
             "in the training centre, on a calendar fixed at the start of the "
             "year."},
    {"id": 18, "subject": "decoy-cooling",
     "text": "The general cooling circuit of the workshop is purged every "
             "quarter to avoid the build-up of deposits."},
    {"id": 19, "subject": "decoy-bearings",
     "text": "Lubricating the bearings reduces wear; choose the lubricant "
             "according to the rotation speed and the applied load."},
]


# Near-duplicates of the good P-42 document: for the "missed at ranking"
# sabotage, they surround the number one and push it down without ever
# answering the question. They DELIBERATELY reuse the vocabulary of the
# question — "procedure", "emergency stop", "P-42 pump" — while NOT describing
# the procedure. That surface overlap is what tips the ranking.
NEAR_DUPLICATES = [
    {"id": 100, "subject": "near-P42-a",
     "text": "The emergency stop procedure for the P-42 pump is recalled at the "
             "head of the service log; the emergency stop procedure must be "
             "displayed near the P-42 pump."},
    {"id": 101, "subject": "near-P42-b",
     "text": "Training on the emergency stop procedure: the P-42 pump serves as "
             "the example; review the emergency stop procedure for the P-42 "
             "pump every quarter."},
    {"id": 102, "subject": "near-P42-c",
     "text": "The statutory notice mentions the emergency stop procedure for the "
             "P-42 pump; the emergency stop procedure for the P-42 pump appears "
             "in the register."},
    {"id": 103, "subject": "near-P42-d",
     "text": "Audit of the emergency stop procedure: the P-42 pump was checked; "
             "the emergency stop procedure for the P-42 pump is found "
             "compliant."},
    {"id": 104, "subject": "near-P42-e",
     "text": "History: the emergency stop procedure for the P-42 pump was "
             "revised; the former emergency stop procedure for the P-42 pump is "
             "archived."},
]


QUERIES = [
    # Labs 22-1 and 22-3: a question whose good document is unique and identifiable.
    {"question": "What is the emergency stop procedure for the P-42 pump?",
     "relevant": [1], "failure": "ranking"},
    # Lab 22-1 (representation): a question phrased away from the document's wording.
    {"question": "How does the emergency stop of the P-42 work?",
     "relevant": [1], "failure": "representation"},
    # Labs 22-1 and 22-4: a multi-part question (incompleteness).
    {"question": "Compare the emergency stop procedures of pumps P-12, P-42 and P-88.",
     "relevant": [0, 1, 2], "failure": "incomplete",
     "parts": ["P-12", "P-42", "P-88"]},
    # Lab 22-4: a multi-part HR question (apprentices / permanent / interns).
    {"question": "What are the remote work rules for apprentices, permanent "
                 "staff and interns?",
     "relevant": [4, 5, 6], "failure": "incomplete",
     "parts": ["apprentices", "permanent", "interns"]},
    # Lab 22-3: a "missing content" case to diagnose (the good document is removed).
    {"question": "What are the remote work entitlements of apprentices?",
     "relevant": [4], "failure": "missing_content"},
]


def main() -> None:
    data = {"fragments": FRAGMENTS, "near_duplicates": NEAR_DUPLICATES,
            "queries": QUERIES}
    path = CORPUS / "fragments.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generating the Chapter 22 test corpus:")
    print(f"  + {path.name}: {len(FRAGMENTS)} fragments, "
          f"{len(NEAR_DUPLICATES)} near-duplicates, {len(QUERIES)} annotated queries")
    print("\nEach good document is written in the \"language of the solution\";")
    print("the decoys are thematically close but off the subject.")
    print("Running examples: Julien (pumps P-12/P-42/P-88, motor M-18) and Claire (HR).")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
