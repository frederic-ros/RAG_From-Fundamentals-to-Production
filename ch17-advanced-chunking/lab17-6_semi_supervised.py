# -*- coding: utf-8 -*-
"""
Lab 17-6 — Semi-supervised chunking: the expert validates, the system learns

Learning objective
------------------
For critical cases, neither the algorithm nor the agent is enough on its own;
but cutting 5,000 pages by hand is unthinkable. Between the two lies
SEMI-SUPERVISED chunking. The system proposes a first cut; the expert only has
to VALIDATE, MERGE or SPLIT, in a few clicks. Moving from creation to plain
validation divides the human time by ten.

Above all, each gesture of the expert — Claire merging "rule" and "exception" —
improves more than today's chunking: it builds a DATASET of human preferences,
the first harvest of expert judgements and the starting point of domain
calibration, in the last part of the book.

This lab provides two things:
  1. a console simulation, runnable anywhere with no browser, which replays
     Claire's validation session and WRITES the calibration file corrections.csv;
  2. a Streamlit interface (interface.py) to do the same thing visually, if
     streamlit is installed.

No API key. Run this first: python generate_corpus.py
Then: python lab17-6_semi_supervised.py   (simulation plus corrections.csv)
Or:   streamlit run interface.py          (visual interface)
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

import corpus

OUTPUT_CSV = Path(__file__).resolve().parent / "corrections.csv"


def initial_proposal(text: str) -> List[str]:
    """The cut proposed by the system, deliberately imperfect.

    Sentences are grouped so that the rule, the exception and the following
    article are isolated, which leaves the rule (Article 5) and its exception in
    two SEPARATE chunks — the error Claire will fix by merging them.
    """
    import re
    sentences = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]
    # Group each "rule" sentence with its continuation, but keep "Exception" as
    # a separate chunk: the imperfect cut that has to be corrected.
    chunks: List[str] = []
    buffer: List[str] = []
    for sentence in sentences:
        if sentence.lower().startswith("exception") or re.match(r"Article\s+\d+", sentence):
            if buffer:
                chunks.append(" ".join(buffer))
                buffer = []
        buffer.append(sentence)
    if buffer:
        chunks.append(" ".join(buffer))
    return chunks


def claires_session(chunks: List[str]) -> Tuple[List[str], List[dict]]:
    """Replay Claire's decisions and record her corrections.

    Claire's business decisions:
      - MERGE the "rule" (Article 5) and "exception" fragments;
      - VALIDATE the rest.
    Every decision is logged, for the calibration.
    """
    corrections: List[dict] = []
    result: List[str] = []

    i = 0
    while i < len(chunks):
        chunk = chunks[i]
        # Claire's business rule: merge an exception with the preceding sentence.
        if chunk.strip().lower().startswith("exception") and result:
            merged = result[-1] + " " + chunk
            result[-1] = merged
            corrections.append({
                "original_chunk": chunk[:50],
                "action": "merge",
                "justification": "rule and exception inseparable",
            })
        else:
            result.append(chunk)
            corrections.append({
                "original_chunk": chunk[:50],
                "action": "validate",
                "justification": "coherent fragment",
            })
        i += 1

    return result, corrections


def write_calibration(corrections: List[dict]) -> None:
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        fields = ["original_chunk", "action", "justification"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in corrections:
            writer.writerow(row)


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    text = corpus.load("hr_agreement.txt")

    print("#" * 78)
    print("# Lab 17-6 — Semi-supervised chunking: the expert validates, the system learns")
    print("#" * 78 + "\n")

    print("=" * 78)
    print("STEP 1 — The system's initial proposal (to be corrected)")
    print("=" * 78)
    proposal = initial_proposal(text)
    for i, c in enumerate(proposal, 1):
        print(f"  Chunk {i}: \"{c[:66]}{'...' if len(c) > 66 else ''}\"")

    print("\n" + "=" * 78)
    print("STEP 2 — Claire's validation session (HR)")
    print("=" * 78)
    final, corrections = claires_session(proposal)
    for c in corrections:
        print(f"  [{c['action']:<8}] {c['original_chunk']:<52} ({c['justification']})")

    print("\n  Final cut, after Claire's corrections:")
    for i, c in enumerate(final, 1):
        print(f"  Chunk {i}: \"{c[:80]}{'...' if len(c) > 80 else ''}\"")

    print("\n" + "=" * 78)
    print("STEP 3 — The calibration file produced")
    print("=" * 78)
    write_calibration(corrections)
    merges = sum(1 for c in corrections if c["action"] == "merge")
    print(f"  File written: {OUTPUT_CSV.name}")
    print(f"  {len(corrections)} decisions recorded, of which {merges} merge(s).")
    print("  These decisions do not only fix today's cut: they form a set of human")
    print("  preferences, the first material of domain calibration.")

    # For the record: the agent would obtain the right merge directly.
    print("\n  (For the record, the agent of Lab 17-5 would propose the rule-plus-")
    print("   exception merge directly; semi-supervision stays useful when the agent")
    print("   gets it wrong, or for critical corpora where a human must validate.)")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Validating rather than creating divides the human time by ten.")
    print("- Each correction is an expert judgement captured at LOW COST, and RECORDED.")
    print("- It is the first stone of domain calibration, in the last part of the book.")
    print("\nWHAT TO REMEMBER")
    print("  The expert does not only correct the cut: they pass on their way of")
    print("  understanding the document — and that understanding becomes data.")
    print("\n  Visual interface: streamlit run interface.py")


if __name__ == "__main__":
    main()
