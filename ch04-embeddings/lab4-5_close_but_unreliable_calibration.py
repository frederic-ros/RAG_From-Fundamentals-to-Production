# -*- coding: utf-8 -*-
"""
Lab 4-5 — Close does not mean reliable: filtering and business scores

Learning objective
------------------
Show that a high semantic score is not always enough.

A document can be very close to the question and yet be:

  - out of date;
  - unofficial;
  - less reliable than an approved procedure.

The message to take away:

    Similarity is not authority.
    Proximity is not applicability.
"""

from typing import Callable, Dict, List


DOCUMENTS: List[Dict[str, object]] = [
    {
        "id": "Doc_Old_2022",
        "title": "Practical guide to meal reimbursements — 2022 edition",
        "sem_score": 0.93,
        "year": 2022,
        "official": True,
        "status": "obsolete",
    },
    {
        "id": "Doc_Official_2024",
        "title": "Official HR directive — reimbursement of travel expenses 2024",
        "sem_score": 0.89,
        "year": 2024,
        "official": True,
        "status": "in_force",
    },
    {
        "id": "Doc_Internal_Blog",
        "title": "Internal post — tips for getting reimbursed quickly",
        "sem_score": 0.85,
        "year": 2025,
        "official": False,
        "status": "informal",
    },
]

# Weights for the validity status. Centralised, to stay readable and tunable.
STATUS_SCORE: Dict[str, float] = {
    "in_force": 1.0,
    "informal": 0.3,
    "obsolete": 0.1,
}


def metadata_score(doc: Dict[str, object]) -> float:
    """A simple business score, normalised to [0, 1]: validity, authority, freshness."""
    score = 0.0

    # Validity: a known status, otherwise a cautious neutral value.
    score += STATUS_SCORE.get(str(doc["status"]), 0.3)

    # Authority.
    score += 1.0 if bool(doc["official"]) else 0.0

    # A simple freshness.
    year = int(doc["year"])  # type: ignore[arg-type]
    if year >= 2024:
        score += 1.0
    elif year == 2023:
        score += 0.6
    else:
        score += 0.2

    # Normalised over the 3 criteria.
    return score / 3.0


def calibrated_score(doc: Dict[str, object], weight_semantic: float = 0.65) -> float:
    """Combine the semantic similarity and the business score.

    weight_semantic lies in [0, 1]; the business weight is its complement.
    """
    if not 0.0 <= weight_semantic <= 1.0:
        raise ValueError("weight_semantic must lie in [0, 1].")
    weight_metadata = 1.0 - weight_semantic
    return weight_semantic * float(doc["sem_score"]) + weight_metadata * metadata_score(doc)


def show_ranking(
    title: str, key_function: Callable[[Dict[str, object]], float]
) -> List[Dict[str, object]]:
    """Print a ranking, sorted by the score function supplied."""
    print("\n" + title)
    print("-" * 78)

    ranked = sorted(DOCUMENTS, key=key_function, reverse=True)

    for rank, doc in enumerate(ranked, start=1):
        print(
            f"#{rank} | {str(doc['id']):18s} | "
            f"sem={float(doc['sem_score']):.2f} | "
            f"business={metadata_score(doc):.2f} | "
            f"final={calibrated_score(doc):.2f} | "
            f"{doc['title']}"
        )

    return ranked


def main() -> None:
    print("=" * 78)
    print("Lab 4-5 — Close does not mean reliable")
    print("=" * 78)

    print("\nQuestion: What is the current rule for expense reimbursement?")

    ranking_semantic = show_ranking(
        "1. Ranking by pure semantic similarity",
        key_function=lambda doc: float(doc["sem_score"]),
    )

    print("\nObservation: the 2022 document, obsolete though it is, comes first.")

    ranking_calibrated = show_ranking(
        "2. Ranking after domain calibration",
        key_function=calibrated_score,
    )

    best_before = ranking_semantic[0]["id"]
    best_after = ranking_calibrated[0]["id"]

    print("\nINTERPRETATION")
    print(f"Before calibration: {best_before}")
    print(f"After calibration : {best_after}")

    if best_before == "Doc_Old_2022" and best_after == "Doc_Official_2024":
        print("The expected result: calibration corrects the choice of document.")
    else:
        print("An unexpected result: check the weightings.")

    print("\nWHAT TO REMEMBER")
    print("- Semantic similarity finds texts that are close.")
    print("- On its own it cannot tell which document is valid or official.")
    print("- Business metadata turns a neighbourhood into a decision you can act on.")


if __name__ == "__main__":
    main()
