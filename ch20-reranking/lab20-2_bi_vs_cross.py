# -*- coding: utf-8 -*-
"""
Lab 20-2 — Bi-encoder against cross-encoder (two ways of judging relevance)

Learning objective
------------------
Why does re-ranking exist? Because there are two deeply different ways of
comparing a question with a document:

  - the BI-ENCODER encodes the question and the document SEPARATELY, then
    measures a distance. Fast, because the vectors are precomputed, but coarse:
    at the moment it encoded the document, it knew nothing of the question.
  - the CROSS-ENCODER reads the PAIR (question, document) TOGETHER and produces a
    relevance score directly. Slow, one computation per pair, but fine: it really
    "re-reads" the question against each document.

    The cross-encoder really re-reads the question.

This lab compares the two rankings on the same query, and shows that the
cross-encoder drives out the neighbouring codes (M-17, M-19) that the bi-encoder
had hoisted up.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import reranklib as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 20-2 — Bi-encodeur contre cross-encodeur")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    print(f"\nModel mode: {R.mode()}")

    best = 0
    question = "motor M-18"
    print(f"Query: \"{question}\"   (expected right fragment: #{best}, the M-18 procedure)")

    # --- The two rankings -----------------------------------------------------
    bi = R.BiEncoder(texts)
    cross = R.CrossEncoder()

    cl_bi = bi.rank(question)
    bi_order = [i for i, _ in cl_bi]

    # The cross-encoder re-scores EVERY fragment; the corpus is small here.
    cl_cross = cross.rerank(question, [(i, texts[i]) for i in range(len(frags))])
    cross_order = [i for i, _ in cl_cross]

    print("\n" + "=" * 78)
    print("TWO RANKINGS, THE SAME DOCUMENTS")
    print("=" * 78)
    print(f"  {'rank':>4s} | {'BI-ENCODER':<22s} | {'CROSS-ENCODER':<22s}")
    print("  " + "-" * 56)
    for rank in range(6):
        ib = bi_order[rank]
        ic = cross_order[rank]
        mb = " *" if ib == best else "  "
        mc = " *" if ic == best else "  "
        print(f"  {rank+1:4d} | {frags[ib]['subject']:<18s}{mb} | "
              f"{frags[ic]['subject']:<18s}{mc}")
    print("  (* = the right fragment #0)")

    bi_rank = R.rank_of(bi_order, best)
    cross_rank = R.rank_of(cross_order, best)

    print("\n" + "=" * 78)
    print("READING THE RESULT")
    print("=" * 78)
    print(f"  Rank of the right fragment for the BI-ENCODER   : {bi_rank}")
    print(f"  Rank of the right fragment for the CROSS-ENCODER: {cross_rank}")
    print()
    print("- The bi-encoder puts M-17 and M-19 at the top of the ranking: to it, those")
    print("  neighbouring codes resemble each other too much to be separated.")
    print("- The cross-encoder, reading the pair (question, document) together,")
    print("  recognises that the question is about M-18 specifically: it pushes M-17")
    print("  and M-19 down and lifts the fragments that REALLY speak of M-18.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The same corpus, the same query, two rankings: the method of comparison")
    print("  changes the result at the top of the list.")
    print("- The cross-encoder is finer because it sets the question and the document")
    print("  side by side, instead of comparing two summaries encoded blind.")
    print("- That extra fineness has a cost, one computation per pair: it cannot be")
    print("  applied to the whole corpus. Hence the two-stage pipeline (Lab 20-3).")

    print("\nWHAT TO REMEMBER")
    print("- Bi-encoder: SEPARATE encoding, fast, coarse — good for retrieving broadly.")
    print("- Cross-encoder: JOINT reading, slow, fine — good for refining the top.")
    print("- Their roles are complementary, not competing.")


if __name__ == "__main__":
    main()
