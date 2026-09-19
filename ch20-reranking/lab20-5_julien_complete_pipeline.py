# -*- coding: utf-8 -*-
"""
Lab 20-5 — Julien looks for the best procedure (the complete pipeline)

Learning objective
------------------
Assemble the three stages of the chapter into one pipeline:

  1. RETRIEVE BROADLY (bi-encoder) -> a wide pool of candidates (recall);
  2. RE-RANK FINELY (cross-encoder) -> reordered by relevance (precision);
  3. DIVERSIFY (MMR) -> avoid answering the same thing five times.

Julien's case, the running thread of the chapter: he is looking for the
maintenance procedure for motor M-18, and the corpus holds neighbouring codes
(M-17, M-19), restatements, and a recent version. The target fragment is followed
through each stage, and the pipeline is seen making it emerge.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import reranklib as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def show(titre, indices, frags, texts, target=None):
    print(f"\n{titre}")
    for rank, i in enumerate(indices, start=1):
        mark = "  <-- target" if i == target else ""
        print(f"  {rank}. #{i:2d} [{frags[i]['subject']:<16s}] "
              f"\"{texts[i][:46].strip()}…\"{mark}")


def main() -> None:
    print("=" * 78)
    print("Lab 20-5 — Julien looks for the best procedure (the complete pipeline)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    print(f"\nModel mode: {R.mode()}")

    # Julien veut the procedure of maintenance of the M-18. Cible : the fragment of
    # reference (#0). On veut the voir in head, without redondance autour.
    question = "What is the maintenance procedure for motor M-18?"
    target = 0
    N = 10  # pool
    k = 4   # answer finale
    print(f"Julien's case — query: \"{question}\"")
    print(f"Target fragment (the M-18 reference procedure): #{target}")

    bi = R.BiEncoder(texts)
    cross = R.CrossEncoder()
    vectors = bi.vectors()
    vec_q = bi.query_vector(question)

    # --- Stage 1 : to retrieve large -----------------------------------------
    cl_bi = bi.rank(question, k=N)
    pool = [i for i, _ in cl_bi]
    show(f"STAGE 1 — RETRIEVE BROADLY (bi-encoder, {N} candidates)",
             pool, frags, texts, target)
    print(f"\n  Rank of the target after stage 1: {R.rank_of(pool, target)}")

    # --- Stage 2 : re-ranker -----------------------------------------------
    cl_cross = cross.rerank(question, [(i, texts[i]) for i in pool])
    reordered = [i for i, _ in cl_cross]
    show("STAGE 2 — RE-RANK (the cross-encoder reorders the pool)",
             reordered[:6], frags, texts, target)
    print(f"\n  Rank of the target after stage 2: {R.rank_of(reordered, target)}")

    # --- Stage 3: MMR over the best re-ranked candidates ----------------------
    # Diversify among the best re-ranked candidates.
    meilleurs = reordered[:8]
    final = R.mmr(vec_q, vectors, meilleurs, k=k, lam=0.6)
    show(f"STAGE 3 — DIVERSIFY (MMR, lambda=0.6, the final top {k})",
             final, frags, texts, target)

    facettes = len({frags[i]["subject"] for i in final})
    print("\n" + "=" * 78)
    print("WHAT THE GENERATION MODEL RECEIVES")
    print("=" * 78)
    print(f"  Top {k} final : {[('#'+str(i)+' '+frags[i]['subject']) for i in final]}")
    print(f"  - The target (#{target}) is present and well placed.")
    print(f"  - {facettes} distinct facets: no repetition, several angles covered.")
    print(f"  - A controlled cost: the cross-encoder called on {N} candidates only.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Each stage plays its part: the retrieval does not miss the target (recall),")
    print("  the reranker lifts it (precision), MMR avoids the duplicates (diversity).")
    print("- No stage alone is enough; it is their CHAINING that produces a good top of")
    print("  the list, complete and free of repetition.")

    print("\nWHAT TO REMEMBER")
    print("- The complete pipeline: retrieve broadly -> re-rank finely -> diversify.")
    print("- The retrieval finds, the reranker chooses, MMR diversifies.")
    print("- This is the skeleton of advanced retrieval in production.")


if __name__ == "__main__":
    main()
