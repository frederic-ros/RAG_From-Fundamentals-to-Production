# -*- coding: utf-8 -*-
"""
Lab 13-1 — Splitting a raw document: why it fails (Claire)

Learning objective
------------------
The first gesture, and the wrong one: point a chunker straight at the raw text
extracted "straight through", without having reconstructed it. It runs — and it
produces poisoned fragments.

    You never chunk the raw file.
    You chunk what you have reconstructed from it.

Here `raw_document.txt` (the creased cloth) is cut into fixed-size fragments, and
then those fragments are EXAMINED for the damage:

  - the pagination noise ("14") welded into the middle of a sentence;
  - the repeated running heads and footers polluting the fragments;
  - the flattened table, reduced to a run of words and numbers;
  - the drowned headings, unable to situate the fragment.

Then a simple question is asked — "how many days of remote work?" — and the
exact fragment comes back to answer it... crooked, because of the parasitic "14".

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"
RAW_DOC = CORPUS / "raw_document.txt"

# Markers of the structural noise we expect to find again in the fragments.
# These must match the strings emitted by generate_corpus.py.
HEADERS = ["HUMAN RESOURCES DEPARTMENT", "Confidential — internal use"]


def chunk_fixed_size(text: str, size: int) -> List[str]:
    """Cut every `size` tokens, with no regard for meaning: a blind split."""
    tokens = tk.encoder(text)
    return [tk.decoder(tokens[i:i + size]) for i in range(0, len(tokens), size)]


def diagnose(chunks: List[str]) -> dict:
    """Count the pathologies introduced by chunking the raw text."""
    header_pollution = 0
    lone_numbers = 0
    for c in chunks:
        if any(h in c for h in HEADERS):
            header_pollution += 1
        # An isolated number surrounded by spaces: the remnant of a page number.
        for tok in c.split():
            if tok.isdigit():
                lone_numbers += 1
    return {
        "n_chunks": len(chunks),
        "polluted_fragments": header_pollution,
        "parasitic_numbers": lone_numbers,
    }


def search_for(chunks: List[str], question: str) -> Tuple[str, float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return chunks[idx], float(sims[idx])


def main() -> None:
    print("=" * 78)
    print("Lab 13-1 — Splitting a raw document: why it fails (Claire)")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not RAW_DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    text = RAW_DOC.read_text(encoding="utf-8")
    chunks = chunk_fixed_size(text, 40)
    diag = diagnose(chunks)

    print("\n" + "=" * 78)
    print("WHAT SPLITTING THE RAW TEXT PRODUCES")
    print("=" * 78)
    print(f"  fragments produced: {diag['n_chunks']}")
    print(f"  polluted fragments (repeated heads and feet): {diag['polluted_fragments']}")
    print(f"  parasitic numbers (page numbers) found: {diag['parasitic_numbers']}")

    print("\nA look at the first two fragments, raw:")
    for i, c in enumerate(chunks[:2], start=1):
        excerpt = c.strip().replace("\n", " ")
        print(f"  [{i}] {excerpt[:90]}…")

    # The trap question: the parasitic "14" has welded itself to "two days".
    question = "How many days of remote work per week?"
    fragment, score = search_for(chunks, question)
    print("\n" + "=" * 78)
    print("THE QUESTION THAT REVEALS THE DAMAGE")
    print("=" * 78)
    print(f"  question: \"{question}\"")
    print(f"  fragment found (score {score:.2f}):")
    print(f"    \"{fragment.strip().replace(chr(10), ' ')[:120]}…\"")

    has_14 = " 14 " in (" " + fragment + " ")
    print("\n  Is the fragment EXACT? Yes: it does come from the right place.")
    if has_14:
        print("  Is it CLEAN? No: the page number \"14\" has inserted itself into the")
        print("  sentence — \"two days 14 per week\". The meaning is blurred for the")
        print("  reader, and the vector is blurred for the machine.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The split did not fail: it did exactly what it was asked to do.")
    print("- The INPUT was bad: a flattened text, never reconstructed.")
    print("- Repeated heads, page numbers, a crushed table: all that noise was")
    print("  patiently produced upstream… then thrown into the fragments by the cut.")

    print("\nWHAT TO REMEMBER")
    print("- Cutting into creased cloth means cutting across the grain without knowing it.")
    print("- The problem is not the chunker, but what it was let loose on.")
    print("- In the next lab: the same document, but reconstructed. And everything changes.")


if __name__ == "__main__":
    main()
