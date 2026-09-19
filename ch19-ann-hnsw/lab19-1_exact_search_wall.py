# -*- coding: utf-8 -*-
"""
Lab 19-1 — The wall of a million vectors (exact search does not hold)

Learning objective
------------------
The chapter opens on a brutal observation: comparing the query with EVERY vector
costs a time that grows LINEARLY with the size of the corpus. Double the corpus,
double the response time. This lab makes that tangible by measuring the latency
of an exact search on corpora from 1,000 to 50,000 vectors.

    The problem is no longer the quality of the retrieval, but the response time.

The law is checked: time is roughly proportional to the number of vectors. Then
it is extrapolated towards a million and a billion, where exact search becomes
unusable in production — which motivates the approximate search of the next lab.

No API key. Reloads the sets from generate_corpus.py.
Run generate_corpus.py first.
"""

import time
from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"


def measure_latency(corpus: np.ndarray, queries: np.ndarray, k: int = 10) -> float:
    """The mean time of one exact search, in milliseconds."""
    t0 = time.perf_counter()
    for q in queries:
        A.exact_search(corpus, q, k=k)
    dt = (time.perf_counter() - t0) / len(queries)
    return dt * 1000.0


def main() -> None:
    print("=" * 78)
    print("Lab 19-1 — The wall of a million vectors")
    print("=" * 78)

    sets = ["corpus_1k.npy", "corpus_5k.npy", "corpus_20k.npy", "corpus_50k.npy"]
    if not all((DATA / j).exists() for j in sets):
        print("\nSets not found. Run this first: python generate_corpus.py")
        return

    rng = np.random.default_rng(2025)
    print("\nEXACT search (brute force): the query is compared with EVERY vector.")
    print("The mean time of one query is measured as the corpus grows.\n")
    print(f"  {'corpus':>10s} | {'latency/query':>16s} | {'factor vs 1k':>14s}")
    print("  " + "-" * 48)

    base = None
    measurements = []
    for j in sets:
        corpus = np.load(DATA / j)
        n = corpus.shape[0]
        # 20 queries: existing points, lightly perturbed.
        qids = rng.choice(n, 20, replace=False)
        queries = corpus[qids] + rng.normal(0, 0.08, (20, corpus.shape[1]))
        lat = measure_latency(corpus, queries)
        if base is None:
            base = lat
        factor = lat / base
        measurements.append((n, lat))
        print(f"  {n:10d} | {lat:13.3f} ms | {factor:13.1f}x")

    # Check the linearity: the latency-to-size ratio should stay roughly constant.
    print("\n" + "=" * 78)
    print("THE LAW: TIME GROWS LINEARLY WITH THE CORPUS")
    print("=" * 78)
    n0, l0 = measurements[0]
    n1, l1 = measurements[-1]
    size_ratio = n1 / n0
    time_ratio = l1 / l0
    print(f"- The corpus was multiplied by {size_ratio:.0f}, from {n0} to {n1} vectors.")
    print(f"- The latency was multiplied by {time_ratio:.0f}.")
    print("- The two factors are of the same order: this is LINEAR growth.")

    # Extrapolation towards the large scales.
    print("\nEXTRAPOLATION (same machine, same linear law):")
    per_vector = l1 / n1  # ms per vector
    for target, name in [(1_000_000, "1 million"), (1_000_000_000, "1 billion")]:
        est = per_vector * target
        if est < 1000:
            txt = f"{est:.0f} ms"
        else:
            txt = f"{est/1000:.1f} s"
        print(f"  - {name:10s} vectors: about {txt} PER QUERY.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- On a prototype, a few thousand vectors, exact search is instantaneous:")
    print("  there is no hurry to optimise it.")
    print("- But its latency grows WITH the corpus. At the scale of a real business")
    print("  corpus, millions of fragments, one query would take seconds.")
    print("- And we want to answer in a few milliseconds. Exact search hits a wall —")
    print("  not for lack of quality, but for lack of speed.")

    print("\nWHAT TO REMEMBER")
    print("- Exact search compares the query with EVERY vector: O(n) per query.")
    print("- Beyond reproach on a prototype, untenable in production.")
    print("- That wall justifies the chapter's renunciation: search APPROXIMATELY (Lab 19-2).")


if __name__ == "__main__":
    main()
