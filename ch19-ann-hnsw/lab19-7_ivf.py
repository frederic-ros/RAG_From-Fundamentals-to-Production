# -*- coding: utf-8 -*-
"""
Lab 19-7 (BONUS) -- The other family: cluster-based search (IVF)

Learning objective
-------------------
HNSW is not the only way to avoid comparing a query to every vector. This lab
builds the second major family of ANN indexes: the Inverted File (IVF). The
idea is radically simpler than a navigable graph: partition the corpus into
clusters with k-means, then at query time compare the query only to the
cluster centroids (a handful of comparisons), and fully scan only the
`n_probe` closest clusters instead of the whole corpus.

No dogma between HNSW and IVF: this lab lets you read, on your own numbers,
where each one is strong -- and shows that IVF is not a competitor to the
quantization of Lab 19-6, but its natural partner (their combination, IVFADC,
is what most production vector databases actually run under the hood).

No API key. Reloads corpus_ref.npy.
Run first: python generate_corpus.py
"""

from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"


def main() -> None:
    print("=" * 78)
    print("Lab 19-7 (BONUS) -- The other family: cluster-based search (IVF)")
    print("=" * 78)

    f = DATA / "corpus_ref.npy"
    if not f.exists():
        print("\nDataset not found. Run first: python generate_corpus.py")
        return

    corpus = np.load(f)
    n, dim = corpus.shape

    # A common rule of thumb: about sqrt(n) clusters balances cluster size
    # against the number of centroids to compare at query time.
    n_clusters = max(4, int(round(np.sqrt(n))))
    print(f"\nCorpus: {n} vectors x {dim} dimensions.")
    print(f"Building the IVF index ({n_clusters} clusters, via k-means)...")
    index = A.IVFMini(corpus, n_clusters=n_clusters, seed=42)

    print("\n" + "=" * 78)
    print("1) THE PARTITION: how evenly did k-means split the corpus?")
    print("=" * 78)
    sizes = np.array(index.cluster_sizes())
    print(f"  Clusters: {index.n_clusters}  |  average size: {sizes.mean():.1f} "
          f"vectors  |  smallest: {sizes.min()}  |  largest: {sizes.max()}")
    print("  A very uneven partition is the classic IVF failure mode: a query")
    print("  routed to an oversized cluster scans almost the whole corpus anyway,")
    print("  while a near-empty cluster wastes a probe for nothing.")

    rng = np.random.default_rng(707)
    qids = rng.choice(n, 100, replace=False)
    requetes = corpus[qids] + rng.normal(0, 0.08, (100, dim))
    verites = [A.exact_search(corpus, q, k=10)[0] for q in requetes]

    print("\n" + "=" * 78)
    print("2) THE DIAL: n_probe (how many clusters to visit per query)")
    print("=" * 78)
    print("  Exactly like ef_search for HNSW, n_probe trades recall for speed --")
    print("  it is IVF's own tuning dial, not a competing idea.\n")

    probes = [1, 2, 4, 8, 16]
    print(f"  {'n_probe':>7s} | {'recall':>7s} | {'comparisons/query':>18s} | recall bar")
    print("  " + "-" * 66)

    points = []
    for np_ in probes:
        recalls, comps = [], []
        for q, ex in zip(requetes, verites):
            found, nc = index.search(q, k=10, n_probe=np_)
            recalls.append(A.recall(found, ex))
            comps.append(nc)
        r = float(np.mean(recalls))
        c = float(np.mean(comps))
        points.append((np_, r, c))
        bar = "#" * int(round(r * 40))
        print(f"  {np_:7d} | {r:6.1%} | {c:16.0f}   | {bar}")

    print("\n" + "=" * 78)
    print("3) IVF vs EXACT SEARCH vs HNSW: same goal, different mechanism")
    print("=" * 78)
    _, exact_comparisons = A.exact_search(corpus, requetes[0], k=10)
    hnsw_index = A.HNSWMini(corpus, M=16, ef_construction=100)
    hnsw_comps = []
    hnsw_recalls = []
    for q, ex in zip(requetes, verites):
        found, nc = hnsw_index.search_for(q, k=10, ef_search=40)
        hnsw_comps.append(nc)
        hnsw_recalls.append(A.recall(found, ex))
    ivf_at_90 = next((p for p in points if p[1] >= 0.90), points[-1])

    print(f"  Exact search      : {exact_comparisons:6d} comparisons/query  |  100.0% recall (the reference)")
    print(f"  HNSW (ef=40)      : {np.mean(hnsw_comps):6.0f} comparisons/query  |  {np.mean(hnsw_recalls):5.1%} recall")
    print(f"  IVF (n_probe={ivf_at_90[0]:<2d})  : {ivf_at_90[2]:6.0f} comparisons/query  |  {ivf_at_90[1]:5.1%} recall")
    print("\n  Both HNSW and IVF cut the comparisons by roughly the same order of")
    print("  magnitude versus exact search on this toy corpus. The difference is not")
    print("  in the destination, but in the road: HNSW pays a rich graph (several")
    print("  links per vector) to navigate directly toward the answer; IVF pays a")
    print("  much lighter structure (one centroid list per cluster) and accepts")
    print("  scanning whole clusters instead of single steps.")

    print("\n" + "=" * 78)
    print("WHAT THIS REVEALS")
    print("=" * 78)
    print("- IVF's structure is almost free to build and update: inserting a new")
    print("  vector means one centroid comparison and one append to a list -- no")
    print("  graph surgery, unlike HNSW. This is why IVF-based indexes are often")
    print("  preferred for corpora that change constantly.")
    print("- IVF's memory footprint is tiny: a few centroids plus flat lists of")
    print("  integers, versus HNSW's several links stored per vector.")
    print("- The price: IVF's recall/speed curve is typically less efficient per")
    print("  comparison than HNSW's in high dimensions -- reaching a given recall")
    print("  usually costs IVF more comparisons than it costs HNSW.")
    print("- The two are not rivals to pick between once and for all: IVF combined")
    print("  with the quantization of Lab 19-6 (compressing what sits *inside* each")
    print("  cluster) is exactly the IVFADC design behind most production vector")
    print("  databases -- coarse partition first, compression second.")

    print("\nKEY TAKEAWAYS")
    print("- IVF: partition with k-means, probe only the n_probe nearest clusters.")
    print("- n_probe is IVF's ef_search -- the same recall/speed dial, a different")
    print("  mechanism underneath.")
    print("- Cheap to build, cheap to update, lighter on memory than HNSW -- at the")
    print("  cost of a less favorable recall-per-comparison curve in general.")
    print("- References: Jegou, Douze & Schmid (2011), Product Quantization for")
    print("  Nearest Neighbor Search, IEEE TPAMI (introduces IVFADC, IVF + PQ).")


if __name__ == "__main__":
    main()
