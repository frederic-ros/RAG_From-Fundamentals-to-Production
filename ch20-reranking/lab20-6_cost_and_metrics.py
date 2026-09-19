# -*- coding: utf-8 -*-
"""
Lab 20-6 (BONUS) — Measuring the gain and its cost (MRR, nDCG)

Learning objective
------------------
Does re-ranking REALLY improve the top of the list, and at what price? The
chapter poses this as a skill: prove the gain, do not assume it. This lab
measures, over the whole set of annotated queries:

  - the rank of the first good document, before and after re-ranking;
  - two standard metrics:
      * MRR (Mean Reciprocal Rank): rewards the position of the FIRST good doc;
      * nDCG@k: rewards the good docs AND their place near the top;
  - the cost, in calls to the cross-encoder.

    Re-ranking has a cost, but it is justified by the gain in quality.

What comes out is a "before and after" table that puts a figure on the
gain-to-effort ratio — often one of the best in the whole pipeline.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import reranklib as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 20-6 (BONUS) — Measuring the gain and its cost (MRR, nDCG)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    queries = data["queries"]
    print(f"\nModel mode: {R.mode()}")
    print(f"{len(queries)} annotated queries, each with its relevant fragments.")

    bi = R.BiEncoder(texts)
    cross = R.CrossEncoder()
    N = 10  # the pool that gets re-ranked

    mrr_av, mrr_ap = [], []
    ndcg_av, ndcg_ap = [], []
    total_calls = 0

    print("\n" + "=" * 78)
    print("RANK OF THE FIRST GOOD DOCUMENT, BEFORE AND AFTER RE-RANKING")
    print("=" * 78)
    print(f"  {'query':<42s} | {'before':>6s} | {'after':>6s}")
    print("  " + "-" * 62)

    for req in queries:
        q = req["question"]
        relevant = req["relevant"]

        # Before: ranking produced by the bi-encoder.
        cl_bi = bi.rank(q)
        ordre_av = [i for i, _ in cl_bi]

        # After : re-ranking of the pool N firsts.
        pool = ordre_av[:N]
        cross.last_calls = 0
        cl_cross = cross.rerank(q, [(i, texts[i]) for i in pool])
        total_calls += cross.last_calls
        ordre_ap = [i for i, _ in cl_cross] + [i for i in ordre_av if i not in pool]

        mrr_av.append(R.mrr(ordre_av, relevant))
        mrr_ap.append(R.mrr(ordre_ap, relevant))
        ndcg_av.append(R.ndcg(ordre_av, relevant, k=5))
        ndcg_ap.append(R.ndcg(ordre_ap, relevant, k=5))

        r_av = R.rank_of(ordre_av, req["best"])
        r_ap = R.rank_of(ordre_ap, req["best"])
        print(f"  {q[:40]:<42s} | {str(r_av):>6s} | {str(r_ap):>6s}")

    def moy(xs):
        return sum(xs) / len(xs)

    print("\n" + "=" * 78)
    print("OVERALL METRICS (averaged over the queries)")
    print("=" * 78)
    print(f"  {'metric':<12s} | {'before':>8s} | {'after':>8s} | {'gain':>8s}")
    print("  " + "-" * 46)
    print(f"  {'MRR':<12s} | {moy(mrr_av):8.3f} | {moy(mrr_ap):8.3f} | "
          f"{moy(mrr_ap)-moy(mrr_av):+8.3f}")
    print(f"  {'nDCG@5':<12s} | {moy(ndcg_av):8.3f} | {moy(ndcg_ap):8.3f} | "
          f"{moy(ndcg_ap)-moy(ndcg_av):+8.3f}")

    print("\n" + "=" * 78)
    print("THE COST SET AGAINST THE GAIN")
    print("=" * 78)
    print(f"  Appels au cross-encodeur (total)   : {total_calls} "
          f"(about {total_calls/len(queries):.0f} per query).")
    print("  Compare with the bi-encoder: 0 expensive calls, the vectors are precomputed.")
    # An illustration with a fictional monetary cost, for order of magnitude.
    unit_cost = 0.0001  # $ by appel (exemple)
    print(f"  Indicative cost (at ${unit_cost}/call): "
          f"${total_calls*unit_cost:.4f} for {len(queries)} queries.")
    print("  -> Re-ranking is NOT free, but its cost stays bounded to the pool, and it")
    print("     buys a measurable gain in quality (the MRR and nDCG above).")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The gain of re-ranking is not ASSUMED: it is MEASURED (MRR and nDCG, before/after).")
    print("- The cost is counted in calls to the cross-encoder, proportional to the size of the")
    print("  pool — not of the corpus. That is what makes re-ranking affordable.")
    print("- The gain-to-effort ratio is often one of the best in the whole pipeline.")

    print("\nWHAT TO REMEMBER")
    print("- MRR measures the position of the first good document; nDCG, the quality of the top.")
    print("- Measuring before and after is the only way to justify re-ranking, or not.")
    print("- The cost is bounded to the candidate pool: an investment, not a pit.")


if __name__ == "__main__":
    main()
