# -*- coding: utf-8 -*-
"""
Lab 4-4 — Hybrid search: merging the lexicon and the meaning

Learning objective
------------------
Understand why so many RAG systems combine a lexical engine and a semantic one,
rather than choosing between them.

The lab uses Reciprocal Rank Fusion (RRF):

    score(doc) = sum over each ranking of 1 / (k + rank)

The message to take away:

    The lexical catches the exact terms.
    The semantic catches the paraphrases.
    The fusion rewards the documents ranked well *in several engines at once*.

A note on robustness
--------------------
RRF depends on a parameter k. When k is large — 60, say — the gaps between
neighbouring ranks are flattened: a document ranked first in a single engine can
then beat one ranked second everywhere. To make the lesson "the consensus rises"
clear and reproducible, this lab uses a corpus where the consensus document is
plainly well ranked in both engines, and it shows the effect of k explicitly.
"""

from typing import Dict, List, Tuple


DOCUMENTS: Dict[str, str] = {
    "Doc_A": "VPN security guide: general reminders and good practice.",
    "Doc_B": "Detailed configuration of a Virtual Private Network for staff.",
    "Doc_C": "VPN procedure: configuring the Virtual Private Network on a Windows machine.",
    "Doc_D": "Requesting leave through the HR portal.",
}


# A simulated ranking from a lexical engine.
# It likes the exact acronym "VPN": Doc_C and Doc_A carry it in plain sight.
RANKING_LEXICAL: List[str] = ["Doc_C", "Doc_A", "Doc_B", "Doc_D"]

# A simulated ranking from a semantic engine.
# It likes the sense "Virtual Private Network": Doc_B and Doc_C spell it out.
RANKING_SEMANTIC: List[str] = ["Doc_B", "Doc_C", "Doc_A", "Doc_D"]

# Doc_C is the only document strong in BOTH engines: first lexically, second
# semantically. It is the one the fusion must bring out — the consensus document.


def reciprocal_rank_fusion(
    rankings: List[List[str]], k: int = 60
) -> List[Tuple[str, float]]:
    """Merge several rankings by Reciprocal Rank Fusion.

    Each document earns 1/(k + rank) for every ranking in which it appears. A
    smaller rank, meaning a better position, is worth more points.
    """
    if k <= 0:
        raise ValueError("The parameter k must be strictly positive.")

    scores: Dict[str, float] = {}

    for ranking in rankings:
        for rank, doc_id in enumerate(ranking, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)

    return sorted(scores.items(), key=lambda item: item[1], reverse=True)


def show_ranking(title: str, ranking: List[str]) -> None:
    """Print a readable ranking, guarding against unknown identifiers."""
    print("\n" + title)
    print("-" * 78)

    for rank, doc_id in enumerate(ranking, start=1):
        text = DOCUMENTS.get(doc_id, "(unknown document)")
        print(f"#{rank} | {doc_id} | {text}")


def show_fusion(title: str, fused: List[Tuple[str, float]]) -> None:
    """Print a merged ranking, with the RRF scores."""
    print("\n" + title)
    print("-" * 78)

    for rank, (doc_id, score) in enumerate(fused, start=1):
        text = DOCUMENTS.get(doc_id, "(unknown document)")
        print(f"#{rank} | {doc_id} | RRF score = {score:.5f} | {text}")


def main() -> None:
    print("=" * 78)
    print("Lab 4-4 — Hybrid search with RRF")
    print("=" * 78)

    print("\nQuery: How do I configure the VPN?")

    show_ranking("Simulated lexical ranking", RANKING_LEXICAL)
    show_ranking("Simulated semantic ranking", RANKING_SEMANTIC)

    # ---------------------------------------------------------------------
    # 1. The default fusion (k = 60, the usual value in the literature)
    # ---------------------------------------------------------------------
    fused = reciprocal_rank_fusion([RANKING_LEXICAL, RANKING_SEMANTIC], k=60)
    show_fusion("Hybrid ranking after RRF (k = 60)", fused)

    best_id = fused[0][0]

    print("\nINTERPRETATION")
    print("- Doc_A and Doc_C are strong lexically: the acronym VPN appears in them.")
    print("- Doc_B and Doc_C are strong semantically: Virtual Private Network is spelled out.")
    print("- Doc_C is the only document ranked well in BOTH engines.")
    print(f"- The fusion brings it out on top: winner = {best_id}.")

    if best_id == "Doc_C":
        print("  The expected result: the consensus document rises to the top.")
    else:
        print("  An unexpected result: check the input rankings.")

    # ---------------------------------------------------------------------
    # 2. The effect of the parameter k (a teaching note)
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("THE EFFECT OF THE PARAMETER k")
    print("=" * 78)
    print("k controls how far the gaps between neighbouring ranks are flattened:")
    print("- small k : the top places weigh very heavily (a sharp fusion).")
    print("- large k : the scores tighten up (a soft fusion, more consensual).")
    print()
    print(f"{'k':>4} | merged ranking (best to worst)")
    print("-" * 78)

    for k in (1, 10, 60, 1000):
        ranked_ids = [doc_id for doc_id, _ in
                      reciprocal_rank_fusion([RANKING_LEXICAL, RANKING_SEMANTIC], k=k)]
        print(f"{k:>4} | {' > '.join(ranked_ids)}")

    print()
    print("Here Doc_C stays on top for every value of k: the consensus is robust.")
    print("That is exactly what you expect of a good hybrid document.")

    print("\nWHAT TO REMEMBER")
    print("Hybrid search combines lexical precision with semantic proximity.")
    print("RRF rewards documents ranked well in several engines at once,")
    print("but its behaviour depends on k: tune it to the level of consensus you want.")


if __name__ == "__main__":
    main()
