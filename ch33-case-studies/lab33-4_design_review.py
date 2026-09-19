# -*- coding: utf-8 -*-
"""
Lab 33-4 — The design review
"Moving from script developer to ARCHITECT of trustworthy AI systems"

The aim: mark an architecture dossier against an explicit scheme — fit to the
specification, justification of the choices, security and governance, user
experience, evaluation strategy, clarity of the defence — and then set the jury's
mark against the objective score of the test bench.

The point: a jury can over-mark a brilliant presentation that is technically
unsuited, or under-mark a sober but correct solution. The test bench objectifies
the debate without replacing judgement.

This is the synthesis of the whole book: build, make reliable, deploy.

No API key. Run generate_corpus.py first.
"""

from archikit import (bandeau, grille_soutenance, evaluate,
                      load_architectures)
import archikit


# Simulated jury marks against the scheme, for two submitted dossiers.
NOTES_JURY = {
    "Banking (compliance)": {
        "Fit to the specification": 23,
        "Justification of the choices (cost/quality/latency)": 18,
        "Security and governance": 14,
        "User experience": 12,
        "Evaluation strategy": 13,
        "Clarity and oral defence": 9},
    "Minimal (low-cost)": {
        "Fit to the specification": 8,
        "Justification of the choices (cost/quality/latency)": 10,
        "Security and governance": 4,
        "User experience": 5,
        "Evaluation strategy": 6,
        "Clarity and oral defence": 7},
}


def main():
    bandeau("Lab 33-4 — Soutenance d'architecture")
    cahiers = archikit.CAHIERS
    archis = load_architectures()
    grille = grille_soutenance()

    # ---- 1) The grille of soutenance ----
    print("\n[1] THE MARKING SHEET (out of 100)")
    print("─" * 74)
    total = 0
    for c in grille:
        total += c["points"]
        print(f"  [{c['points']:>2} pts] {c['critere']}")
        print(f"           {c['question']}")
    print(f"  Total : {total} points")

    # ---- 2) & 3) Notation jury vs banc d'essai ----
    print("\n[2] NOTATION DU JURY vs SCORE OBJECTIF (banc d'essai)")
    print("─" * 74)
    cahier = cahiers["banque"]
    for nom in ("Banking (compliance)", "Minimal (low-cost)"):
        note_jury = sum(NOTES_JURY[nom].values())
        score_objectif = evaluate(archis[nom], cahier)["score_final"]
        ecart = round(note_jury - score_objectif, 1)
        print(f"  Submission \"{nom}\"")
        print(f"     Jury mark        : {note_jury}/100")
        print(f"     Test bench       : {score_objectif}/100 "
              f"(against the banking specification)")
        print(f"     Jury minus bench : {ecart:+.1f} "
              f"({'an indulgent jury' if ecart > 8 else 'a severe jury' if ecart < -8 else 'consistent'})")
        print()

    print("  Reading: a jury can over-mark a brilliant presentation that is")
    print("  technically unsuited, or under-mark a sober but correct solution.")
    print("  The test bench objectifies the debate — without replacing judgement.")

    # ---- 4) The completed marking sheet in detail (a solid submission) ----
    print("\n[3] THE COMPLETED SHEET — the \"Banking (compliance)\" submission")
    print("─" * 74)
    for c in grille:
        obtenu = NOTES_JURY["Banking (compliance)"][c["critere"]]
        barre = "▇" * round(obtenu / c["points"] * 10)
        print(f"  {c['critere'][:42]:<42} {obtenu:>2}/{c['points']:<2} {barre}")

    # ---- 5) Retour of experience ----
    print("\n[4] THE DEBRIEF (a summary sheet)")
    print("─" * 74)
    print("  Strengths: an architecture aligned with the specification;")
    print("             justified choices; security and UX handled.")
    print("  Limits   : the evaluation strategy can be improved (coverage of the")
    print("             failures); the cost of sovereignty needs objectifying.")
    print("  Next     : put a figure on the ROI; prepare an adversarial test plan;")
    print("            document the autonomy tiers (Chapter 31).")

    print("\n" + "═" * 74)
    print("THE MESSAGE: moving from script developer to ARCHITECT of trustworthy AI")
    print("systems. A good review defends its trade-offs, owns its limits, and")
    print("proves itself on a test bench — not only in the telling. This is the")
    print("synthesis of the whole book: build, make reliable, deploy.")


if __name__ == "__main__":
    main()
