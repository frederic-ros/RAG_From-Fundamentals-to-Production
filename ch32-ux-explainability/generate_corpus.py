# -*- coding: utf-8 -*-
"""
generate_corpus.py — generates the Chapter 32 corpus (user experience).

Written to corpus/:
  - documents.json    : 16 fragments, each with its source document and page,
                        so a citation can point at something real;
  - reponses_rag.json : 30 pre-computed RAG answers, each with its blocks, its
                        retrieval and generation scores, its number of sources,
                        whether the sources contradict each other, the freshness,
                        and a `correcte` label (the ground truth for calibration);
  - signaux.json      : about 50 simulated IMPLICIT feedback events (source
                        reading, copy, reformulation, dwell time).

THE DOCUMENTS AND THE ANSWER BLOCKS ARE PAIRED. Attribution in Lab 32-1 matches
each block against the documents by lexical overlap; if the two drift apart in
translation, the fidelity collapses and the lab reports it as a quality problem
rather than as a broken pairing. The French baseline for the mean fidelity is 34%.

The forced signals at the end of generate_signals() name one query verbatim: it
must match one of the questions above, or Lab 32-4 has nothing to aggregate them
onto.

Run before the labs: python generate_corpus.py
"""

import json
import random
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)
random.seed(32)


def D(i, titre, texte, document, page):
    return {"id": f"D{i:02d}", "titre": titre, "texte": texte,
            "document": document, "page": page}


# THE DOCUMENTS AND THE ANSWER BLOCKS BELOW ARE PAIRED. Attribution in Lab 32-1
# matches each block of an answer against the documents by lexical overlap. If
# the two sides drift apart in the translation, the attribution fidelity
# collapses to zero and the lab reports it as a quality problem rather than as a
# broken pairing. The French baseline for the mean fidelity is 34%.
DOCUMENTS = [
    D(1, "Emergency stop P-42",
      "The emergency stop of pump P-42 cuts the electrical supply in under two "
      "seconds.", "Manual_P42.pdf", 12),
    D(2, "Cold stop P-42",
      "The cold stop follows a gradual procedure: reduce the flow, close the "
      "valves, then cut the motor after stabilisation.",
      "Manual_P42.pdf", 14),
    D(3, "Cavitation diagnosis",
      "Cavitation is diagnosed by a gravel-like noise and pitting on the vanes; "
      "a frequent cause is an available NPSH that is too low.",
      "Failure_guide.pdf", 5),
    D(4, "Cavitation remedy",
      "To correct cavitation, raise the pressure at the suction and reduce the "
      "temperature of the fluid.", "Failure_guide.pdf", 6),
    D(5, "Valve V-7 supplier",
      "Valve V-7 is supplied by Sulzer, reference VS-7-2026, lead time five "
      "working days.", "Suppliers.html", 1),
    D(6, "Bearing lubrication",
      "The bearings of the P-42 are lubricated every 500 hours with a "
      "high-temperature grease.", "Manual_P42.pdf", 22),
    D(7, "Flange tightening torque",
      "The tightening torque for DN80 flanges is 85 N.m, in a star pattern, in "
      "three increasing passes.", "Manual_P42.pdf", 30),
    D(8, "Lock-off of line 3",
      "Any intervention on line 3 requires a prior electrical lock-off and the "
      "signing of the zone.", "HSE_procedures.pdf", 8),
    D(9, "On-call",
      "The maintenance on-call line is extension 4242; out of hours, escalate to "
      "the shift supervisor.", "Directory.html", 1),
    D(10, "NPSH definition",
      "The available NPSH must always stay above the required NPSH, to avoid "
      "cavitation.", "Failure_guide.pdf", 4),
    D(11, "Gradual start-up",
      "The P-42 is started by priming, then raising the flow, then checking the "
      "vibration.", "Manual_P42.pdf", 16),
    D(12, "Grease specification",
      "The recommended grease is a lithium complex type, range -20 to 150 "
      "degrees C.", "Manual_P42.pdf", 23),
    D(13, "Hydraulic purge (recent)",
      "The current hydraulic purge opens valve V-5 first, then V-3, under the "
      "2025 revision of the procedure.", "HSE_procedures.pdf", 11),
    D(14, "Vibration thresholds",
      "Beyond 4.5 mm/s of RMS velocity, a planned stoppage of the P-42 must be "
      "scheduled.", "Failure_guide.pdf", 9),
    D(15, "Suction filter",
      "The suction filter is cleaned every 250 hours; fouling reduces the "
      "available NPSH.", "Manual_P42.pdf", 19),
    D(16, "Sealing check",
      "The sealing of the mechanical seal is checked visually on every round; "
      "any weeping is recorded.", "Manual_P42.pdf", 27),
]


# --- 30 pre-computed RAG answers, with ground truth for the calibration ---
def REP(i, question, blocs, s_ret, s_gen, n_src, contradiction, fraicheur,
        correcte):
    return {"id": f"R{i:02d}", "question": question, "blocs": blocs,
            "score_retrieval": s_ret, "score_generation": s_gen,
            "n_sources": n_src, "contradiction": contradiction,
            "fraicheur": fraicheur, "correcte": correcte}


REPONSES = [
    # --- High trust: high scores, several consistent sources, correct ---
    REP(1, "What is the cold stop procedure for the P-42?",
        ["The cold stop follows a gradual procedure.",
         "Reduce the flow, close the valves, then cut the motor after thermal "
         "stabilisation."],
        0.62, 0.70, 3, False, "up to date (rev. 2025)", True),
    REP(2, "How is cavitation diagnosed?",
        ["Cavitation is recognised by a gravel-like noise.",
         "It leaves pitting on the vanes; the frequent cause is an available "
         "NPSH that is too low."],
        0.58, 0.66, 2, False, "up to date", True),
    REP(3, "What is the tightening torque for DN80 flanges?",
        ["The tightening torque for DN80 flanges is 85 N.m.",
         "It is applied in a star pattern, in three increasing passes."],
        0.71, 0.74, 2, False, "up to date", True),
    REP(4, "How often should the bearings be lubricated?",
        ["The bearings are lubricated every 500 hours.",
         "A high-temperature grease is used."],
        0.66, 0.69, 2, False, "up to date", True),
    REP(5, "Who supplies valve V-7?",
        ["Valve V-7 is supplied by Sulzer.",
         "Its reference is VS-7-2026, for a lead time of five working days."],
        0.60, 0.64, 1, False, "up to date", True),
    REP(6, "How is the P-42 started?",
        ["Starting is done by priming.",
         "The flow is then raised, and the vibration checked."],
        0.57, 0.63, 2, False, "up to date", True),
    REP(7, "What is the number for the on-call line?",
        ["The maintenance on-call line is extension 4242."],
        0.55, 0.60, 1, False, "up to date", True),
    REP(8, "When is the suction filter cleaned?",
        ["The suction filter is cleaned every 250 hours.",
         "Fouling reduces the available NPSH."],
        0.61, 0.65, 2, False, "up to date", True),
    REP(9, "How is cavitation corrected?",
        ["To correct cavitation, raise the pressure at the suction.",
         "Also reduce the temperature of the fluid."],
        0.59, 0.67, 2, False, "up to date", True),
    REP(10, "What vibration threshold requires a stoppage?",
        ["Beyond 4.5 mm/s of RMS velocity, a planned stoppage must be "
         "scheduled."],
        0.64, 0.68, 1, False, "up to date", True),

    # --- Low trust: middling scores, a single source, or a contradiction ---
    REP(11, "What is the hydraulic purge procedure?",
        ["The hydraulic purge opens valve V-5 first, then V-3.",
         "Careful: an older procedure gave the reverse order."],
        0.34, 0.40, 2, True, "two versions in disagreement", False),
    REP(12, "Which grease exactly should be used?",
        ["The recommended grease is a lithium complex type.",
         "The temperature range runs from -20 to 150 degrees C."],
        0.30, 0.36, 1, False, "up to date", True),
    REP(13, "How long does the cold stop take?",
        ["The cold stop requires a thermal stabilisation.",
         "The precise duration is not clearly specified in the fragments "
         "retrieved."],
        0.28, 0.33, 1, False, "partial", False),
    REP(14, "What is the pilot pressure of the V-7?",
        ["Valve V-7 is pneumatically controlled.",
         "The exact pilot pressure does not appear clearly."],
        0.26, 0.31, 1, False, "partial", False),
    REP(15, "Must line 3 be locked off before an intervention?",
        ["An electrical lock-off is required.",
         "The detail of the signing remains to be confirmed by zone."],
        0.35, 0.42, 1, False, "up to date", True),
    REP(16, "What is the exact required NPSH of the P-42?",
        ["The available NPSH must stay above the required NPSH.",
         "The required numerical value is not in the fragments."],
        0.24, 0.30, 1, False, "partial", False),
    REP(17, "Is the purge done V-3 then V-5?",
        ["Under the 2025 revision it is V-5 then V-3.",
         "An older note contradicts that order."],
        0.33, 0.38, 2, True, "contradictory versions", False),
    REP(18, "Which grease for -30 degrees C?",
        ["The lithium complex grease covers -20 to 150 degrees C.",
         "For -30 degrees C the documentation does not settle it."],
        0.29, 0.34, 1, False, "outside the documented range", False),
    REP(19, "What torque for DN50 flanges?",
        ["The documentation gives the torque for DN80 (85 N.m).",
         "For DN50, no value is supplied."],
        0.31, 0.37, 1, False, "a risky extrapolation", False),
    REP(20, "How many hours before changing the seal?",
        ["The sealing is checked on every round.",
         "No replacement interval is specified."],
        0.27, 0.32, 1, False, "partial", False),

    # --- Abstention: scores below the critical threshold ---
    REP(21, "What is the energy efficiency of the P-42 at part load?",
        ["No relevant source was found on this precise point."],
        0.12, 0.15, 0, False, "absent", False),
    REP(22, "What is the make of the original electric motor?",
        ["This information appears in no indexed fragment."],
        0.10, 0.14, 0, False, "absent", False),
    REP(23, "What is the hourly cost of a stoppage on line 3?",
        ["Economic data not covered by the technical documentation."],
        0.09, 0.13, 0, False, "absent", False),
    REP(24, "What is the date of the next regulatory revision?",
        ["No revision date is available in the corpus."],
        0.11, 0.16, 0, False, "absent", False),
    REP(25, "Which software drives the P-42 controller?",
        ["Information not present in the indexed documentation."],
        0.08, 0.12, 0, False, "absent", False),

    # --- A few further edge cases, for the calibration ---
    REP(26, "How is the sealing of the seal checked?",
        ["The sealing of the mechanical seal is checked visually on every "
         "round.", "Any weeping is recorded."],
        0.56, 0.61, 1, False, "up to date", True),
    REP(27, "What is the temperature range of the grease?",
        ["The lithium complex grease covers the range -20 to 150 degrees C."],
        0.52, 0.58, 1, False, "up to date", True),
    REP(28, "What are the signs of a fouled filter?",
        ["Fouling of the suction filter reduces the available NPSH.",
         "That encourages the appearance of cavitation."],
        0.48, 0.55, 2, False, "up to date", True),
    REP(29, "What causes a gravel-like noise?",
        ["A gravel-like noise in the pump casing signals cavitation."],
        0.50, 0.57, 1, False, "up to date", True),
    REP(30, "Should a stoppage be planned at 5 mm/s of vibration?",
        ["Beyond 4.5 mm/s, a planned stoppage must be scheduled.",
         "At 5 mm/s the stoppage is therefore required."],
        0.53, 0.59, 1, False, "up to date", True),
]
# The types of implicit signal, with their parameters. A long source read or a
# copy is a silent "yes"; an immediate reformulation or an abandonment is a "no".
TYPES = [
    ("lecture_source", {"duree_s": lambda: random.choice([2, 5, 18, 22, 30, 1])}),
    ("copier_coller", {}),
    ("reformulation", {}),
    ("abandon", {}),
    ("vote", {"valeur": lambda: random.choice([1, -1])}),
]
QUESTIONS_SIG = [r["question"] for r in REPONSES[:12]]
DOCS_SIG = [d["document"] for d in DOCUMENTS]


def generate_signals(n=50):
    signaux = []
    for _ in range(n):
        typ, params = random.choice(TYPES)
        ev = {"type": typ,
              "requete": random.choice(QUESTIONS_SIG),
              "document": random.choice(DOCS_SIG)}
        for k, v in params.items():
            ev[k] = v() if callable(v) else v
        signaux.append(ev)
    # A few clear signals are forced, to make one query plainly problematic;
    # this is what Lab 32-4 analyses. The query text must match one of the
    # answers above, or the aggregation finds nothing to attach them to.
    mauvaise = "What is the hydraulic purge procedure?"
    for _ in range(4):
        signaux.append({"type": "reformulation", "requete": mauvaise,
                        "document": "Procedures_HSE.pdf"})
    signaux.append({"type": "lecture_source", "duree_s": 2,
                    "requete": mauvaise, "document": "Procedures_HSE.pdf"})
    return signaux


def main():
    (CORPUS / "documents.json").write_text(
        json.dumps(DOCUMENTS, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "reponses_rag.json").write_text(
        json.dumps(REPONSES, ensure_ascii=False, indent=2), encoding="utf-8")
    signaux = generate_signals()
    (CORPUS / "signaux.json").write_text(
        json.dumps(signaux, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Corpus written to {CORPUS}/:")
    print(f"  documents.json    : {len(DOCUMENTS)} fragments (document + page)")
    print(f"  reponses_rag.json : {len(REPONSES)} pre-computed answers "
          f"({sum(r['correcte'] for r in REPONSES)} correct)")
    print(f"  signaux.json      : {len(signaux)} implicit feedback signals")


if __name__ == "__main__":
    main()
