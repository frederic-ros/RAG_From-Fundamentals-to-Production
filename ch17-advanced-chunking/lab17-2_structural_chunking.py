# -*- coding: utf-8 -*-
"""
Lab 17-2 — Structural chunking: cutting along the document's own outline

Learning objective
------------------
The first advanced strategy of the chapter, and the cheapest: many documents
already carry their plan — Markdown headings, HTML sections, numbered articles.
Rather than imposing an arbitrary length, follow that plan.

Each section becomes one chunk, whole, and carries its title with it. The title
gives the fragment a context it would not otherwise have.

The lab compares, on Julien's M-18 manual:
  - a fixed cut of 80 characters, which still breaks the critical sentence;
  - a structural cut, where the section stays whole and comes with its heading.

No API key. Run this first: python generate_corpus.py
"""

from __future__ import annotations

import corpus
import chunkers
import embeddings

QUESTION = "What is the inspection frequency of the M-18 motor?"


def step_structural(markdown: str) -> list:
    print("=" * 78)
    print("STEP 1 — Cutting along the Markdown outline (# / ## headings)")
    print("=" * 78)
    sections = chunkers.split_structural(markdown)
    chunks = []
    for title, content in sections:
        # Prefix the content with its title: the chunk carries its context.
        chunk = f"[{title}] {content}"
        chunks.append(chunk)
        print(f"\n  Section \"{title}\":")
        print(f"    {content[:90]}{'...' if len(content) > 90 else ''}")
    print("\n  Every section stays whole; no sentence is cut.")
    return chunks


def step_comparison(markdown: str, structural_chunks: list) -> None:
    print("\n" + "=" * 78)
    print("STEP 2 — Structural against fixed, on the same question")
    print("=" * 78)
    print(f"Embedding mode: {embeddings.mode()}")
    print(f"Question: \"{QUESTION}\"\n")

    # A fixed cut of the same document, in characters.
    raw_text = markdown
    fixed_chunks = chunkers.split_fixed(raw_text, size=80)

    fixed_engine = embeddings.SimilarityEngine(fixed_chunks)
    idx_f, score_f = fixed_engine.search_for(QUESTION, k=1)[0]
    fixed_has = "100 hours" in fixed_chunks[idx_f]
    print("  FIXED (80 chars) — best chunk:")
    print(f"    (score {score_f:.3f}) \"{fixed_chunks[idx_f].strip()}\"")
    print(f"    Does it hold the complete answer \"100 hours\"? "
          f"{'yes' if fixed_has else 'NO — cut right through it'}")

    struct_engine = embeddings.SimilarityEngine(structural_chunks)
    idx_s, score_s = struct_engine.search_for(QUESTION, k=1)[0]
    print("\n  STRUCTURAL — best chunk:")
    print(f"    (score {score_s:.3f}) \"{structural_chunks[idx_s][:110]}...\"")

    struct_has = "100 hours" in structural_chunks[idx_s]
    print(f"\n  Does the structural chunk hold the complete answer \"100 hours\"? "
          f"{'yes' if struct_has else 'no'}")
    print("  Even when the fixed cut sometimes gets a good score, its best chunk")
    print("  stops in the middle of the sentence, amputated of the answer. The")
    print("  structural chunk holds it whole, along with its heading.")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    markdown = corpus.load("motor_M18_manual.md")

    print("#" * 78)
    print("# Lab 17-2 — Structural chunking: cutting along the document's outline")
    print("#" * 78 + "\n")

    chunks = step_structural(markdown)
    step_comparison(markdown, chunks)

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The document's native structure is a goldmine for chunking.")
    print("- Cutting by section keeps ideas whole and supplies a title as context.")
    print("- No LLM needed: a Markdown or HTML parser is enough in many cases.")
    print("\nWHAT TO REMEMBER")
    print("  The document already carries its own plan. The first advanced chunking")
    print("  strategy is to follow it.")


if __name__ == "__main__":
    main()
