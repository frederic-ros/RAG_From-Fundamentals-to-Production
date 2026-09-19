# -*- coding: utf-8 -*-
"""
Lab 20-4 — Why the top results all look alike (MMR diversification)

Learning objective
------------------
Re-ranking by relevance solves one problem and leaves another. Imagine the best
fragments are excellent BUT near-identical: five wordings of the same fact. The
model receives the same thing five times and misses the angle that was absent.

    More relevant does not mean more useful.

The answer has a name: MMR (Maximal Marginal Relevance). Instead of choosing
fragments on relevance alone, they are chosen on a BALANCE: relevant to the
question AND different from what has already been kept. A lambda slider sets the
dosage (1 is pure relevance, 0 is pure diversity).

This lab shows a redundant selection (without MMR), then a diversified one (with
MMR), and sweeps lambda to see the tipping.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import reranklib as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 20-4 — Why the top results all look alike (MMR)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    print(f"\nModel mode: {R.mode()}")

    # A broad question: we want a PANORAMA of motor M-18, not a single facet.
    question = "What is there to know about motor M-18?"
    print(f"Query (broad): \"{question}\"")
    print("For this kind of question we want to COVER several facets, not repeat one.")

    bi = R.BiEncoder(texts)
    vectors = bi.vectors()
    vec_q = bi.query_vector(question)

    # The candidate pool deliberately mixes three near-DUPLICATES about the
    # inspection (ids 4, 5, 6: "every 100 hours", in three wordings) with DIVERSE
    # facets (safety, supplier, failure, the recent version).
    candidates = [4, 5, 6, 7, 8, 9, 11]
    k = 4

    def sim(a, b):
        import numpy as np
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(a @ b / (na * nb)) if na and nb else 0.0

    def mean_redundancy(selection):
        """The mean similarity between the fragments kept: the higher it is, the
        more redundant the selection, because the fragments resemble each other."""
        import itertools
        pairs = list(itertools.combinations(selection, 2))
        if not pairs:
            return 0.0
        return sum(sim(vectors[a], vectors[b]) for a, b in pairs) / len(pairs)

    print(f"\nA pool of {len(candidates)} candidates, three of them near-duplicates about")
    print("the inspection (ids 4, 5, 6: \"every 100 hours\", three wordings), plus varied facets.")

    # --- Without MMR: pure relevance (lambda = 1) -----------------------------
    without_mmr = R.mmr(vec_q, vectors, candidates, k=k, lam=1.0)
    # --- With MMR: a balance (lambda = 0.5) -----------------------------------
    with_mmr = R.mmr(vec_q, vectors, candidates, k=k, lam=0.5)

    print("\n" + "=" * 78)
    print("WITHOUT MMR (pure relevance, lambda = 1.0)")
    print("=" * 78)
    for rank, i in enumerate(without_mmr, start=1):
        print(f"  {rank}. #{i:2d} [{frags[i]['subject']:<18s}] "
              f"\"{texts[i][:50].strip()}…\"")

    print("\n" + "=" * 78)
    print("WITH MMR (a relevance/diversity balance, lambda = 0.5)")
    print("=" * 78)
    for rank, i in enumerate(with_mmr, start=1):
        print(f"  {rank}. #{i:2d} [{frags[i]['subject']:<18s}] "
              f"\"{texts[i][:50].strip()}…\"")

    # Two measures: distinct facets AND internal redundancy.
    facets_without = len({frags[i]["subject"] for i in without_mmr})
    facets_with = len({frags[i]["subject"] for i in with_mmr})
    red_without = mean_redundancy(without_mmr)
    red_with = mean_redundancy(with_mmr)
    print("\n" + "=" * 78)
    print("DIVERSITY COVERED (top 4)")
    print("=" * 78)
    print(f"  {'':<12s} | {'distinct facets':>20s} | {'internal redundancy':>20s}")
    print("  " + "-" * 58)
    print(f"  {'Without MMR':<12s} | {facets_without:>20d} | {red_without:>20.3f}")
    print(f"  {'With MMR':<12s} | {facets_with:>20d} | {red_with:>20.3f}")
    print("\n  -> MMR raises the facet count and LOWERS the internal redundancy:")
    print("     the fragments kept resemble each other less, so they cover more.")

    # --- Sweeping lambda ------------------------------------------------------
    print("\n" + "=" * 78)
    print("THE lambda SLIDER: FROM PURE RELEVANCE TO PURE DIVERSITY")
    print("=" * 78)
    print(f"  {'lambda':>6s} | facets   | subjects kept")
    print("  " + "-" * 58)
    for lam in [1.0, 0.8, 0.6, 0.4, 0.0]:
        sel = R.mmr(vec_q, vectors, candidates, k=k, lam=lam)
        nf = len({frags[i]["subject"] for i in sel})
        subjects = ", ".join(frags[i]["subject"] for i in sel)
        print(f"  {lam:6.1f} | {nf:^8d} | {subjects}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Without MMR the summit fills with near-duplicates: all relevant, all")
    print("  redundant. The model reads the same idea five times.")
    print("- With MMR the most relevant is kept, and THEN what brings a new angle is")
    print("  preferred: the coverage of the subject widens.")
    print("- lambda sets the dosage: high for a sharp factual question, lower for a")
    print("  broad one (\"give me an overview\").")

    print("\nWHAT TO REMEMBER")
    print("- Pure relevance can produce an echo; MMR prefers a fan.")
    print("- A lambda slider arbitrates relevance against diversity, by the kind of question.")
    print("- What remains is combining it all: retrieval, re-ranking and MMR (Lab 20-5).")


if __name__ == "__main__":
    main()
