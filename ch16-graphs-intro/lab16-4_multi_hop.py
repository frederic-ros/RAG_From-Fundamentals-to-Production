# -*- coding: utf-8 -*-
"""
Lab 16-4 — Multi-hop questions: chaining the facts (Julien)

Learning objective
------------------
Name and resolve MULTI-HOP questions: the ones whose answer requires chaining
several facts, each resting on the result of the last.

    A simple question: "What is procedure P-21?" -> one hop, one document.
    A multi-hop question: "Which procedure supersedes the one that superseded
    P-17?" -> P-17 to P-18 to P-21.

The difficulty is no longer documentary relevance, but NAVIGATION through the
relations. This lab:

  1. displays the TRAVERSALS followed explicitly (a chain, and a BFS);
  2. counts the number of hops;
  3. shows WHY similarity fails: the final link is structurally disconnected
     from the question, because it shares none of its words.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import corpus
import embeddings
from graph import format_path


def lineage_question(g) -> None:
    """"Which procedure supersedes the one that superseded P-17?" — a chain."""
    print("=" * 78)
    print("QUESTION 1 — \"Which procedure supersedes the one that superseded P-17?\"")
    print("=" * 78)
    chain = g.chain("P-17", "superseded by")
    print("  The traversal followed (the \"superseded by\" relation, as a chain):")
    print("    " + " ->(superseded by)-> ".join(chain))
    print(f"  Number of hops: {len(chain) - 1}")
    print(f"  Answer: {chain[-1]}, the procedure in force.")


def dependency_question(g) -> None:
    """"Which supplier does pump P-42 ultimately depend on?" — a BFS."""
    print("\n" + "=" * 78)
    print("QUESTION 2 — \"Which supplier does pump P-42 ultimately depend on?\"")
    print("=" * 78)
    path = g.path_bfs("P-42", "Mecafluid")
    if path is not None:
        print("  Route found, by breadth-first search:")
        print("    " + format_path(path, "P-42"))
        print(f"  Number of hops: {len(path)}")
        print(f"  Answer: {path[-1][1]}.")
    else:
        print("  No path found.")


def why_similarity_fails(g) -> None:
    """Show that the final link does not resemble the question."""
    print("\n" + "=" * 78)
    print("WHY SIMILARITY FAILS")
    print("=" * 78)

    docs = corpus.load_documents()
    names = list(docs.keys())
    texts = list(docs.values())
    engine = embeddings.SimilarityEngine(texts)

    question = "Which procedure supersedes the one that superseded P-17?"
    print(f"Embedding mode: {embeddings.mode()}")
    print(f"Question: \"{question}\"\n")
    results = engine.search_for(question, k=3)
    for rank, (idx, score) in enumerate(results, 1):
        print(f"  {rank}. {names[idx]:<24} (score {score:.3f})")

    # The answer is P-21; let us see where it ranks.
    rank_p21 = next((r for r, (idx, _) in enumerate(engine.search_for(question, k=20), 1)
                     if names[idx] == "procedure_P21.txt"), None)
    print(f"\n  The document carrying the ANSWER (procedure_P21.txt) comes in at rank {rank_p21}.")
    print("  But the rank is not the real problem. The real problem lies elsewhere:")
    print("  even if the search brings back all three sheets, NONE says \"P-21")
    print("  supersedes P-17\". The P-21 sheet never mentions P-17: it talks about P-18.")
    print("  Similarity juxtaposes the links; it does not CHAIN them. The connection")
    print("  P-17 -> P-21 exists only if you TRAVERSE the relation, hop after hop.")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    g = corpus.load_graph()

    print("#" * 78)
    print("# Lab 16-4 — Multi-hop questions: chaining the facts")
    print("#" * 78 + "\n")

    lineage_question(g)
    dependency_question(g)
    why_similarity_fails(g)

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- A multi-hop question chains several triples that share a node.")
    print("- The graph resolves it by TRAVERSAL — a chain, a BFS — not by resemblance.")
    print("- Similarity brings back the scattered links and leaves the model to")
    print("  reconstruct the thread, often in vain: the last link does not resemble")
    print("  the question at all.")
    print("\nWHAT TO REMEMBER")
    print("  For a multi-hop question, what is missing is not a better ranking:")
    print("  it is the RELATION itself, explicitly represented.")


if __name__ == "__main__":
    main()
