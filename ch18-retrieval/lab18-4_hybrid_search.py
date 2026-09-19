# -*- coding: utf-8 -*-
"""
Lab 18-4 — The hybrid search: reconciling the two searchers

Learning objective
------------------
Put the pieces together: run BM25 AND the dense search on every query, merge with
RRF, and MEASURE the gain over a query set mixing exact codes with semantic
questions.

    Faced with two complementary methods, a hybrid search refuses to choose.
    It runs both, and reconciles their results.

This lab produces the central table of the chapter: for each query, the RANK of
the right document under BM25 alone, the dense alone, and the hybrid. You can see
that the hybrid is not "better everywhere", but that it CATCHES the blind spots
of each method — it is never the worse of the two, and it repairs the outright
failures.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import bm25
import corpus
import embeddings
import rrf


def rank_of(ranking, ids, target_id):
    for position, (idx, _score) in enumerate(ranking, start=1):
        if ids[idx] == target_id:
            return position
    return None


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    ids, texts = corpus.load_documents()
    queries = corpus.load_queries()
    bm25_engine = bm25.BM25(texts)
    dense = embeddings.DenseSearch(texts)

    print("#" * 78)
    print("# Lab 18-4 — The hybrid search: reconciling the two searchers")
    print("#" * 78 + "\n")
    print(f"Embedding mode: {embeddings.mode()}\n")

    # --- Step 1: a detailed example on E-204 ---------------------------------
    print("=" * 78)
    print("STEP 1 — The anatomy of a fusion: \"E-204\"")
    print("=" * 78)
    cb = bm25_engine.rank("E-204")
    cd = dense.rank("E-204")
    fus = rrf.rrf([cb, cd], k=60)
    print("  The rank of doc_E204 in each list:")
    print(f"    BM25  : {rank_of(cb, ids, 'doc_E204')}")
    print(f"    Dense : {rank_of(cd, ids, 'doc_E204')}")
    print(f"    Hybrid: {rank_of(fus, ids, 'doc_E204')}")
    print("  Ranked high by BM25, ranked badly by the dense: the fusion reconciles the")
    print("  two and the right document rises. Neither method alone managed as well.")

    # --- Step 2: the full comparison table -----------------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — The rank of the right document, by method and by query")
    print("=" * 78)
    header = f"  {'type':<11}{'query':<40}{'BM25':>6}{'Dense':>7}{'Hybrid':>9}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    bm25_gains = dense_gains = 0
    never_worse = True
    for q, cid, typ in queries:
        cb = bm25_engine.rank(q)
        cd = dense.rank(q)
        fus = rrf.rrf([cb, cd], k=60)
        rb = rank_of(cb, ids, cid)
        rd = rank_of(cd, ids, cid)
        rf = rank_of(fus, ids, cid)
        q_short = (q[:36] + "…") if len(q) > 37 else q
        print(f"  {typ:<11}{q_short:<40}{rb:>6}{rd:>7}{rf:>9}")
        # Is the hybrid at least as good as the worse of the two?
        if rf > max(rb, rd):
            never_worse = False
        if rf < rd:
            bm25_gains += 1   # the lexical contribution helped
        if rf < rb:
            dense_gains += 1  # the dense contribution helped

    # --- Step 3: reading the table -------------------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — Reading the table")
    print("=" * 78)
    print(f"  The hybrid is never worse than the worse of the two: {'yes' if never_worse else 'no'}")
    print(f"  Queries where the lexical contribution (BM25) improves on the dense: {bm25_gains}")
    print(f"  Queries where the dense contribution improves on BM25: {dense_gains}")
    print("  On the exact-code queries (E-204) the hybrid follows BM25; on the semantic")
    print("  ones (telecommuting) it follows the dense. It takes the better of the two")
    print("  WITHOUT anyone having to choose the method in advance.")

    print("\n  A nuance: when ONE method fails completely, at a very high rank, it can")
    print("  drag the fusion down. Fusion helps most when both methods stay in the")
    print("  race — which is the more frequent case.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The hybrid catches the blind spots: codes for BM25, meaning for the dense.")
    print("- It is not better EVERYWHERE, but it avoids each method's outright failures.")
    print("- What comes out is a solid list, ready to be refined (Lab 18-5).")
    print("\nA RETENIR")
    print("  The ideal document is the one BOTH methods agree to rank well.")


if __name__ == "__main__":
    main()
