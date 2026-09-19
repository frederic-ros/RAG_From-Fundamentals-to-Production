# -*- coding: utf-8 -*-
"""
Lab 3-2 — Diagnosing bad answers

Learning objective
------------------
This lab trains you to locate a failure in a RAG system.

Faced with a bad answer, the common reflex is to blame the LLM. But the error
can come from:

  - the documents;
  - the preparation;
  - the indexing;
  - the retrieval;
  - the augmentation;
  - the generation;
  - the domain calibration.

The lab offers fictional cases and produces a diagnosis for each.
"""

from typing import Dict, List


CASES: List[Dict[str, str]] = [
    {
        "case": "An old procedure",
        "symptom": "The assistant cites a 2021 procedure although a 2024 version exists.",
        "expected_zone": "domain calibration",
        "reason": "The system did not know to prefer the recent, official document.",
    },
    {
        "case": "An off-topic answer",
        "symptom": "The question is about visitor badges, but the context speaks of employee badges.",
        "expected_zone": "retrieval",
        "reason": "The passages retrieved do not match the intent exactly.",
    },
    {
        "case": "Unreadable text",
        "symptom": "The answer contains fragments of severed sentences, taken from a PDF.",
        "expected_zone": "preparation",
        "reason": "The extraction or the cutting of the document degraded the content.",
    },
    {
        "case": "Good source, poor synthesis",
        "symptom": "The right regulation is in the context, but the answer reverses the rule.",
        "expected_zone": "generation",
        "reason": "The model misread or badly summarised the context.",
    },
    {
        "case": "Sources mixed together",
        "symptom": "The answer combines two contradictory documents without flagging it.",
        "expected_zone": "augmentation",
        "reason": "The prompt does not separate the sources or their status clearly enough.",
    },
]


def print_case(case: Dict[str, str], index: int) -> None:
    """Print one case and its diagnosis."""
    print("\n" + "=" * 78)
    print(f"CASE {index} — {case['case']}")
    print("=" * 78)
    print(f"Symptom       : {case['symptom']}")
    print(f"Probable zone : {case['expected_zone']}")
    print(f"Reasoning     : {case['reason']}")


def main() -> None:
    print("=" * 78)
    print("Lab 3-2 — Diagnosing bad answers")
    print("=" * 78)

    for i, case in enumerate(CASES, start=1):
        print_case(case, i)

    print("\nWHAT TO REMEMBER")
    print("- An error in an answer is not always a hallucination of the LLM.")
    print("- The diagnosis has to locate the faulty zone in the chain.")
    print("- Domain calibration handles the errors similarity cannot see.")


if __name__ == "__main__":
    main()
