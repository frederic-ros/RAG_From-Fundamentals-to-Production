# -*- coding: utf-8 -*-
"""
generate_corpus.py — generates the Chapter 36 lab corpus.

Written to corpus/:
  - documents.json : 14 documents carrying the metadata from which the
                     calibration is deduced (folder, date, status, provenance,
                     consultations);
  - questions.json : 6 questions whose ground truth is the document an EXPERT
                     would choose — not necessarily the most similar one.

FIVE OF THE SIX QUESTIONS ARE TRAPS. The semantically closest document is a
draft, a FAQ or a SUPERSEDED version. Only the business calibration picks the
right one. That is the thesis of the book, put to the test of a figure.

TWO PROPERTIES MUST SURVIVE ANY EDIT.

  1. The right document must NOT be the closest match. If a translation makes the
     in-force agreement the most similar, the naive retrieval starts succeeding
     and the demonstration collapses.
  2. But the gap must stay small enough for the calibration to overturn it. A
     first English wording of the FAQ used "remote work", two tokens against the
     French single token "teletravail", which doubled its weight in the TF-IDF
     vector and put it beyond the reach of the calibration.

Lab 36-1 reports recall@1 and MRR, before and after. The French baseline is
33% -> 100% and 0.47 -> 1.00, with 2 of 6 correct becoming 6 of 6.

Run before the lab: python generate_corpus.py
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


def D(id, titre, texte, dossier, date, statut="en vigueur", provenance="interne",
      remplace_par=None, consultations=None, corrections=None):
    d = {"id": id, "titre": titre, "texte": texte, "dossier": dossier,
         "date": date, "statut": statut, "provenance": provenance}
    if remplace_par:
        d["remplace_par"] = remplace_par
    if consultations is not None:
        d["consultations"] = consultations
    if corrections:
        d["corrections_expertes"] = corrections
    return d


DOCUMENTS = [
    # ---- HR case (Claire): remote work --------------------------------------
    # THE TRAP: the FAQ and the DRAFT agreement resemble the question most, but
    # it is the agreement IN FORCE that governs — and it says two days, not
    # three. That gap between resemblance and authority is the whole chapter.
    # If a translation makes the in-force agreement the closest match, the naive
    # retrieval starts succeeding and the demonstration collapses.
    #
    # "telework" is deliberately ONE token, mirroring the French "teletravail".
    # A two-word term such as "remote work" contributes twice to the TF-IDF
    # vector, which inflated the FAQ score beyond what the calibration could
    # overcome and left Q1 failing.
    D("RH-FAQ", "Internal FAQ — telework",
      "Telework is possible up to three days a week, depending on your manager. "
      "This FAQ summarises the current practices for telework.",
      dossier="/hr/faq/", date="2025-09-01", provenance="interne",
      consultations=180),
    D("RH-PROJET", "Draft telework agreement (unsigned)",
      "This draft agreement provides for telework of up to three days a week for "
      "all staff. A working document.",
      dossier="/hr/drafts/", date="2024-03-10", statut="brouillon",
      provenance="interne", consultations=40),
    D("RH-ACCORD", "Collective telework agreement (in force)",
      "The collective agreement authorises telework of two days a week, with "
      "possible derogation.",
      dossier="/hr/agreements/validees/", date="2026-01-15", statut="en vigueur",
      provenance="interne validee", consultations=95),
    D("RH-NOTE", "Service note — hybrid organisation",
      "A service note recalls the principles of hybrid organisation and refers "
      "to the collective agreement for the rules on telework.",
      dossier="/hr/notes/", date="2026-02-20", provenance="interne",
      consultations=60),

    # ---- Maintenance case (Julien): overheating of press A14 ----------------
    # THE TRAP: PROC-448 v4 (superseded) is very similar indeed, but v5 replaces it.
    D("PROC-448-v4", "PROC-448 v4 — overheating of press A14 (superseded)",
      "Intervention procedure in the event of overheating of press A14: stop, "
      "cooling, check. Version 4.",
      dossier="/maintenance/procedures/archive/", date="2024-05-01",
      statut="remplacee", provenance="interne validee",
      remplace_par="PROC-448-v5", consultations=70),
    D("PROC-448-v5", "PROC-448 v5 — overheating of press A14 (in force)",
      "Intervention procedure in the event of overheating of press A14: "
      "emergency stop, lock-off, controlled cooling, safety verification before "
      "return to service. Version 5.",
      dossier="/maintenance/procedures/validees/", date="2026-03-15",
      statut="en vigueur", provenance="interne validee", consultations=120),
    D("SEC-012", "SEC-012 — general safety instruction for presses",
      "General safety instruction applicable to presses: wearing PPE, "
      "compulsory electrical lock-off before any intervention, a safety "
      "perimeter. A regulatory document, legally binding.",
      dossier="/maintenance/safety/validees/", date="2025-11-10",
      statut="en vigueur", provenance="officiel", consultations=140),
    D("FORUM-A14", "Internal forum thread — A14 overheating tip",
      "A tip shared on the internal forum: for the overheating of press A14, "
      "some technicians short out the sensor. Unofficial.",
      dossier="/misc/forum/", date="2025-06-01", provenance="unverified web",
      consultations=30,
      corrections={"valide": True}),  # valid, but low authority and trust

    # ---- Thematic noise, so the retrieval has something to chew on ----------
    D("PROC-310", "PROC-310 — preventive maintenance of press A14",
      "Preventive maintenance procedure for press A14: greasing, checking the "
      "bearings, a six-monthly interval.",
      dossier="/maintenance/procedures/validees/", date="2026-02-01",
      statut="en vigueur", provenance="interne validee", consultations=85),
    D("PROC-205", "PROC-205 — overheating of motor M-7",
      "Procedure in the event of overheating of motor M-7: cut-off, thermal "
      "diagnosis. Does not apply to presses.",
      dossier="/maintenance/procedures/validees/", date="2025-12-05",
      statut="en vigueur", provenance="interne validee", consultations=50),
    D("RH-CONGES", "Agreement — paid leave",
      "The agreement on paid leave sets the arrangements for booking and "
      "carrying over leave days.",
      dossier="/hr/agreements/validees/", date="2026-01-15", statut="en vigueur",
      provenance="interne validee", consultations=110),
    D("RH-FAQ-CONGES", "FAQ — leave and time off",
      "FAQ on leave and time off in lieu: how many days, how to book them.",
      dossier="/hr/faq/", date="2025-08-01", provenance="interne",
      consultations=130),
    D("MANUEL-PRESSE", "Manufacturer manual — press A14",
      "The manufacturer's manual for press A14: technical characteristics, "
      "diagrams, nominal operating temperature ranges.",
      dossier="/maintenance/manuals/", date="2023-04-01",
      provenance="constructeur", consultations=45),
    D("PROC-448-v3", "PROC-448 v3 — overheating of press A14 (obsolete)",
      "The old overheating procedure for press A14, version 3. Kept for the "
      "historical record only.",
      dossier="/maintenance/procedures/archive/", date="2022-09-01",
      statut="obsolete", provenance="interne", remplace_par="PROC-448-v4",
      consultations=10),
]


# The ground truth: the document an EXPERT would choose, not the closest one.
#
# Five of the six are traps. Q6 is the control case, where the right document IS
# also the most similar: the calibration must not break it. Lab 36-1 reports
# recall@1 and MRR before and after; the French baseline is 33% -> 100% and
# 0.67 -> 1.00, with 2/6 correct becoming 6/6.
QUESTIONS = [
    {"id": "Q1",
     "question": "How many days of telework can an employee take per week?",
     "attendus": ["RH-ACCORD"],
     "piege": "The FAQ and the draft (three days) are more similar; the "
              "agreement in force (two days) governs."},
    {"id": "Q2",
     "question": "What is the procedure if press A14 overheats?",
     "attendus": ["PROC-448-v5"],
     "piege": "PROC-448 v4 (superseded) is near-identical; only v5 is in force."},
    {"id": "Q3",
     "question": "What safety precautions apply before working on a press?",
     "attendus": ["SEC-012"],
     "piege": "A binding regulatory document, to be preferred over forum tips."},
    {"id": "Q4",
     "question": "How can an overheating A14 press be cooled quickly?",
     "attendus": ["PROC-448-v5"],
     "piege": "The forum offers a similar-looking tip that is not reliable."},
    {"id": "Q5",
     "question": "How many days of paid leave can I book?",
     "attendus": ["RH-CONGES"],
     "piege": "The leave FAQ is more similar; the agreement governs."},
    {"id": "Q6",
     "question": "Preventive maintenance procedure for press A14?",
     "attendus": ["PROC-310"],
     "piege": "The control case: here the right document IS also the closest."},
]


def main():
    (CORPUS / "documents.json").write_text(
        json.dumps(DOCUMENTS, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "questions.json").write_text(
        json.dumps(QUESTIONS, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Chapter 36 corpus generated in:", CORPUS)
    print(f"  - documents.json : {len(DOCUMENTS)} documents (HR plus maintenance)")
    print(f"  - questions.json : {len(QUESTIONS)} questions "
          f"(5 of them traps, where the right doc is not the closest)")


if __name__ == "__main__":
    main()
