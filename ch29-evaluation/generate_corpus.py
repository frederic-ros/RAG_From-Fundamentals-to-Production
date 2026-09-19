# -*- coding: utf-8 -*-
"""
generate_corpus.py — generates the Chapter 29 corpus (evaluation).

Written to corpus/:
  - documents.json  : 18 maintenance fragments
  - golden_set.json : 12 annotated cases, including cases designed to make one
                      precise score COLLAPSE

Three of the twelve are traps, and each targets a different component:
  - G08 (distinction) : D01 and D02 are lexically very close; can the retriever
                        tell the emergency stop from the cold stop?
  - G09 (out of corpus): no fragment holds the answer. Context recall must
                        collapse and the system must abstain.
  - G10 (multi-hop)   : the complete answer needs D14 AND D04. recall@1 must be
                        0.50 and recall@3 must be 1.00, which is what points at
                        the chunker rather than the generator.

TWO WORDINGS IN THIS FILE ARE CALIBRATED against thresholds elsewhere, and both
carry a comment explaining why: the verb form in G10, and the opening of G09.
Re-run Labs 29-1 and 29-7 after editing either.

Run before the labs: python generate_corpus.py
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


def D(i, titre, texte):
    return {"id": f"D{i:02d}", "titre": titre, "texte": texte}


DOCUMENTS = [
    # D01 and D02 must stay LEXICALLY VERY CLOSE: the same pump, the same word
    # "stop". Case G08 tests whether the retriever can tell them apart. Pull them
    # further apart in the translation and that test stops testing anything.
    D(1, "Emergency stop of the pump",
      "The emergency stop of pump P-42 cuts the electrical supply in under two "
      "seconds. It is used only in the event of immediate danger to people."),
    D(2, "Cold stop of the pump",
      "The cold stop of pump P-42 follows a gradual procedure: reduce the flow, "
      "close the valves, then cut the motor after thermal stabilisation. Typical "
      "duration: fifteen minutes."),
    D(3, "Cavitation — diagnosis",
      "Cavitation is diagnosed by a gravel-like noise in the pump casing and by "
      "pitting on the vanes. A frequent cause: an available NPSH below the "
      "required NPSH."),
    D(4, "Cavitation — remedy",
      "To correct cavitation, raise the pressure at the suction: raise the tank "
      "level, reduce the upstream pressure losses, or lower the pump speed."),
    D(5, "Bearings — greasing interval",
      "The bearings of pump P-42 are greased every 2000 hours of operation, with "
      "a lithium NLGI 2 grease."),
    D(6, "Mechanical seal — replacement",
      "Replacing the mechanical seal requires prior electrical lock-off and "
      "draining of the pump casing."),
    D(7, "Electrical lock-off",
      "Electrical lock-off has five steps: separation, locking, identification, "
      "verification of the absence of voltage, and earthing. It precedes any "
      "intervention."),
    D(8, "Flange tightening torque",
      "The tightening torque for DN100 flanges is 90 N.m, applied crosswise in "
      "three passes."),
    D(9, "Laser alignment",
      "Laser alignment of the coupling is done cold. The tolerance on parallel "
      "misalignment is 0.05 mm."),
    D(10, "Vibration monitoring",
      "Vibration monitoring measures the RMS velocity in mm/s. Beyond 7.1 mm/s "
      "on pump P-42, an intervention is required."),
    D(11, "Water hammer — protection",
      "Protection against water hammer rests on bladder surge arresters and slow "
      "closing of the motorised valves."),
    D(12, "Motor overheating — thresholds",
      "Motor overheating trips beyond 130 degrees C at the stator. The system "
      "then cuts the supply automatically."),
    D(13, "Seal leak — alert threshold",
      "A seal leak above 10 drops per minute raises a corrective maintenance "
      "alert."),
    D(14, "Suction filter — upkeep",
      "The suction filter is cleaned every month. Fouling increases the pressure "
      "losses and encourages cavitation."),
    D(15, "Pump start-up — procedure",
      "Starting the pump requires prior priming and the opening of the suction "
      "valve before the motor is energised."),
    D(16, "Minimum tank level",
      "The minimum level of the suction tank is 1.2 metres. Below that, the risk "
      "of cavitation becomes high."),
    D(17, "Failure history of P-42",
      "Pump P-42 had two episodes of cavitation in 2025, corrected by raising "
      "the tank level and cleaning the suction filter."),
    D(18, "Spare parts for P-42",
      "The critical spare parts for pump P-42 are: the mechanical seal "
      "(ref. G-220), the front bearing (ref. R-310) and the impeller."),
]


# The golden set. Each case carries an "expected_diagnosis" saying, for the
# trapped cases, which component we are trying to make fail. That is the
# teaching point of Lab 29-1.
def G(qid, question, attendus, reference, categorie="ok", diagnostic=""):
    return {"id": qid, "question": question, "expected_fragments": attendus,
            "reference": reference, "category": categorie,
            "expected_diagnosis": diagnostic}


GOLDEN = [
    G("G01", "How is cavitation diagnosed in the pump casing?",
      ["D03"],
      "Cavitation is recognised by a gravel-like noise in the pump casing and "
      "by pitting on the vanes, often due to an insufficient NPSH."),
    G("G02", "How is cavitation corrected?",
      ["D04"],
      "Raise the pressure at the suction: raise the tank level, reduce the "
      "upstream pressure losses, or lower the speed."),
    G("G03", "What are the steps of electrical lock-off?",
      ["D07"],
      "Separation, locking, identification, verification of the absence of "
      "voltage, and earthing."),
    G("G04", "How often are the bearings greased?",
      ["D05"],
      "Every 2000 hours of operation, with a lithium NLGI 2 grease."),
    G("G05", "What vibration threshold requires an intervention?",
      ["D10"],
      "Beyond 7.1 mm/s of RMS velocity on pump P-42."),
    G("G06", "What is the tightening torque for DN100 flanges?",
      ["D08"],
      "90 N.m, applied crosswise in three passes."),
    G("G07", "What is the minimum level of the suction tank?",
      ["D16"],
      "1.2 metres; below that, the risk of cavitation is high."),
    # --- A case designed to test the FINE DISTINCTION (a weakness of the retriever)
    G("G08", "What is the emergency stop procedure for the pump?",
      ["D01"],
      "The emergency stop cuts the supply in under two seconds, only in the "
      "event of immediate danger to people.",
      categorie="distinction",
      diagnostic="retriever: a risk of confusing the emergency stop (D01) with "
                 "the cold stop (D02), which are lexically very close."),
    # --- A case with NO answer in the corpus: context recall must collapse
    # THE WORDING HERE IS CALIBRATED AGAINST THE ABSTENTION THRESHOLD (0.30 in
    # Lab 29-7). This question has no answer in the corpus, so its top-1 score
    # must fall BELOW that threshold or the abstention never fires on the one
    # case it exists for. A first English wording opened with "What is the ... of
    # the ... under the", and those grammatical words alone lifted the score to
    # 0.396 — above the threshold. The out-of-corpus case sailed through while a
    # legitimate one abstained instead: the demonstration ran inverted, with no
    # error. Check the top-1 score if you reword this.
    G("G09", "Which IE4 efficiency class does the frequency inverter certify "
             "under IEC 60034-30?",
      [],
      "This information is not present in the documentation supplied.",
      categorie="out_of_corpus",
      diagnostic="retrieval/corpus: no fragment holds the answer; the context "
                 "recall must collapse. The right behaviour is abstention."),
    # --- A multi-hop case: the complete answer needs TWO fragments
    # THE VERB FORM HERE IS CALIBRATED. "how to correct it" matches D04's "To
    # correct cavitation"; "how is it corrected" would instead match D17's
    # "corrected by", a distractor holding both "cavitation" and "suction
    # filter". French inflection separated the two for free (corriger against
    # corriges); English does not. With the wrong form, recall@3 falls to 0.50
    # and the lesson "raising k fixes it" stops being true.
    G("G10", "Why does the suction filter influence cavitation, and how to "
             "correct it?",
      ["D14", "D04"],
      "A fouled filter increases the pressure losses and encourages cavitation; "
      "it is corrected by raising the pressure at the suction (cleaning the "
      "filter, raising the tank level).",
      categorie="multi_hop",
      diagnostic="chunker/retriever: the complete answer is spread across two "
                 "fragments; a retrieval at k=1 misses half of it."),
    G("G11", "At what temperature does the motor go into safe state?",
      ["D12"],
      "Beyond 130 degrees C at the stator, the supply is cut automatically."),
    G("G12", "What are the critical spare parts for pump P-42?",
      ["D18"],
      "The mechanical seal (G-220), the front bearing (R-310) and the impeller."),
]


def main():
    (CORPUS / "documents.json").write_text(
        json.dumps(DOCUMENTS, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "golden_set.json").write_text(
        json.dumps(GOLDEN, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Chapter 29 corpus generated in:", CORPUS)
    print(f"  - documents.json  : {len(DOCUMENTS)} fragments")
    print(f"  - golden_set.json : {len(GOLDEN)} cases "
          f"(including fine distinction, out-of-corpus, multi-hop)")


if __name__ == "__main__":
    main()
