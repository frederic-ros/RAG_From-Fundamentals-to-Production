# -*- coding: utf-8 -*-
"""
Lab 16-1 — Every document is there, the answer stays invisible (Julien)

Learning objective
------------------
Reproduce the chapter's WHEN OF SHOCK. In the earlier chapters something was
always missing: the right context, the right version. Here NOTHING IS MISSING.
Every document is present, exact, perfectly indexed — and the answer is still
nowhere to be found by search.

    "Which procedure supersedes procedure P-17 today?"

The corpus holds P-17, P-18 and P-21. The search finds them without trouble. But
no document holds the sentence "P-21 supersedes P-17": each link lives in a
different document. The complete chain is written NOWHERE.

    A document holds a piece of information.
    A graph shows how the pieces of information are linked to each other.

This lab shows the two worlds side by side:

  1. the similarity search — perfect, and yet mute;
  2. a simple structure of relations, which DEDUCES the answer.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import corpus
import embeddings


QUESTION = "Which procedure supersedes procedure P-17 today?"


def show_search(docs: dict) -> None:
    """Step 1: the similarity search does find the right documents..."""
    names = list(docs.keys())
    texts = list(docs.values())
    engine = embeddings.SimilarityEngine(texts)

    print("=" * 78)
    print("STEP 1 — The similarity search")
    print("=" * 78)
    print(f"Embedding mode: {embeddings.mode()}")
    print(f"Question: \"{QUESTION}\"\n")

    results = engine.search_for(QUESTION, k=3)
    print("The top 3 closest documents:")
    for rank, (idx, score) in enumerate(results, 1):
        print(f"  {rank}. {names[idx]:<24} (score {score:.3f})")

    print("\nThe search works: it does bring back the procedure sheets.")
    print("But let us read what those documents actually say...")

    # Show the key sentence of each sheet found.
    for idx, _ in results:
        name = names[idx]
        if name.startswith("procedure_"):
            sentence = _supersede_sentence(texts[idx])
            print(f"    - {name}: {sentence}")

    print("\n=> No document says \"P-21 supersedes P-17\".")
    print("   P-18 says it supersedes P-17. P-21 says it supersedes P-18.")
    print("   The final link, P-21, NEVER mentions P-17 at all:")
    print("   in vector terms it is \"too far\" from the question.")


def _supersede_sentence(text: str) -> str:
    """Extract the sentence about superseding, for display."""
    for sentence in text.replace("\n", " ").split("."):
        if "supersedes" in sentence.lower():
            return sentence.strip() + "."
    return "(says nothing about superseding)"


def show_graph() -> None:
    """Step 2: the same question, resolved by following the relations."""
    g = corpus.load_graph()

    print("\n" + "=" * 78)
    print("STEP 2 — The structure of relations")
    print("=" * 78)
    print("The same facts, but made explicit as triples:")
    for subject, relation, obj in g.triples():
        if relation in ("supersedes", "superseded by"):
            print(f"  {subject:<8} --[{relation}]--> {obj}")

    print(f"\nQuestion: \"{QUESTION}\"")
    print("The \"superseded by\" relation is followed AS A CHAIN from P-17:")
    chain = g.chain("P-17", "superseded by")
    print("   " + "  ->  ".join(chain))

    current = chain[-1]
    print(f"\n=> The procedure in force that supersedes P-17, in the end, is: {current}.")
    print("   That answer was written in NO document.")
    print("   It is a LOGICAL CONSEQUENCE of the relations, not a piece of text.")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    docs = corpus.load_documents()

    print("#" * 78)
    print("# Lab 16-1 — Every document is there, the answer stays invisible")
    print("#" * 78 + "\n")

    show_search(docs)
    show_graph()

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Finding EVERY document does not guarantee finding the answer.")
    print("- Similarity finds the stations; it cannot trace the route between them.")
    print("- Some answers are not IN a document, but BETWEEN the documents, in the")
    print("  link that joins them.")
    print("\nWHAT TO REMEMBER")
    print("  Every piece of information may be present.")
    print("  The answer can still stay invisible.")


if __name__ == "__main__":
    main()
