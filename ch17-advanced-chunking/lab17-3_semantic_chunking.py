# -*- coding: utf-8 -*-
"""
Lab 17-3 — Semantic chunking: cutting where the meaning changes

Learning objective
------------------
Some documents carry no structure at all: an inspection report, a set of notes,
a transcript. There is no heading to follow. Semantic chunking reads the text
sentence by sentence, measures the similarity between consecutive sentences, and
places a boundary where that similarity DROPS — that is, where the subject
changes.

The report used here runs through three subjects in a row: the P-42 pump, then
the M-18 motor, then the storage tank. Nothing marks the transitions, and yet
the similarity curve makes them visible.

A note on the threshold: the scale of the similarities depends on the embedding
model. An ADAPTIVE threshold is used here, computed from the distribution of the
text itself, so that the cut falls at the relative breaks — robust with a dense
model as well as with TF-IDF.

No API key. Run this first: python generate_corpus.py
"""

from __future__ import annotations

import corpus
import chunkers
import embeddings


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    text = corpus.load("inspection_report.txt")

    print("#" * 78)
    print("# Lab 17-3 — Semantic chunking: cutting where the meaning changes")
    print("#" * 78 + "\n")
    print(f"Embedding mode: {embeddings.mode()}\n")

    # --- Step 1: the sentences and their similarities -----------------------
    print("=" * 78)
    print("STEP 1 — Similarity between consecutive sentences")
    print("=" * 78)
    sentences = chunkers.split_into_sentences(text)
    chunks, similarities = chunkers.split_semantic(text, adaptive=True)

    import numpy as np
    threshold = float(np.mean(similarities) - 0.5 * np.std(similarities))
    print(f"Adaptive threshold computed: {threshold:.3f}\n")
    for i, sim in enumerate(similarities):
        breakpoint_mark = "  <<< DROP -> boundary" if sim < threshold else ""
        print(f"  Sentence {i+1} -> {i+2}: similarity {sim:.3f}{breakpoint_mark}")
        print(f"      S{i+1}: {sentences[i][:62]}")
    print(f"      S{len(sentences)}: {sentences[-1][:62]}")

    # --- Step 2: the chunks obtained ----------------------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — The semantic chunks obtained")
    print("=" * 78)
    for i, c in enumerate(chunks, 1):
        print(f"\n  Chunk {i}:")
        print(f"    \"{c}\"")

    # --- Step 3: contrast with the fixed cut --------------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — Contrast with the fixed cut")
    print("=" * 78)
    fixed = chunkers.split_fixed(text, size=70)
    cut_open = sum(1 for c in fixed if c and not c.rstrip().endswith((".", "!", "?")))
    print(f"  Fixed cut (70 chars): {len(fixed)} chunks, of which {cut_open} end in")
    print("  the middle of a sentence. For instance:")
    print(f"    \"{fixed[0]}\"")
    print(f"  Semantic cut: {len(chunks)} chunks, each centred on one subject")
    print("  (the P-42 pump, then the M-18 motor, then the tank), with no sentence cut.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Meaning can guide the cut even with no explicit structure.")
    print("- A boundary falls where the similarity drops: a change of subject.")
    print("- The chunks obtained are thematically homogeneous, so easier to retrieve.")
    print("\nWHAT TO REMEMBER")
    print("  With no visible plan, you read the text sentence by sentence and cut at")
    print("  the breaks in meaning, not at fixed intervals.")


if __name__ == "__main__":
    main()
