# -*- coding: utf-8 -*-
"""
Lab 18-1 — The blind spot of dense search: exact codes (Julien)

Learning objective
------------------
Reproduce the chapter's blind spot. Dense search excels at grasping what the user
MEANS; it is almost blind to what they WRITE EXACTLY: codes, references,
acronyms, proper nouns.

    The query: "E-204"

A code like "E-204" has almost no MEANING in the vector sense: an embedding
captures significance, and "E-204" signifies nothing — it is a label. Two
neighbouring codes, "E-204" and "E-205", are near-identical to the model, while
they denote two unrelated failures. The result: dense search can rank the wrong
sheet ahead of the right one.

This lab shows:

  1. the dense search on "E-204" — and the right document NOT coming out on top;
  2. the confusion between neighbouring codes (E-204, E-205, E-311);
  3. the announcement of the remedy: a LITERAL searcher (BM25, Lab 18-2).

A note: in TF-IDF mode, offline, the fallback faithfully simulates this blind
spot by folding codes onto a generic family token (see embeddings.py). With real
dense embeddings the phenomenon is native.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

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
    dense = embeddings.DenseSearch(texts)

    print("#" * 78)
    print("# Lab 18-1 — The blind spot of dense search: exact codes")
    print("#" * 78 + "\n")
    print(f"Embedding mode: {embeddings.mode()}\n")

    # --- Step 1: the code query "E-204" --------------------------------------
    print("=" * 78)
    print("STEP 1 — Dense search on an exact code")
    print("=" * 78)
    query = "E-204"
    print(f"Query: \"{query}\"  (we are after the doc_E204 sheet)\n")
    ranking = dense.rank(query)
    print("The top 5 of the dense search:")
    for position, (idx, score) in enumerate(ranking[:5], start=1):
        mark = "  <-- THE RIGHT DOCUMENT" if ids[idx] == "doc_E204" else ""
        print(f"  {position}. {ids[idx]:<18} (score {score:.3f}){mark}")

    rank, _ = rank_of(ranking, ids, "doc_E204")
    print(f"\n  The right sheet (doc_E204) comes in at rank {rank}.")
    if rank and rank > 1:
        ahead = [ids[idx] for idx, _ in ranking[:rank - 1]]
        print(f"  Documents come AHEAD of it: {ahead}")
        print("  And those are other fault codes (E-205, E-311...): to a dense search")
        print("  every code \"looks alike\" — none of them has a meaning of its own.")

    # --- Step 2: the confusion between neighbouring codes ---------------------
    print("\n" + "=" * 78)
    print("STEP 2 — Why E-204, E-205 and E-311 blur together")
    print("=" * 78)
    for code, doc in (("E-204", "doc_E204"), ("E-205", "doc_E205"), ("E-311", "doc_E311")):
        cl = dense.rank(code)
        r, _ = rank_of(cl, ids, doc)
        top = ids[cl[0][0]]
        print(f"  Query \"{code:<6}\" -> on top: {top:<16} | right sheet at rank {r}")
    print("\n  Dense search does not tell two neighbouring codes finely apart:")
    print("  they occupy almost the same region of the semantic space.")

    # --- Step 3: announcing the remedy ----------------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — What is needed: a LITERAL searcher")
    print("=" * 78)
    print("  For \"E-204\" you need a searcher that finds the EXACT run of characters,")
    print("  without trying to understand it. That is the lexical search (BM25), the")
    print("  subject of Lab 18-2 — and the missing half of a hybrid search.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Dense search grasps the INTENTION, not the exact form.")
    print("- Codes, references, versions, acronyms: all blind spots of the dense search.")
    print("- In a business, those exact references are precisely the valuable queries.")
    print("\nWHAT TO REMEMBER")
    print("  Dense search excels at grasping what the user MEANS;")
    print("  it is almost blind to what they WRITE EXACTLY.")


if __name__ == "__main__":
    main()
