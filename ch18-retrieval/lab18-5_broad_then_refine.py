# -*- coding: utf-8 -*-
"""
Lab 18-5 — Retrieve broadly then refine, and the condition of diversity

Learning objective
------------------
Two ideas that structure all modern retrieval, made concrete here.

1) RETRIEVE BROADLY, THEN REFINE. The hybrid search gives a fast, approximate
   list, optimised for RECALL — missing nothing. A second, more expensive step
   re-examines those candidates one by one and reorders them, for PRECISION. That
   step, reranking, is the subject of Chapter 20; a minimal version is shown here
   to capture its spirit: "finding" and "sorting" are two distinct trades.

2) DIVERSITY IS THE CONDITION OF THE HYBRID. Fusion only helps if the methods are
   REALLY different. Merging two variants of BM25 brings almost nothing — they go
   wrong in the same places. The strength of the hybrid comes from the diversity
   of its searchers, not from their number. This lab measures it.

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


def simple_reranker(query: str, candidate_idx, texts):
    """A minimal reranker: reorder the candidates by their overlap of exact
    tokens with the query — a stand-in for the real reranker of Chapter 20.

    The point is not subtlety but the PRINCIPLE: a second pass, more attentive to
    the precise query, reorders the broad list retrieved upstream.
    """
    q_tokens = set(bm25.tokenize(query))
    scores = []
    for idx in candidate_idx:
        toks = set(bm25.tokenize(texts[idx]))
        overlap = len(q_tokens & toks)
        scores.append((idx, overlap))
    scores.sort(key=lambda t: t[1], reverse=True)
    return scores


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    ids, texts = corpus.load_documents()
    bm25_engine = bm25.BM25(texts)
    dense = embeddings.DenseSearch(texts)

    print("#" * 78)
    print("# Lab 18-5 — Retrieve broadly then refine, and the condition of diversity")
    print("#" * 78 + "\n")

    # --- Part A: retrieve broadly, then refine -------------------------------
    print("=" * 78)
    print("PART A — Retrieve broadly (hybrid), then refine (reranker)")
    print("=" * 78)
    query = "procedure fault E-204"
    cd = dense.rank(query)

    # 1) Retrieve broadly: the DENSE search brings back a wide pool of candidates
    #    (good recall), but ranks the exact code E-204 badly — its blind spot.
    N = 6
    candidates = [idx for idx, _ in cd[:N]]
    print(f"Query: \"{query}\"\n")
    print(f"1) RETRIEVE BROADLY — the top {N} of the dense search (good recall, rough order):")
    for position, idx in enumerate(candidates, start=1):
        mark = "  <-- doc_E204 (badly ranked: the dense blind spot)" if ids[idx] == "doc_E204" else ""
        print(f"    {position}. {ids[idx]:<18}{mark}")

    # 2) Refine: a reranker reorders those same candidates, for precision.
    reordered = simple_reranker(query, candidates, texts)
    print("\n2) REFINE — the reranker reorders those same candidates (precision):")
    for position, (idx, ov) in enumerate(reordered, start=1):
        mark = "  <-- doc_E204" if ids[idx] == "doc_E204" else ""
        print(f"    {position}. {ids[idx]:<18} (overlap {ov}){mark}")

    r_before = rank_of([(i, 0) for i in candidates], ids, "doc_E204")
    r_after = rank_of([(i, 0) for i, _ in reordered], ids, "doc_E204")
    print(f"\n  Rank of doc_E204 — after retrieval: {r_before}  ->  after reranking: {r_after}")
    print("  \"Retrieving\" optimises recall; \"refining\" optimises precision.")
    print("  They are two distinct trades, and two distinct storeys of the pipeline.")

    # --- Part B: diversity is what makes the hybrid strong -------------------
    print("\n" + "=" * 78)
    print("PART B — Diversity is what makes the hybrid strong")
    print("=" * 78)
    print("Two fusions are compared over the whole query set:")
    print("  (1) BM25 + Dense         -> two DIFFERENT searchers")
    print("  (2) BM25 + a BM25 variant -> two SIMILAR searchers (different k1 and b)\n")

    bm25_variant = bm25.BM25(texts, k1=2.0, b=0.5)  # the same lexical biases

    sum_diverse = sum_redundant = 0
    n = 0
    for q, cid, _typ in corpus.load_queries():
        cb = bm25_engine.rank(q)
        cd = dense.rank(q)
        cbv = bm25_variant.rank(q)
        fus_diverse = rrf.rrf([cb, cd], k=60)       # diversity
        fus_redundant = rrf.rrf([cb, cbv], k=60)    # redundancy
        r_div = rank_of(fus_diverse, ids, cid)
        r_red = rank_of(fus_redundant, ids, cid)
        sum_diverse += r_div
        sum_redundant += r_red
        n += 1

    print(f"  {'Fusion':<32}{'mean rank of the right doc':>26}")
    print("  " + "-" * 58)
    print(f"  {'BM25 + Dense (diversity)':<32}{sum_diverse / n:>26.2f}")
    print(f"  {'BM25 + BM25 variant (redundant)':<32}{sum_redundant / n:>26.2f}")
    print("\n  Merging two BM25s merely copies the same mistakes: the mean rank stays")
    print("  close to BM25 alone. Merging BM25 with the dense, whose blind spots are")
    print("  OPPOSED, improves the mean rank clearly. Diversity, not number.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Modern retrieval has two storeys: retrieve broadly (recall), refine (precision).")
    print("- Reranking (Chapter 20) is that second pass, one of the most profitable there is.")
    print("- The hybrid is only worth anything through the DIVERSITY of the searchers combined.")
    print("\nWHAT TO REMEMBER")
    print("  Reordering a list by a criterion is already a step away from pure resemblance")
    print("  — the first step towards the weighted score of business calibration.")


if __name__ == "__main__":
    main()
