# -*- coding: utf-8 -*-
"""
Lab 18-2 — BM25, the literal searcher: symmetrical strengths and limits

Learning objective
------------------
Meet the chapter's other searcher: the LEXICAL search (BM25). Give it "E-204"
and it finds the documents holding exactly that run of characters. It understands
nothing about the subject, but it never misses an exact reference.

    BM25 finds WHAT IS WRITTEN.
    Embeddings find WHAT WAS MEANT.

This lab shows the strengths AND the limits of BM25, symmetrical with those of
the dense search:

  1. BM25 on "E-204": it ranks the right sheet first, where the dense failed;
  2. BM25 on "a motor that runs hot": it fails, because the right document speaks
     of "overheating" — no shared word — where the dense succeeds;
  3. the conclusion: strengths and weaknesses that are almost exactly
     COMPLEMENTARY.

BM25 is implemented by hand in bm25.py, with no dependency. In production you
would use rank_bm25, Elasticsearch or OpenSearch, with an identical interface
(see the note at the end of the lab).

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import bm25
import corpus
import embeddings


def rank_of(ranking, ids, target_id):
    for position, (idx, score) in enumerate(ranking, start=1):
        if ids[idx] == target_id:
            return position, score
    return None, None


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    ids, texts = corpus.load_documents()
    bm25_engine = bm25.BM25(texts)
    dense = embeddings.DenseSearch(texts)

    print("#" * 78)
    print("# Lab 18-2 — BM25, the literal searcher: symmetrical strengths and limits")
    print("#" * 78 + "\n")

    # --- Step 1: BM25 wins on the exact code ---------------------------------
    print("=" * 78)
    print("STEP 1 — BM25 on an exact code: \"E-204\"")
    print("=" * 78)
    cl_bm25 = bm25_engine.rank("E-204")
    print("The top 3 for BM25:")
    for position, (idx, score) in enumerate(cl_bm25[:3], start=1):
        mark = "  <-- THE RIGHT DOCUMENT" if ids[idx] == "doc_E204" else ""
        print(f"  {position}. {ids[idx]:<18} (score {score:.2f}){mark}")
    r_bm25, _ = rank_of(cl_bm25, ids, "doc_E204")
    r_dense, _ = rank_of(dense.rank("E-204"), ids, "doc_E204")
    print(f"\n  Rank of doc_E204 — BM25: {r_bm25}   |   Dense: {r_dense}")
    print("  Where the dense search blurred the codes, BM25 finds the EXACT \"E-204\".")

    # --- Step 2: BM25 fails on the synonyms ----------------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — BM25 on a reformulation: \"a motor that runs hot\"")
    print("=" * 78)
    query = "how to fix a motor that runs hot"
    cl_bm25b = bm25_engine.rank(query)
    print(f"Query: \"{query}\"  (the right document speaks of \"overheating\")\n")
    print("The top 3 for BM25:")
    for position, (idx, score) in enumerate(cl_bm25b[:3], start=1):
        mark = "  <-- THE RIGHT DOCUMENT" if ids[idx] == "doc_overheating" else ""
        print(f"  {position}. {ids[idx]:<18} (score {score:.2f}){mark}")
    r_bm25b, _ = rank_of(cl_bm25b, ids, "doc_overheating")
    r_denseb, _ = rank_of(dense.rank(query), ids, "doc_overheating")
    print(f"\n  Rank of doc_overheating — BM25: {r_bm25b}   |   Dense: {r_denseb}")
    print("  \"runs hot\" and \"overheating\" share no keyword: BM25 struggles, where")
    print("  the dense search, which grasps MEANING, finds the right sheet.")

    # --- Step 3: the complementarity -----------------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — Strengths that are almost exactly complementary")
    print("=" * 78)
    print(f"  {'Query':<38}{'BM25':>8}{'Dense':>8}")
    print("  " + "-" * 54)
    cases = [
        ("E-204", "doc_E204"),
        ("how to fix a motor that runs hot", "doc_overheating"),
        ("section 172 Companies Act", "doc_law"),
        ("company telecommuting policy", "doc_remote_work"),
    ]
    for q, cid in cases:
        rb, _ = rank_of(bm25_engine.rank(q), ids, cid)
        rd, _ = rank_of(dense.rank(q), ids, cid)
        print(f"  {q[:36]:<38}{str(rb):>8}{str(rd):>8}")
    print("\n  Where one puts the right answer far down, the other puts it on top —")
    print("  and the reverse. Neither is better in absolute terms.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- BM25 never misses an exact reference, but ignores synonyms.")
    print("- The dense search grasps synonyms, but blurs neighbouring codes.")
    print("- Their blind spots are OPPOSED: hence the idea of combining them (Labs 18-3, 18-4).")
    print("\nWHAT TO REMEMBER")
    print("  BM25 finds what is written; embeddings find what was meant.")
    print("\n  In production: replace bm25.py with rank_bm25 (the same 'rank / search_for'")
    print("  interface), or with Elasticsearch or OpenSearch. The principle does not change.")


if __name__ == "__main__":
    main()
