# -*- coding: utf-8 -*-
"""
Lab 2-3 — A direct answer against a grounded one

Learning objective
------------------
This lab compares two behaviours:

  1. A direct answer, which leans on the model's supposed memory.
  2. A grounded answer, which leans only on the documents provided.

So as to stay runnable with no API key, the answers are simulated. The point is
to learn to read the differences: precision, caution, traceability, and the risk
of invention.
"""

from typing import Dict, List


QUESTION = "May a student borrow 15 books for a month?"

DOCUMENTS = [
    "A student may borrow up to 10 books.",
    "The normal borrowing period is 21 days.",
    "An extension may be requested if the book is not reserved.",
]


RESPONSES = {
    "direct": (
        "Yes, in many university libraries a student can borrow around 15 books "
        "for a month."
    ),
    "grounded": (
        "No. According to the documents, a student may borrow up to 10 books for "
        "a normal period of 21 days. An extension may be requested, but the "
        "documents do not say that an initial loan of 15 books for a month is "
        "allowed."
    ),
}


def evaluate_response(response: str, documents: List[str]) -> Dict[str, str]:
    """Produce a very simple qualitative evaluation."""
    cites_context = any(fragment in response for fragment in ["10 books", "21 days"])
    cautious = any(fragment in response.lower()
                   for fragment in ["do not say", "according to", "documents"])
    invents = "15 books for a month" in response and not cites_context

    return {
        "documentary grounding": "yes" if cites_context else "no",
        "caution": "yes" if cautious else "no",
        "risk of invention": "high" if invents else "low",
    }


def print_evaluation(name: str, response: str) -> None:
    """Print the answer and its diagnosis."""
    print("\n" + name.upper())
    print("-" * 78)
    print(response)

    evaluation = evaluate_response(response, DOCUMENTS)

    print("\nDiagnosis")
    for key, value in evaluation.items():
        print(f"- {key:22s}: {value}")


def main() -> None:
    print("=" * 78)
    print("Lab 2-3 — A direct answer against a grounded one")
    print("=" * 78)

    print("\nQUESTION")
    print(QUESTION)

    print("\nDOCUMENTS PROVIDED")
    for i, doc in enumerate(DOCUMENTS, start=1):
        print(f"[Document {i}] {doc}")

    print_evaluation("Direct answer", RESPONSES["direct"])
    print_evaluation("Grounded answer", RESPONSES["grounded"])

    print("\nWHAT TO REMEMBER")
    print("- A direct answer can be fluent and yet unverifiable.")
    print("- A grounded answer must stay within the perimeter of the documents.")
    print("- RAG serves to move the answer onto a controlled documentary base.")


if __name__ == "__main__":
    main()
