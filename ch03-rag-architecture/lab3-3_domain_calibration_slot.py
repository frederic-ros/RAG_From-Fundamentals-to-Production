# -*- coding: utf-8 -*-
"""
Lab 3-3 — Adding a "domain calibration" slot

Learning objective
------------------
This lab shows why the most similar-looking document is not always the best one
to use.

Two rankings are compared:

  1. a ranking by textual similarity alone;
  2. a ranking enriched by business signals: authority, freshness, validity,
     criticality.

The lab runs with no API key.
"""

from typing import Dict, List


DOCUMENTS: List[Dict[str, object]] = [
    {
        "id": "A",
        "title": "Old internal FAQ",
        "text_similarity": 0.92,
        "official": False,
        "year": 2021,
        "valid": False,
        "criticality": 1,
    },
    {
        "id": "B",
        "title": "Recent official procedure",
        "text_similarity": 0.78,
        "official": True,
        "year": 2024,
        "valid": True,
        "criticality": 3,
    },
    {
        "id": "C",
        "title": "Training note",
        "text_similarity": 0.84,
        "official": False,
        "year": 2023,
        "valid": True,
        "criticality": 1,
    },
    {
        "id": "D",
        "title": "Regulatory archive",
        "text_similarity": 0.88,
        "official": True,
        "year": 2019,
        "valid": False,
        "criticality": 2,
    },
]


def business_score(doc: Dict[str, object]) -> float:
    """Compute a simple business score.

    The score is not universal: it exists to make the idea of calibration
    visible.
    """
    score = float(doc["text_similarity"])

    if doc["official"]:
        score += 0.20

    if doc["valid"]:
        score += 0.25
    else:
        score -= 0.40

    freshness = (int(doc["year"]) - 2019) / (2024 - 2019)
    score += 0.15 * freshness

    score += 0.05 * int(doc["criticality"])

    return score


def show_ranking(title: str, key_function) -> None:
    """Print one ranking of the documents."""
    print("\n" + title)
    print("-" * 78)

    ranked = sorted(DOCUMENTS, key=key_function, reverse=True)

    for rank, doc in enumerate(ranked, start=1):
        print(
            f"#{rank} | {doc['id']} | {doc['title']:<28s} "
            f"| similarity={doc['text_similarity']:.2f} "
            f"| score={key_function(doc):.2f} "
            f"| official={doc['official']} | valid={doc['valid']} | year={doc['year']}"
        )


def main() -> None:
    print("=" * 78)
    print("Lab 3-3 — Adding a \"domain calibration\" slot")
    print("=" * 78)

    show_ranking(
        "Ranking 1 — textual similarity alone",
        key_function=lambda doc: float(doc["text_similarity"]),
    )

    show_ranking(
        "Ranking 2 — similarity plus domain calibration",
        key_function=business_score,
    )

    print("\nA RETENIR")
    print("- The most similar document is not always the one that carries authority.")
    print("- Authority, validity and freshness must be represented explicitly.")
    print("- Domain calibration completes the retrieval; it does not replace it.")


if __name__ == "__main__":
    main()
