# -*- coding: utf-8 -*-
"""
Lab 17-4 — Late Chunking against Contextual Retrieval: which one wins?

Learning objective
------------------
Two recent techniques attack the same problem — a fragment torn from its
document loses what made it intelligible — but from opposite ends.

  Late Chunking acts on the VECTORS: the whole document is encoded first, and
  the vector of each chunk is derived afterwards, so every chunk keeps the trace
  of what was read elsewhere.

  Contextual Retrieval acts on the TEXT: before indexing, each chunk is
  rewritten with a sentence of context — "this fragment comes from the manual of
  the P-42 pump".

Neither is universal. This lab puts them side by side on three questions chosen
to separate them: a dispersed context, a fact plus its context, and an isolated
precise fact.

No API key. Run this first: python generate_corpus.py
"""

from __future__ import annotations

from typing import List

import corpus
import chunkers
import contextual
import embeddings


# Three queries chosen to tell the strategies apart:
QUERIES = [
    ("Which pump does the M-18 motor drive?", "dispersed context"),
    ("How often should the M-18 motor be inspected?", "fact plus context"),
    ("What is the reference of the casing screw?", "isolated precise fact"),
]


def best_text_score(chunks: List[str], query: str) -> float:
    """Score of the best chunk for a query, in a space shared by query and chunks.

    The query is given to the vectoriser so that its vocabulary is covered: the
    scores of the different strategies then become comparable with each other.
    """
    return embeddings.best_shared_score(chunks, query)


def best_late_score(document: str, chunks: List[str], query: str) -> float:
    """Late Chunking score: chunk vectors contextualised by the document,
    compared with the query in a shared space (see embeddings.py)."""
    return embeddings.compare_late_chunking(document, chunks, query)


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    document = corpus.load("long_manual.md")

    print("#" * 78)
    print("# Lab 17-4 — Late Chunking against Contextual Retrieval: which one wins?")
    print("#" * 78 + "\n")
    print(f"Embedding mode: {embeddings.mode()}")
    if embeddings.mode() == "tfidf":
        print("(Late Chunking approximated in TF-IDF; the contrast still holds.)")
    print()

    # --- Prepare the three sets of chunks -----------------------------------
    sections = chunkers.split_structural(document)
    base_chunks = [f"[{t}] {c}" for t, c in sections]              # cut by section
    naive_chunks = chunkers.split_fixed(document, size=160)        # naive cut
    ctx_chunks = contextual.contextualise(base_chunks, document)   # Contextual Retrieval

    print("=" * 78)
    print("STEP 1 — An example of contextualisation (Contextual Retrieval)")
    print("=" * 78)
    print("  Raw chunk:")
    print(f"    \"{base_chunks[-1][:90]}...\"")
    print("  Contextualised chunk (prefix added before indexing):")
    print(f"    \"{ctx_chunks[-1][:110]}...\"")

    # --- Compare on the three queries ---------------------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — Score of the best chunk, by strategy and by query")
    print("=" * 78)
    header = f"{'Query':<42}{'Naive':>8}{'Late':>8}{'Context.':>10}"
    print(header)
    print("  " + "-" * (len(header)))
    for query, nature in QUERIES:
        s_naive = best_text_score(naive_chunks, query)
        s_late = best_late_score(document, base_chunks, query)
        s_ctx = best_text_score(ctx_chunks, query)
        short = (query[:38] + "…") if len(query) > 39 else query
        print(f"  {short:<40}{s_naive:>8.3f}{s_late:>8.3f}{s_ctx:>10.3f}   [{nature}]")

    print("\n" + "=" * 78)
    print("STEP 3 — Reading the results")
    print("=" * 78)
    mode = embeddings.mode()
    if mode == "tfidf":
        print("  In TF-IDF mode, a bag of words, the three strategies give neighbouring")
        print("  scores: that base does not capture the \"dispersed\" context of a document.")
        print("  The figures above are therefore indicative, not a demonstration of the")
        print("  contrast. The chapter's lesson shows fully with REAL dense embeddings")
        print("  (sentence-transformers), where:")
    else:
        print("  With dense embeddings, the expected contrast appears:")
    print("   - on a dispersed context (the M-18 to P-42 link, scattered), Late Chunking")
    print("     and Contextual Retrieval beat the naive cut, which isolates the fragments;")
    print("   - on an isolated, precise fact (the screw reference), Contextual Retrieval")
    print("     keeps the detail sharp while Late Chunking DILUTES it, by averaging the")
    print("     whole context of the document.")
    print("\n  To run in dense mode: install sentence-transformers and make sure the")
    print("  all-MiniLM-L6-v2 model is reachable (see the README).")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Late Chunking acts on the vectors; Contextual Retrieval on the text.")
    print("- Late Chunking shines on dispersed context; it dilutes isolated facts.")
    print("- Contextual Retrieval keeps the detail, at the price of a rewrite (LLM cost).")
    print("- No method is universal: the choice depends on the type of question.")
    print("\nWHAT TO REMEMBER")
    print("  For a long time the effort went into RETRIEVING fragments better; Contextual")
    print("  Retrieval begins by WRITING them better. Late Chunking, for its part,")
    print("  contextualises the vectors without touching the text.")


if __name__ == "__main__":
    main()
