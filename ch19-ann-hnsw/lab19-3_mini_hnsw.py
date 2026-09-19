# -*- coding: utf-8 -*-
"""
Lab 19-3 — Building a mini-HNSW by hand (the layers and the navigation)

Learning objective
------------------
HNSW is not magic: it is a navigation system. This lab lifts the bonnet. A small
HNSW graph is built, and three things are OBSERVED:

  1. the pyramid of layers: dense at the bottom (the streets), sparse at the top
     (the motorways);
  2. the ROUTE of a query: you enter at the top, descend layer by layer, and
     visit only a handful of nodes;
  3. the number of HOPS needed to reach the target, set against the number of
     comparisons an exhaustive search would make.

    HNSW is a navigation system, not algorithmic magic.

The descent is instrumented to show, at each layer, the entry node and the node
reached — the concrete trace of "long hops first, small steps after".

No API key. Builds a small corpus in memory; generate_corpus is not needed.
"""



import numpy as np

import annlib as A


def main() -> None:
    print("=" * 78)
    print("Lab 19-3 — Building a mini-HNSW by hand")
    print("=" * 78)

    # A small corpus of 300 vectors: enough for several layers, small enough to read.
    corpus = A.generate_corpus(300, dim=16, n_clusters=6, seed=5)
    n = corpus.shape[0]
    print(f"\nToy corpus: {n} vectors of dimension {corpus.shape[1]}.")

    index = A.HNSWMini(corpus, M=8, ef_construction=40, seed=5)
    sizes = index.layer_sizes()

    print("\n" + "=" * 78)
    print("1) THE PYRAMID OF LAYERS")
    print("=" * 78)
    print("From the top (motorways, few nodes) to the bottom (streets, every node):\n")
    for level in range(len(sizes) - 1, -1, -1):
        t = sizes[level]
        bar = "#" * max(1, int(40 * t / max(sizes)))
        role = "motorway (long links)" if level == len(sizes) - 1 else (
               "local streets (short links, dense)" if level == 0 else "main roads")
        print(f"  layer {level} | {t:4d} nodes {bar}")
        print(f"          | {role}")
    print("\n-> The great majority of nodes live only in layer 0. A few climb one")
    print("   storey; very few reach the top. It is that scarcity at the top that")
    print("   makes the long hops possible.")

    # --- The instrumented route of a query ------------------------------------
    print("\n" + "=" * 78)
    print("2) THE ROUTE OF A QUERY: FROM THE MOTORWAY TO THE STREETS")
    print("=" * 78)
    rng = np.random.default_rng(3)
    # A query is chosen DELIBERATELY far from the entry point, so that the descent
    # makes real hops from one node to another. Otherwise the navigation is
    # trivial and illustrates nothing.
    entry_vec = corpus[index.entry]
    entry_sims = corpus @ entry_vec
    # A point among those furthest from the entry point.
    far = int(np.argsort(entry_sims)[:30][rng.integers(0, 30)])
    q = A.normalize(corpus[far] + rng.normal(0, 0.05, 16))
    print(f"\n  A query near node {far}, chosen far from the entry point.")

    # The descent is replayed "by hand", to trace the path.
    index.last_distances = 0
    ep = [index.entry]
    print(f"\n  Graph entry: node {index.entry} (the top of the pyramid)")
    for level in range(index.max_level, 0, -1):
        res = index._search_layer(q, ep, ef=1, level=level)
        reached = res[0][1] if res else ep[0]
        print(f"  layer {level}: node {ep[0]:3d} --hop--> node {reached:3d}  "
              f"(closing in on the query)")
        ep = [reached]
    res = index._search_layer(q, ep, ef=40, level=0)
    final = [idx for _, idx in res[:5]]
    print(f"  layer 0: fine exploration around node {ep[0]} "
          f"-> top 5 neighbours {final}")

    hops = index.max_level  # the number of storey descents
    distances = index.last_distances

    print("\n" + "=" * 78)
    print("3) HOPS AGAINST EXHAUSTIVE COMPARISONS")
    print("=" * 78)
    print(f"  Storey descents (long hops)        : {hops}")
    print(f"  Distances computed in total        : {distances}")
    print(f"  An exhaustive search would compute : {n} distances")
    print(f"  -> {distances} against {n}: we navigated, we did not sweep.")

    # Check the accuracy.
    ex, _ = A.exact_search(corpus, q, k=5)
    rec = A.recall(final, ex)
    print(f"\n  Quality: {rec:.0%} of the 5 true neighbours found by this navigation.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The graph is a PYRAMID: sparse at the top, dense at the bottom.")
    print("- You enter at the summit and descend: long hops first (the rough")
    print("  approach), small steps after (the fine tuning) — exactly the image of")
    print("  motorways and then streets from the chapter.")
    print("- The number of nodes visited stays small against the size of the corpus.")

    print("\nWHAT TO REMEMBER")
    print("- HNSW is layers plus a greedy navigation from the top down.")
    print("- The query is not compared with every vector: we navigate TOWARDS it.")
    print("- What remains is setting the exploration width: the recall-latency trade-off (Lab 19-4).")


if __name__ == "__main__":
    main()
