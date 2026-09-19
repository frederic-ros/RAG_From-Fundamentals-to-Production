# -*- coding: utf-8 -*-
"""
Lab 19-2 — Finding the house without walking every street (the ANN idea)

Learning objective
------------------
How do you avoid walking through everything? The chapter answers with an image:
to reach a street at the far end of the country you do not travel every road —
you jump intelligently towards the right region, and then refine. Approximate
nearest neighbour search (ANN) does the same in vector space.

    ANN does not search everywhere, it searches WHERE to search.

This lab compares, on the SAME corpus and the SAME queries:

  - the EXACT search: how many distances does it compute? (all of them)
  - the GUIDED search (HNSW): how many does it compute? (a handful)

Both the saving in computation AND the quality preserved (the recall) are
measured. The message: a sliver of quality is given up for an enormous saving in
computation.

No API key. Reloads corpus_ref.npy.
Run generate_corpus.py first.
"""

from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"


def main() -> None:
    print("=" * 78)
    print("Lab 19-2 — Finding the house without walking every street")
    print("=" * 78)

    f = DATA / "corpus_ref.npy"
    if not f.exists():
        print("\nSet not found. Run this first: python generate_corpus.py")
        return

    corpus = np.load(f)
    n = corpus.shape[0]
    print(f"\nCorpus: {n} vectors of dimension {corpus.shape[1]}.")
    print("Building an HNSW index — the \"navigation system\"…")
    index = A.HNSWMini(corpus, M=16, ef_construction=100)
    print(f"Graph layers (from the dense bottom to the sparse top): "
          f"{index.layer_sizes()}")

    rng = np.random.default_rng(11)
    qids = rng.choice(n, 50, replace=False)
    queries = corpus[qids] + rng.normal(0, 0.08, (50, corpus.shape[1]))

    exact_dist = []
    guided_dist = []
    recalls = []
    for q in queries:
        ex, nd_ex = A.exact_search(corpus, q, k=10)
        ap, nd_ap = index.search_for(q, k=10, ef_search=80)
        exact_dist.append(nd_ex)
        guided_dist.append(nd_ap)
        recalls.append(A.recall(ap, ex))

    mean_ex = np.mean(exact_dist)
    mean_ap = np.mean(guided_dist)
    mean_recall = np.mean(recalls)

    print("\n" + "=" * 78)
    print("EXACT AGAINST GUIDED: HOW MANY DISTANCES COMPUTED?")
    print("=" * 78)
    print(f"  EXACT search : {mean_ex:6.0f} distances per query (it looks at EVERYTHING).")
    print(f"  GUIDED search: {mean_ap:6.0f} distances per query (a fraction of the corpus).")
    print(f"  Saving       : {(1 - mean_ap/mean_ex)*100:5.1f}% fewer computations.")
    print(f"  Factor       : about {mean_ex/mean_ap:.0f}x fewer distances.")

    print("\n" + "=" * 78)
    print("AND THE QUALITY? (the recall)")
    print("=" * 78)
    print(f"  Mean recall of the guided search: {mean_recall:.1%}")
    print(f"  -> On average it finds {mean_recall*10:.0f} of the 10 true nearest neighbours,")
    print("     while computing only a handful of distances.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The exact search visits EVERY point: certain, but that is the whole road network.")
    print("- The guided search jumps to the right region and explores one neighbourhood:")
    print("  a few hundred distances instead of several thousand.")
    print("- Almost nothing is lost in quality (recall stays high) for a massive saving.")
    print("- That is the whole art of ANN: not searching everywhere, but searching where.")

    print("\nWHAT TO REMEMBER")
    print("- Approximate search gives up perfect exactness for speed.")
    print("- The number of distances computed is the key indicator: it stays small.")
    print("- What remains is the STRUCTURE that makes this navigation possible: HNSW (Lab 19-3).")


if __name__ == "__main__":
    main()
