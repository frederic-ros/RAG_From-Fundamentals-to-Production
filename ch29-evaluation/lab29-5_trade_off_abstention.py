# -*- coding: utf-8 -*-
"""
Lab 29-5 — The coverage/reliability trade-off (the abstention rate)
"Abstaining is not a hole in the coverage: it is a guardrail"

The aim: show concretely the central trade-off of any critical system. By
varying the pipeline's abstention threshold, the slider moves between COVERAGE
(answering often) and RELIABILITY (answering only when you know). The curve is
traced, and the point where abstention means safety is identified.

The steps: run the golden set at several abstention thresholds; measure the
coverage (the share of questions answered) and the reliability (mean fidelity ON
the answers given); then check that the system does abstain on the out-of-corpus
question, G09.

At a threshold of 0, coverage is maximal but the system answers even the
out-of-corpus question, which is the risk. As the threshold rises, coverage
falls, reliability rises, and G09 tips into abstention.

No API key. Run generate_corpus.py first.
"""

from evalkit import (RAGPipeline, load_fragments, load_golden,
                     juge_fidelite, taux_abstention, bandeau)


def evaluate(threshold, docs, golden):
    pipe = RAGPipeline(docs, k=3, seuil_abstention=threshold)
    reponses, fids = [], []
    g09_abst = None
    for g in golden:
        rep = pipe.repondre(g["question"])
        reponses.append(rep)
        if not rep.abstention:
            ctx = " ".join(f["texte"] for f in rep.fragments)
            fids.append(juge_fidelite(rep.reponse, ctx))
        if g["id"] == "G09":
            g09_abst = rep.abstention
    couverture = sum(1 for r in reponses if not r.abstention) / len(reponses)
    fiabilite = sum(fids) / len(fids) if fids else 0.0
    return couverture, fiabilite, taux_abstention(reponses), g09_abst


def main():
    bandeau("Lab 29-5 — The coverage/reliability trade-off (abstention)")
    docs = load_fragments()
    golden = load_golden()

    print(f"\n{'thresh.':>8}{'coverage':>12}{'reliability':>13}"
          f"{'abstention':>13}  G09 hors-corpus")
    print("─" * 64)
    for threshold in [0.0, 0.15, 0.25, 0.30, 0.37, 0.45]:
        couv, fia, abst, g09 = evaluate(threshold, docs, golden)
        etat = "abstains" if g09 else "answers"
        # small barre visuelle of the couverture
        barre = "█" * int(couv * 20)
        print(f"{threshold:>7.2f}{couv:>12.0%}{fia:>12.0%}{abst:>12.0%}   {etat}  {barre}")

    print("─" * 64)
    print("\nREADING: at a threshold of 0 the system answers EVERYTHING, including")
    print("out-of-corpus question (G09), at the risk of inventing. By raising the")
    print("threshold it begins to abstain: coverage falls, the reliability of the")
    print("answers GIVEN stays high, and G09 finally tips towards the right")
    print("behaviour — \"I do not know\".")
    print("\nBUT watch the PRICE: to make G09 abstain (threshold 0.37), you")
    print("sacrifice two thirds of the coverage. That is the limit of a single")
    print("on the RAW SCORE: vector retrieval gives non-zero scores")
    print("READING: at a threshold of 0 the system answers EVERYTHING, including")
    print("the out-of-corpus question. As the threshold rises it begins to")
    print("abstain: coverage falls, the fidelity of the answers GIVEN stays high,")
    print("and G09 finally tips towards the right behaviour — \"I do not know\".")

    print("\n" + "═" * 64)
    print("THE MESSAGE: in a critical system, a RAG that answers less but knows")
    print("its limits is worth more than a RAG that always answers. Abstention is")
    print("not a failure to be corrected: it is a safety characteristic to be")
    print("MEASURED and valued. The right threshold depends on the cost of an")
    print("error — high in industrial maintenance, so the threshold stays cautious.")


if __name__ == "__main__":
    main()
