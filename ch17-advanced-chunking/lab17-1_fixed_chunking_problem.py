# -*- coding: utf-8 -*-
"""
Lab 17-1 — Fixed chunking breaks the meaning: Julien's case

Learning objective
------------------
Reproduce the ill the chapter is about: information that is PRESENT and that a
bad chunking makes INVISIBLE. Julien's manual holds, in black and white:

    "The M-18 drive motor must be inspected every 100 hours..."

But a fixed-size cut (50 characters here) falls right in the middle:
"...every 100 h" | "ours in cruising...". Neither half, in isolation, resembles
the question "how often should the M-18 be inspected?". The answer was there;
the chunking made it unfindable.

This lab shows:
  1. the fixed cut and the sentence broken in two;
  2. the failure of retrieval over the fixed chunks;
  3. the same corpus, cut at sentence boundaries: the answer becomes findable
     again.

The problem is NOT the search engine, it is the CUT upstream of it.

No API key. Run this first: python generate_corpus.py
"""

from __future__ import annotations

import corpus
import chunkers
import embeddings

QUESTION = "How many hours between inspections of the M-18 motor?"

# The critical sentence of the manual, the one the fixed cut will break.
SENTENCE = ("The M-18 drive motor must be inspected every 100 hours in cruising "
            "mode. This instruction is critical for the P-42 pump.")


def step_fixed_split() -> list:
    print("=" * 78)
    print("STEP 1 — The fixed-size cut (50 characters)")
    print("=" * 78)
    chunks = chunkers.split_fixed(SENTENCE, size=50)
    for i, c in enumerate(chunks, 1):
        print(f"  Chunk {i}: \"{c}\"")
    print("\n  Look at chunks 1 and 2: \"100 h | ours\". The number is cut, and")
    print("  \"inspected\" and \"100 hours\" end up in two different chunks.")
    return chunks


def step_retrieval_failure(fixed_chunks: list) -> None:
    print("\n" + "=" * 78)
    print("STEP 2 — The search fails on the fixed chunks")
    print("=" * 78)
    print(f"Embedding mode: {embeddings.mode()}")
    print(f"Question: \"{QUESTION}\"\n")

    engine = embeddings.SimilarityEngine(fixed_chunks)
    results = engine.search_for(QUESTION, k=len(fixed_chunks))
    for rank, (idx, score) in enumerate(results, 1):
        mark = "  <-- holds \"100 h\"" if "100 h" in fixed_chunks[idx] else ""
        print(f"  {rank}. (score {score:.3f}) \"{fixed_chunks[idx]}\"{mark}")

    best_idx = results[0][0]
    has_answer = "100 hours" in fixed_chunks[best_idx]
    print(f"\n  Does the best chunk hold the complete answer \"100 hours\"? "
          f"{'yes' if has_answer else 'NO'}")
    print("  No chunk brings together \"inspected\", \"M-18\" and \"100 hours\": the")
    print("  answer is scattered, and therefore effectively invisible to the search.")


def step_solution() -> None:
    print("\n" + "=" * 78)
    print("STEP 3 — The same information, cut at sentence boundaries")
    print("=" * 78)
    chunks = chunkers.split_by_sentences(SENTENCE, sentences_per_chunk=1)
    for i, c in enumerate(chunks, 1):
        print(f"  Chunk {i}: \"{c}\"")

    engine = embeddings.SimilarityEngine(chunks)
    idx, score = engine.search_for(QUESTION, k=1)[0]
    print(f"\n  Best chunk for the question (score {score:.3f}):")
    print(f"    \"{chunks[idx]}\"")
    print("  The sentence stayed whole: \"100 hours\" and \"inspected\" are together")
    print("  again. The answer becomes findable — without changing the engine.")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    print("#" * 78)
    print("# Lab 17-1 — Fixed chunking breaks the meaning: Julien's case")
    print("#" * 78 + "\n")

    fixed_chunks = step_fixed_split()
    step_retrieval_failure(fixed_chunks)
    step_solution()

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Information that is present can be made invisible by a bad cut.")
    print("- The fixed cut produces \"silence\": an idea cut in two, unreadable.")
    print("- The problem is not the retrieval, it is the CUT upstream.")
    print("\nWHAT TO REMEMBER")
    print("  Cutting is not a mechanical act: it is an intervention of precision.")
    print("  You incise at the joints of meaning, never in the middle of an idea.")


if __name__ == "__main__":
    main()
