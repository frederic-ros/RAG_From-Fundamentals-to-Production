# -*- coding: utf-8 -*-
"""
Lab 36-1 — Calibrate and measure
"annotate -> pre-annotate -> weighted retrieval -> measure"

This is THE demonstration lab of the book. It gathers the thesis of Part VII and
puts it to the test of a figure: a purely semantic retrieval (the "naive" one) is
compared with a retrieval weighted by the business calibration, on questions
where the two disagree — the FAQ against the agreement in force, the superseded
v4 procedure against the v5. The score that rises is the demonstration.

The lab is broken into steps, so every cog is visible:

    STEP A — deduce the calibration with NO model (the "free" part)
    STEP B — propose and validate the calibration (inferred, then the expert)
    STEP C — build the weighted score (the formula of Chapter 35)
    STEP D — rank: naive retrieval against calibrated retrieval

BASELINE (French edition, reproduced here): recall@1 rises from 33% to 100%, MRR
from about 0.5 to 1.00, and 2 of 6 correct top-1 answers become 6 of 6.

Five of the six questions are traps, where the right document is NOT the closest
match; the sixth is the control, where it is. The calibration must fix the five
without breaking the sixth.

No API key: TF-IDF embeddings (or sentence-transformers), pre-annotation by rules
(or Ollama).
"""

from calibkit import (Search, calibrate_corpus, deduire_calibration,
                     classer_nu, classer_calibre, score_pondere, Weights,
                     recall_at_k, mrr, load_documents, load_questions,
                     bandeau)


def etape_A(documents):
    print("\n" + "─" * 76)
    print("STEP A — Deduce the calibration with NO model (the automatic part)")
    print("─" * 76)
    print("Only signals ALREADY present are used: the filing folder,")
    print("date, workflow status, replacement links and consultation counts.\n")
    # Illustrated on two "trap" pairs.
    for did in ("RH-FAQ", "RH-ACCORD", "PROC-448-v4", "PROC-448-v5"):
        doc = next(d for d in documents if d["id"] == did)
        cal = deduire_calibration(doc)
        print(f"  {did:<12} {cal.as_dict()}")
        for k, v in cal.justifs.items():
            print(f"       · {k:<10}: {v}")
        print()
    print("READING: without a single hand annotation, the system already knows the FAQ")
    print("has low authority, that v4 is no longer in force (the 'superseded"
          " by' link),")
    print("and that v5 is official and critical. That is the thesis of Chapter 36:")
    print("a large part of the calibration is deduced, for free.")


def etape_B(documents):
    print("\n" + "─" * 76)
    print("STEP B — Propose, then validate (the inferred part, then the expert)")
    print("─" * 76)
    print("The LLM, if Ollama is connected, proposes adjustments to criticality and")
    print("authority; otherwise the deduction serves as the proposal. Finally,")
    print("TARGETED expert corrections are applied — the \"20% that commits you\".\n")
    cals = calibrate_corpus(documents)
    # Show a case where expert validation changes the proposed calibration.
    exemples = ("FORUM-A14", "PROC-448-v5", "RH-ACCORD")
    for did in exemples:
        print(f"  {did:<12} {cals[did].as_dict()}")
    print("\nREADING: the expert does not fill everything in. They guarantee the")
    print("commit the organisation: safety, the authority of a binding document.")
    return cals


def etape_C(documents, cals):
    print("\n" + "─" * 76)
    print("STEP C — The weighted score (the formula of Chapter 35)")
    print("─" * 76)
    print("Score = similarity, MODULATED by the calibration:")
    print("   sim x (1 + beta*criticality + gamma*confidence + delta*usage + 0.4*authority)")
    print("   minus a strong penalty if the document is NO LONGER in force.")
    print("The calibration does not REPLACE the similarity: it reorders the already")
    print("relevant documents, and sets aside those that are stale.\n")
    poids = Weights()
    print(f"  Weights : alpha={poids.alpha} (sim), beta={poids.beta} (crit), "
          f"gamma={poids.gamma} (conf), delta={poids.delta} (usage)")
    # A demonstration in figures on the v4 / v5 pair, for an overheating query.
    r = Search(documents)
    sims = r.similarites("overheating procedure press A14")
    idx = {d["id"]: i for i, d in enumerate(documents)}
    for did in ("PROC-448-v4", "PROC-448-v5"):
        i = idx[did]
        sc = score_pondere(float(sims[i]), cals[did], poids)
        print(f"  {did:<12} sim={sims[i]:.3f}  valide={cals[did].valide}"
              f"  ->  weighted score={sc:.3f}")
    print("\nREADING: v4 and v5 resemble each other enormously (close similarity).")
    print("The invalidity penalty drops v4 below v5: the system")
    print("finally makes an expert-like choice.")


def etape_DE(documents, cals):
    print("\n" + "─" * 76)
    print("STEPS D AND E — Rank (naive against calibrated), then measure the gain")
    print("─" * 76)
    questions = load_questions()
    r = Search(documents)
    poids = Weights()
    K = 3

    print(f"\n{'Q':<4}{'expected':<14}{'top-1 naive':<16}{'top-1 calibrated':<18}  trap")
    print("─" * 90)
    rec_nu, rec_cal, mrr_nu, mrr_cal = [], [], [], []
    for q in questions:
        sims = r.similarites(q["question"])
        nu = [d["id"] for d in classer_nu(documents, sims, K)]
        cal = [d["id"] for d in classer_calibre(documents, sims, cals, poids, K)]
        rec_nu.append(recall_at_k(nu, q["attendus"], 1))
        rec_cal.append(recall_at_k(cal, q["attendus"], 1))
        mrr_nu.append(mrr(nu, q["attendus"]))
        mrr_cal.append(mrr(cal, q["attendus"]))
        ok_nu = "ok " if nu[0] in q["attendus"] else "   "
        ok_cal = "ok " if cal[0] in q["attendus"] else "   "
        print(f"{q['id']:<4}{q['attendus'][0]:<14}{ok_nu+nu[0]:<16}"
              f"{ok_cal+cal[0]:<16}  {q['piege'][:34]}")
    print("─" * 90)

    moy = lambda xs: sum(xs) / len(xs)
    n = len(questions)
    print(f"\n{'':<22}{'NAIVE (sim only)':>18}{'CALIBRATED':>13}")
    print("─" * 50)
    print(f"{'recall@1':<22}{moy(rec_nu):>15.0%}{moy(rec_cal):>12.0%}")
    print(f"{'MRR':<22}{moy(mrr_nu):>16.2f}{moy(mrr_cal):>12.2f}")
    print(f"{'top-1 corrects':<22}{sum(rec_nu):>13.0f}/{n}{sum(rec_cal):>10.0f}/{n}")

    print("\n" + "═" * 76)
    print("THE MESSAGE: on the \"trap\" questions — those where the right document is")
    print("NOT the closest match — the naive retrieval gets it wrong (the FAQ instead of")
    print("agreement, a superseded procedure instead of the version in force). The")
    print("business calibration fixes them without breaking the easy cases. The")
    print("thesis of the book is no longer asserted: it is MEASURED. Retrieval,")
    print("which began as a comparison of words, has become a problem of")
    print("valeur documentaire.")


def main():
    bandeau("Lab 36-1 — Calibrating a corpus and measuring the gain "
            "(annotate -> weight -> measure)")
    documents = load_documents()
    etape_A(documents)
    cals = etape_B(documents)
    etape_C(documents, cals)
    etape_DE(documents, cals)


if __name__ == "__main__":
    main()
