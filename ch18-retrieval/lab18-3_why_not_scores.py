# -*- coding: utf-8 -*-
"""
Lab 18-3 — Why scores cannot be added: rank fusion (RRF)

Learning objective
------------------
To combine BM25 with the dense search, the naive idea would be to add their
scores. A bad idea: those scores do not live in the same world. A BM25 score has
no bound (12, 18, 30...); a cosine similarity lives between 0 and 1. Adding them
is adding kilometres to degrees — the result always leans towards whichever scale
is wider.

The good solution sidesteps the problem: IGNORE the scores, keep only the RANKS.
That is Reciprocal Rank Fusion:

    RRF(d) = sum over the methods of 1 / (k + rank(d))    (k around 60)

This lab shows:

  1. the absurdity of adding scores, with their incomparable scales;
  2. the detailed RRF calculation on an example (the chapter's exercise);
  3. the effect of the constant k.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import bm25
import corpus
import embeddings
import rrf


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    ids, texts = corpus.load_documents()
    bm25_engine = bm25.BM25(texts)
    dense = embeddings.DenseSearch(texts)

    print("#" * 78)
    print("# Lab 18-3 — Why not the scores: rank fusion (RRF)")
    print("#" * 78 + "\n")

    # --- Step 1: incomparable scales -----------------------------------------
    print("=" * 78)
    print("STEP 1 — The scores do not live in the same world")
    print("=" * 78)
    query = "how to fix a motor that runs hot"
    cl_b = bm25_engine.rank(query)
    cl_d = dense.rank(query)
    print(f"Query: \"{query}\"\n")
    print("  The best BM25 scores (unbounded):")
    for idx, score in cl_b[:3]:
        print(f"    {ids[idx]:<18} {score:7.2f}")
    print("  The best dense scores (between 0 and 1):")
    for idx, score in cl_d[:3]:
        print(f"    {ids[idx]:<18} {score:7.3f}")
    print("\n  Add those scores? BM25 — up to about 3 here, but unbounded in general —")
    print("  would mechanically crush the similarity, capped at 1. The sum would no")
    print("  longer measure relevance, but the wider of the two scales.")

    # --- Step 2: RRF in detail, on an example --------------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — Rank fusion, step by step")
    print("=" * 78)
    print("  The chapter's example: a document ranked 2nd by BM25 and 5th by the dense.")
    k = 60
    c2 = rrf.contribution(2, k)
    c5 = rrf.contribution(5, k)
    print(f"    BM25 contribution (rank 2)  = 1/(60+2) = {c2:.4f}")
    print(f"    dense contribution (rank 5) = 1/(60+5) = {c5:.4f}")
    print(f"    RRF total = {c2 + c5:.4f}")
    print("\n  A second document: 1st for BM25, ABSENT from the dense list.")
    c1 = rrf.contribution(1, k)
    print(f"    RRF total = 1/(60+1) = {c1:.4f}")
    print(f"\n  Which ranks higher? The first ({c2 + c5:.4f}) beats the second")
    print(f"  ({c1:.4f}): fusion REWARDS agreement between methods, even without")
    print("  being first anywhere. Being well ranked by SEVERAL wins out.")

    # --- Step 3: the effect of k ---------------------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — The effect of the constant k")
    print("=" * 78)
    print(f"  {'k':>5}{'1st place':>12}{'10th place':>12}{'gap 1st/10th':>16}")
    for k in (10, 20, 60, 100):
        c1 = rrf.contribution(1, k)
        c10 = rrf.contribution(10, k)
        gap = (c1 - c10) / c10 * 100
        print(f"  {k:>5}{c1:>12.4f}{c10:>12.4f}{gap:>14.0f} %")
    print("\n  The larger k is, the flatter the curve: at k=60, first place is worth")
    print("  only about 15% more than tenth. That SMOOTHS the influence of an extreme")
    print("  ranking by a single method. The optimum is flat, anywhere from 20 to 100.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Adding scores from different scales is meaningless.")
    print("- RRF does not ask \"how much?\" but \"in what place?\".")
    print("- k is a robust setting, around 60, not a magic number.")
    print("\nWHAT TO REMEMBER")
    print("  Rank fusion reconciles two incomparable methods by bringing them back to")
    print("  the one thing they have in common: an ORDER.")


if __name__ == "__main__":
    main()
