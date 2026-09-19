# -*- coding: utf-8 -*-
"""
Lab 32-2 — Calibrating uncertainty: saying "I am not sure" at the right moment
"A trust score that does not predict correctness is decoration"

A trust score is built from the available signals — retrieval, generation, number
of sources, contradiction, freshness — and then CALIBRATED against the ground
truth: does a score of 0.8 really mean 80% correct?

The Expected Calibration Error is measured, an abstention threshold is sought,
and the effect shown: what is served becomes reliable, at the price of coverage.

BASELINE (French edition, reproduced here): ECE before calibration 0.258; the
precision of the answers served rises to 100%, against 57% on the raw set.

No API key. Run generate_corpus.py first.
"""

from collections import Counter

from uxkit import (bandeau, etat_confiance, message_operationnel,
                  ece, calibrer_seuils, load_answers)


def main():
    bandeau("Lab 32-2 — Handling uncertainty, and calibrated trust")
    reponses = load_answers()

    # ---- 1) & 2) Classement in states + messages operationnels ----
    print("\n[1] SCORES -> STATE -> AN OPERATIONAL MESSAGE (no percentage)")
    print("─" * 74)
    etats = Counter()
    exemples = {}
    for r in reponses:
        etat = etat_confiance(r["score_retrieval"], r["score_generation"],
                              r["n_sources"], r["contradiction"])
        etats[etat] += 1
        msg = message_operationnel(etat, r["n_sources"], r["fraicheur"],
                                   r["contradiction"])
        exemples.setdefault(etat, (r, msg))

    for etat in ("elevee", "faible", "abstention"):
        r, msg = exemples[etat]
        couleur = {"vert": "[green] ", "orange": "[orange]", "rouge": "[red]   "}[msg["couleur"]]
        print(f"  {couleur} {etat.upper():<11} ({etats[etat]} answers)")
        print(f"     e.g. \"{r['question'][:48]}\"")
        print(f"     ton: {msg['ton_reponse']:<12} | {msg['message'][:60]}")
        if msg["bandeau"]:
            print(f"     banner: \"{msg['bandeau']}\"")
        print()

    print(f"  Split: high={etats['elevee']}  "
          f"faible={etats['faible']}  abstention={etats['abstention']}")

    # ---- 3) Calibration BEFORE ----
    print("\n[2] CALIBRATION — aligning perceived trust with real reliability")
    print("─" * 74)
    scores = [min(r["score_retrieval"], r["score_generation"]) for r in reponses]
    justes = [r["correcte"] for r in reponses]
    ece_avant = ece(scores, justes)
    print(f"  ECE before calibration: {ece_avant:.3f} "
          f"(0 = perfectly calibrated)")

    # Combien of answers FAUSSES seraient servies without abstention ?
    servies_naif = [r for r in reponses
                    if min(r['score_retrieval'], r['score_generation']) > 0.0]
    fausses_naif = sum(1 for r in servies_naif if not r["correcte"])
    print(f"  With no abstention threshold: {len(servies_naif)} answers served, "
          f"of which {fausses_naif} are wrong.")

    # ---- 4) Search of the threshold of abstention ----
    print("\n[3] THRESHOLD CALIBRATION")
    print("─" * 74)
    calib = calibrer_seuils(scores, justes)
    threshold = calib["threshold"]
    servies = [r for r in reponses
               if min(r['score_retrieval'], r['score_generation']) >= threshold]
    fausses = sum(1 for r in servies if not r["correcte"])
    print(f"  Recommended abstention threshold: {threshold:.2f}")
    print(f"  After calibration: {len(servies)} answers served, "
          f"of which {fausses} are wrong.")
    print(f"  Precision of the answers served: "
          f"{calib['precision_servie']:.0%} "
          f"(vs {sum(justes)/len(justes):.0%} on the raw set).")
    print(f"  -> Better to abstain {len(reponses)-len(servies)} times than to serve")
    print(f"     {fausses_naif - fausses} more false answers.")

    print("\n" + "═" * 74)
    print("THE MESSAGE: calibrated trust is worth more than displayed trust. You do")
    print("not say \"82% confidence\", which misleads, but \"official documentation,")
    print("consistent across 3 sources\". And you set the threshold so that what the")
    print("system DARES to assert is actually reliable — at the price of abstaining")
    print("and offering a human escalation on the grey areas.")


if __name__ == "__main__":
    main()
