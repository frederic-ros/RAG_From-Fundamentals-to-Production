# -*- coding: utf-8 -*-
"""
Lab 20-3 — The two-stage pipeline (retrieve broadly, then refine)

Learning objective
------------------
The cross-encoder cannot be applied to the whole corpus: too expensive. The
bi-encoder alone will not do either: too coarse at the top. The solution is not
to choose between them, but to CHAIN them.

    [Query] -> bi-encoder (retrieves broadly, recall) -> N candidates
            -> cross-encoder (refines, precision) -> top k
            -> the generation model

    Precision comes after recall.

This lab builds the complete pipeline and measures the movement of the right
fragment: relegated by the bi-encoder, it rises to the top after re-ranking —
without having paid for a cross-encoder over the whole corpus, only over the
candidates.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import reranklib as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 20-3 — The two-stage pipeline")
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
    N = 12  # a wide pool: enough to catch the right fragment despite its initial rank
    k = 3   # the final number sent to the model
    print(f"Query: \"{question}\"   (the right fragment: #{best})")
    print(f"Setting: retrieve {N} candidates, re-rank them, keep the top {k}.")

    bi = R.BiEncoder(texts)
    cross = R.CrossEncoder()

    # --- Stage 1: retrieve broadly (recall) -----------------------------------
    cl_bi = bi.rank(question, k=N)
    pool = [i for i, _ in cl_bi]
    initial_rank = R.rank_of(pool, best)

    print("\n" + "=" * 78)
    print(f"STAGE 1 — RETRIEVE BROADLY (bi-encoder, {N} candidates, aiming at RECALL)")
    print("=" * 78)
    for rank, (i, s) in enumerate(cl_bi, start=1):
        mark = "  <-- the right one" if i == best else ""
        print(f"  rank {rank:2d}: #{i:2d} [{frags[i]['subject']}]{mark}")
    print(f"\n  The right fragment is in the pool, at rank {initial_rank}.")
    print("  What matters at this stage: NOT MISSING IT. The precise order can wait.")

    # --- Stage 2: refine (precision) ------------------------------------------
    cross.last_calls = 0
    cl_cross = cross.rerank(question, [(i, texts[i]) for i in pool])
    calls = cross.last_calls
    top_final = [i for i, _ in cl_cross[:k]]

    print("\n" + "=" * 78)
    print(f"STAGE 2 — REFINE (cross-encoder, {calls} pairs re-read, aiming at PRECISION)")
    print("=" * 78)
    for rank, (i, s) in enumerate(cl_cross[:k], start=1):
        print(f"  rank {rank:2d}: #{i:2d} [{frags[i]['subject']}]  score {s:.3f}")

    # Measure the precision at the top: the share of the RIGHT subject (M-18)
    # in the top k.
    def is_right_subject(idx: int) -> bool:
        return frags[idx]["subject"].startswith("M-18")

    top_bi = pool[:k]
    bi_purity = sum(is_right_subject(i) for i in top_bi) / k
    cross_purity = sum(is_right_subject(i) for i in top_final) / k

    print("\n" + "=" * 78)
    print("THE GAIN — THE TOP OF THE LIST IS PURIFIED")
    print("=" * 78)
    print(f"  Top {k} after stage 1 (bi)   : "
          f"{[frags[i]['subject'] for i in top_bi]}")
    print(f"  Top {k} after stage 2 (cross): "
          f"{[frags[i]['subject'] for i in top_final]}")
    print("\n  Share of the right subject (M-18) at the top:")
    print(f"    - after the bi-encoder   : {bi_purity:.0%}  "
          f"(neighbouring codes M-17 and M-19 pollute the summit)")
    print(f"    - after the cross-encoder: {cross_purity:.0%}  "
          f"(the neighbouring codes have been driven out)")
    print(f"\n  The cost of re-ranking: {calls} calls to the cross-encoder, "
          f"not {len(frags)}, the whole corpus.")
    print("  -> The fine model was paid for on the candidates only, not on everything.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Stage 1: wide and fast, raking broadly so as to miss nothing (recall).")
    print("- Stage 2: narrow and fine, re-reading the survivors to order them well (precision).")
    print("- The generation model receives only the TRUE best, not the ones an")
    print("  approximate distance had hoisted up by accident.")

    print("\nWHAT TO REMEMBER")
    print("- The two-stage pipeline combines the best of both: recall, then precision.")
    print("- The cost of the cross-encoder stays bounded to the small pool of candidates.")
    print("- This is the standard architecture of modern retrieval in production.")


if __name__ == "__main__":
    main()
