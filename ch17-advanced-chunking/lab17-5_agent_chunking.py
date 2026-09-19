# -*- coding: utf-8 -*-
"""
Lab 17-5 — The chunking agent: delegating the cut to an LLM

Learning objective
------------------
The most advanced strategy of the chapter, and the most expensive. Structural
chunking follows the layout; semantic chunking follows the vocabulary. Neither
understands the BUSINESS logic of the text.

In an HR or regulatory agreement, a rule and its exception are inseparable:
cutting between them produces a false reading, as Chapter 12 already showed. No
length and no similarity threshold knows that. A model reading the text does.

The agent receives an instruction — "insert [CUT] when a new rule begins, keep a
rule and its exception together" — and decides on meaning rather than on length.

In this lab the agent is simulated by deterministic rules, so that everything
runs offline (see contextual.py). The code marks precisely where a real LLM call
would go. The aim is to show the FLOW, not to reproduce the finesse of a model.

No API key. Run this first: python generate_corpus.py
"""

from __future__ import annotations

import corpus
import chunkers
import contextual


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    text = corpus.load("hr_agreement.txt")

    print("#" * 78)
    print("# Lab 17-5 — The chunking agent: delegating the cut to an LLM")
    print("#" * 78 + "\n")

    # --- The prompt a real agent would receive ------------------------------
    print("=" * 78)
    print("STEP 1 — The instruction given to the agent (the prompt)")
    print("=" * 78)
    print('  "You are an expert in processing HR documents. Read this text.')
    print('   Insert [CUT] when a new rule begins. Keep a rule and its exception')
    print('   TOGETHER. Justify each cut in three words."')
    print("\n  (In this lab the agent is simulated by deterministic rules; the code")
    print("   shows where a real LLM call would be plugged in.)")

    # --- The cut proposed by the agent --------------------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — The cut proposed by the agent")
    print("=" * 78)
    segments = contextual.agent_chunk(text)
    for i, (segment, justification) in enumerate(segments, 1):
        print(f"\n  Chunk {i}  [CUT — {justification}]:")
        print(f"    \"{segment}\"")

    # --- Contrast with semantic chunking ------------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — Contrast with semantic chunking")
    print("=" * 78)
    semantic, _ = chunkers.split_semantic(text, adaptive=True)
    print(f"  Semantic chunking proposes {len(semantic)} fragments, cutting at the")
    print("  breaks in vocabulary. It does NOT KNOW that a rule and its exception")
    print("  must stay together: it may separate them.")
    print(f"  The agent proposes {len(segments)} fragments and has MERGED the rule")
    print("  (Article 5) with its exception, because it understands the legal link.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The agent captures business nuances a similarity calculation cannot see.")
    print("- It decides by the logic of the text, not by a length or a threshold.")
    print("- A precise but costly method — one LLM call per decision — to be kept")
    print("  for high-value corpora.")
    print("\nWHAT TO REMEMBER")
    print("  When the boundary depends on BUSINESS meaning, a rule and its exception")
    print("  being inseparable, you delegate the decision to an agent rather than to")
    print("  a blind rule.")


if __name__ == "__main__":
    main()
