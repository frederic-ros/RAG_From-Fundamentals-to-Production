# -*- coding: utf-8 -*-
"""
Lab 19-4 — The magic dial: recall against speed (setting ef_search)

Learning objective
------------------
HNSW is not magic: it offers a dial. The central knob is `ef_search` — how many
candidates are explored at query time. This lab turns it and traces the
recall-against-latency curve.

    No setting is perfect; everything is a trade-off.

ef_search is swept from small (fast, modest recall) to large (slow, high recall),
and two things are observed:

  - recall RISES with ef_search... and then SATURATES, with a diminishing
    marginal gain;
  - latency, measured in distances computed, rises steadily.

The teaching point: there is a "knee" beyond which you pay a great deal of
latency for very little recall. That is where you set the dial, according to the
business need.

No API key. Reloads corpus_ref.npy.
Run generate_corpus.py first.
"""

from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"


def main() -> None:
    print("=" * 78)
    print("Lab 19-4 — The magic dial : recall vs vitesse")
    print("=" * 78)

    f = DATA / "corpus_ref.npy"
    if not f.exists():
        print("\nJeu introuvable. Lancez d'abord : python generate_corpus.py")
        return

    corpus = np.load(f)
    n = corpus.shape[0]
    print(f"\nCorpus : {n} vectors. Construction de l'index HNSW (M=16)…")
    index = A.HNSWMini(corpus, M=16, ef_construction=100)

    rng = np.random.default_rng(404)
    qids = rng.choice(n, 100, replace=False)
    queries = corpus[qids] + rng.normal(0, 0.08, (100, corpus.shape[1]))

    # Truth of terrain (search exacte) a fois for toutes.
    truths = [A.exact_search(corpus, q, k=10)[0] for q in queries]

    efs = [5, 10, 20, 40, 80, 160]
    print("\nSweeping ef_search (the knob on the dial):\n")
    print(f"  {'ef_search':>9s} | {'recall':>7s} | {'distances/query':>15s} | recall curve")
    print("  " + "-" * 64)

    points = []
    for ef in efs:
        recalls = []
        dists = []
        for q, ex in zip(queries, truths):
            ap, nd = index.search_for(q, k=10, ef_search=ef)
            recalls.append(A.recall(ap, ex))
            dists.append(nd)
        r = float(np.mean(recalls))
        d = float(np.mean(dists))
        points.append((ef, r, d))
        bar = "#" * int(round(r * 40))
        print(f"  {ef:9d} | {r:6.1%} | {d:12.0f}   | {bar}")

    # Spot the "knee": where the recall gained per extra distance collapses.
    print("\n" + "=" * 78)
    print("READING THE CURVE: THE TRADE-OFF, WITH YOUR OWN EYES")
    print("=" * 78)
    for i in range(1, len(points)):
        ef0, r0, d0 = points[i - 1]
        ef1, r1, d1 = points[i]
        recall_gain = (r1 - r0) * 100
        dist_cost = d1 - d0
        yield_ = recall_gain / dist_cost if dist_cost else 0.0
        print(f"  ef {ef0:3d} -> {ef1:3d}: +{recall_gain:4.1f} pt of recall "
              f"for +{dist_cost:4.0f} distances  (yield {yield_:.3f} pt/dist)")

    print("\n  -> At first, each extra distance buys a lot of recall.")
    print("     Then the yield collapses: you pay dearly to scrape a few tenths of")
    print("     a point. That is the \"knee\" of the curve.")

    print("\n" + "=" * 78)
    print("CHOOSING AN OPERATING POINT (according to the business)")
    print("=" * 78)
    # Find the smallest ef reaching 90% recall or better.
    target = next((ef for ef, r, _ in points if r >= 0.90), points[-1][0])
    print("  - A real-time assistant (latency first): a low ef_search (5 to 20);")
    print("    slightly less recall is accepted in order to answer fast.")
    print("  - A regulatory or legal search (recall first): a high ef_search")
    print("    (80 to 160); more latency is accepted in order to miss nothing.")
    print(f"  - A balanced setting here: ef_search around {target}, the first to pass 90% recall.")

    print("\nWHAT TO REMEMBER")
    print("- ef_search raises recall AND latency: it is a slider, not a switch.")
    print("- Recall saturates: past the knee, the latency bought returns almost nothing.")
    print("- There is no best setting in the absolute — only the right one for YOUR case (Lab 19-5).")


if __name__ == "__main__":
    main()
