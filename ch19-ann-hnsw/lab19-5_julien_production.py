# -*- coding: utf-8 -*-
"""
Lab 19-5 — Julien goes into production (choosing a realistic strategy)

Learning objective
------------------
The setting is not decided in the abstract, but according to BUSINESS
CONSTRAINTS. This lab stages two of the running profiles and compares three
strategies on the same corpus:

  - exact search: perfect recall, prohibitive latency;
  - aggressive ANN: very fast, recall a little lower (low ef_search);
  - balanced ANN: good recall, controlled latency (medium ef_search).

    The best system is the one that answers fast while staying useful.

Julien (maintenance) wants RESPONSIVENESS: about 90% recall is enough if the
answer arrives quickly. Sophie (regulatory) wants RECALL: missing nothing comes
first, even at the price of latency. The lab shows that one corpus calls for two
different settings — and that the "right" answer depends on the business
question.

No API key. Reloads corpus_ref.npy.
Run generate_corpus.py first.
"""

import time
from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"


def evaluate_strategy(index, corpus, queries, truths, ef):
    """Mean recall and mean distances for a given ef setting."""
    recalls, dists = [], []
    for q, ex in zip(queries, truths):
        ap, nd = index.search_for(q, k=10, ef_search=ef)
        recalls.append(A.recall(ap, ex))
        dists.append(nd)
    return float(np.mean(recalls)), float(np.mean(dists))


def main() -> None:
    print("=" * 78)
    print("Lab 19-5 — Julien goes into production")
    print("=" * 78)

    f = DATA / "corpus_ref.npy"
    if not f.exists():
        print("\nSet not found. Run this first: python generate_corpus.py")
        return

    corpus = np.load(f)
    n = corpus.shape[0]
    print(f"\nA simulated production corpus: {n} vectors.")
    index = A.HNSWMini(corpus, M=16, ef_construction=100)

    rng = np.random.default_rng(505)
    qids = rng.choice(n, 100, replace=False)
    queries = corpus[qids] + rng.normal(0, 0.08, (100, corpus.shape[1]))
    truths = [A.exact_search(corpus, q, k=10)[0] for q in queries]

    # Latency exacte of reference (temps real, for donner a ordre of largeur).
    t0 = time.perf_counter()
    for q in queries:
        A.exact_search(corpus, q, k=10)
    exact_latency_ms = (time.perf_counter() - t0) / len(queries) * 1000

    print("\n" + "=" * 78)
    print("THREE STRATEGIES ON THE SAME CORPUS")
    print("=" * 78)
    print(f"  {'strategy':<22s} | {'recall':>7s} | {'distances/query':>15s} | {'vs exact':>10s}")
    print("  " + "-" * 64)

    # Exacte.
    print(f"  {'Exact (reference)':<22s} | {1.0:6.1%} | {float(n):12.0f}   | {'1.0x':>10s}")

    # Aggressive ANN (low ef) and balanced ANN (medium ef).
    r_ag, d_ag = evaluate_strategy(index, corpus, queries, truths, ef=10)
    r_eq, d_eq = evaluate_strategy(index, corpus, queries, truths, ef=80)
    print(f"  {'Aggressive ANN (ef=10)':<22s} | {r_ag:6.1%} | {d_ag:12.0f}   | "
          f"{n/d_ag:8.0f}x")
    print(f"  {'Balanced ANN (ef=80)':<22s} | {r_eq:6.1%} | {d_eq:12.0f}   | "
          f"{n/d_eq:8.0f}x")

    print(f"\n  (Measured latency of the exact search here: {exact_latency_ms:.3f} ms/query;")
    print("   it would grow linearly with the corpus — see Lab 19-1.)")

    # --- The deux profils business -------------------------------------------
    print("\n" + "=" * 78)
    print("THE SAME CORPUS, TWO OPPOSED BUSINESS NEEDS")
    print("=" * 78)

    print("\n  JULIEN (maintenance) — a workshop assistant, responsiveness comes first.")
    print("    Constraint: a near-instant answer; 90% recall or better is enough.")
    print(f"    Choice    : aggressive or balanced ANN. At ef=80, recall {r_eq:.0%} for")
    print(f"                only {d_eq:.0f} distances (about {n/d_eq:.0f}x fewer than exact).")
    print("    Verdict   : responsiveness wins; rarely missing a neighbour is accepted.")

    print("\n  SOPHIE (regulatory) — missing NOTHING is vital.")
    print("    Constraint: the highest recall possible; latency is acceptable.")
    print("    Choice    : a high ef_search, plus the metadata filtering of Chapter 15,")
    print("                to search only the texts IN FORCE.")
    print("    Verdict   : latency is paid for safety; and a repealed text discarded")
    print("                upstream lightens the search into the bargain.")

    # An illustration of filtering: restrict to an "in force" subset.
    print("\n" + "=" * 78)
    print("A NOTE — FILTER THEN SEARCH (the link with Chapter 15)")
    print("=" * 78)
    # Simulate metadata: 60% of the fragments are "in force".
    status = rng.random(n) < 0.6
    subset = np.where(status)[0]
    print(f"  Of {n} fragments, {len(subset)} are marked \"in force\".")
    print("  Filtering BEFORE the search reduces the space explored to that subset:")
    print("  the search becomes more correct (no repealed text on top) and lighter.")
    print("  In practice, at scale, this filter is folded into the index traversal")
    print("  (see the \"filter and search\" box in the chapter).")

    print("\nWHAT TO REMEMBER")
    print("- Three strategies, one corpus: the choice depends on constraints, not an ideal.")
    print("- Julien optimises latency; Sophie optimises recall. Opposed settings, both legitimate.")
    print("- The best system is the one that answers fast WHILE staying useful for ITS use.")


if __name__ == "__main__":
    main()
