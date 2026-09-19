# -*- coding: utf-8 -*-
"""
Lab 29-7 — A complete benchmark of RAG configurations

Four configurations are measured on the same golden set (recall@k, MRR,
fidelity, abstention, attribution), producing a dashboard that says, in figures,
what each setting buys and what it costs.

    k=1 (minimal)      : cheap, but misses the multi-hop case.
    k=3 (reference)    : the usual compromise.
    k=5 (wide)         : maximises recall, costs more, brings noise.
    k=3 + abstention   : protects against the out-of-corpus question.

THE ABSTENTION THRESHOLD (0.30) IS CALIBRATED against the score distribution of
the corpus. It must fire on G09 — the one question with no answer — and on
nothing else. When this chapter was translated, an English wording of G09 scored
0.396, above the threshold: the out-of-corpus case sailed through while a
legitimate case abstained in its place. The lab still ran, and the dashboard
still looked reasonable. Check the abstention rate: it should be 8%, one case in
twelve, and that case should be G09.

No API key. Run generate_corpus.py first.
"""

from evalkit import (RAGPipeline, load_fragments, load_golden,
                     recall_at_k, mrr, juge_fidelite, taux_abstention,
                     taux_attribution, bandeau)


def evaluate_config(nom, docs, golden, k, threshold):
    pipe = RAGPipeline(docs, k=k, seuil_abstention=threshold)
    recs_m, mrr_m, fid_m, reponses = [], [], [], []
    for g in golden:
        rep = pipe.repondre(g["question"])
        reponses.append(rep)
        recs = [f["id"] for f in pipe.rech.chercher(g["question"], k=5)]
        if g["category"] != "out_of_corpus":
            recs_m.append(recall_at_k(recs, g["expected_fragments"], k))
            mrr_m.append(mrr(recs, g["expected_fragments"]))
        if not rep.abstention:
            ctx = " ".join(f["texte"] for f in rep.fragments)
            fid_m.append(juge_fidelite(rep.reponse, ctx))
    moy = lambda xs: sum(xs) / len(xs) if xs else 0.0
    return {
        "nom": nom,
        "recall": moy(recs_m),
        "mrr": moy(mrr_m),
        "fidelite": moy(fid_m),
        "abstention": taux_abstention(reponses),
        "attribution": taux_attribution(reponses),
    }


def main():
    bandeau("Lab 29-7 — Benchmark complet de configurations RAG")
    docs = load_fragments()
    golden = load_golden()

    configs = [
        ("k=1 (minimal)",        1, 0.0),
        ("k=3 (reference)",      3, 0.0),
        ("k=5 (wide)",          5, 0.0),
        ("k=3 + abstention",     3, 0.30),
    ]
    resultats = [evaluate_config(n, docs, golden, k, s) for n, k, s in configs]

    print(f"\n{'configuration':<20}{'recall@k':>10}{'MRR':>7}{'fidel.':>8}"
          f"{'abst.':>7}{'attrib.':>9}")
    print("─" * 61)
    for r in resultats:
        print(f"{r['nom']:<20}{r['recall']:>10.2f}{r['mrr']:>7.2f}"
              f"{r['fidelite']:>8.2f}{r['abstention']:>7.0%}{r['attribution']:>9.0%}")
    print("─" * 61)

    # === recommandation selon the criterion prioritaire ====================
    best_recall = max(resultats, key=lambda r: r["recall"])
    # NOTE: "maximum reliability" is NOT selected by a plain
    # max(fidelity, -abstention). Fidelity is measured only on the questions the
    # pipeline agreed to answer, so a naive max() would wrongly reward the
    # configuration that abstains
    # never (abstention=0), the opposite of the chapter's message. The config
    # the cautious one is the only one that abstains on the out-of-corpus case,
    # and it is the one that really protects the reliability the user perceives.
    prudent = next(r for r in resultats if "abstention" in r["nom"])

    print("\nRECOMMENDATION BY PRIORITY CRITERION:")
    print(f"  - maximum coverage     → {best_recall['nom']} "
          f"(recall {best_recall['recall']:.2f})")
    print(f"  - maximum reliability    → {prudent['nom']} "
          f"(abstention {prudent['abstention']:.0%}, protects against the out-of-corpus)")
    print("  - production trade-off  -> k=3 (reference): good recall without the cost")
    print("    de k=5 ni la perte de couverture de l'abstention agressive.")

    print("\n" + "═" * 61)
    print("THE MESSAGE: there is no \"best\" configuration in the absolute.")
    print("THE MESSAGE: there is no \"best\" configuration in the absolute. The")
    print("benchmark does not name a winner: it makes the trade-off EXPLICIT.")
    print("k=5 maximises recall but costs more and brings noise; abstention")
    print("protects but reduces coverage. To choose is to name your priority")
    print("criterion, and the cost of an error decides it.")


if __name__ == "__main__":
    main()
