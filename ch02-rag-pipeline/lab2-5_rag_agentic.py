# -*- coding: utf-8 -*-
"""
Lab 2-5 — From linear RAG to agentic RAG

Learning objective
------------------
This lab simulates a multi-step RAG.

In a linear RAG:
    one question -> one retrieval -> one answer

In an agentic RAG:
    one question -> a retrieval -> a reading -> a new question
                 -> a new retrieval -> ...

The program produces a trace of the resolution.
"""

from typing import Dict, List


ENVELOPES: Dict[str, str] = {
    "profile": "X is an external contractor assigned to the Alpha site.",
    "regulations": "Contractors may request a temporary badge if a site manager "
                   "approves the request.",
    "calendar": "This Friday is a working day. The building closes at 8 pm.",
    "history": "X has already requested two temporary badges, all returned on time.",
    "org_chart": "The manager of the Alpha site is Sophie Martin.",
}


def retrieve_envelope(question: str) -> str:
    """Pick the envelope to open, given the current question.

    This function simulates an agent's decision.

    NOTE — deliberately naive: the routing rests on plain keywords, a substring
    search. That is exactly the lexical limit seen in Chapter 1: "approves" is
    recognised because it contains "approve", but an unforeseen synonym
    ("authorise", "sign off") would trigger nothing. Making this routing robust,
    through embeddings or through an LLM, is precisely the subject of the
    chapters that follow.
    """
    q = question.lower()

    if "status" in q or "who is x" in q:
        return "profile"
    if "rule" in q or "contractor" in q:
        return "regulations"
    if "friday" in q or "evening" in q:
        return "calendar"
    if "history" in q or "reliable" in q:
        return "history"
    if "manager" in q or "approve" in q:
        return "org_chart"

    return "profile"


def solve_case() -> List[str]:
    """Produce a multi-step resolution trace."""
    trace = []

    question = "Is employee X entitled to request a badge this Friday evening?"
    trace.append(f"Initial question: {question}")

    question = "What is the status of X?"
    envelope = retrieve_envelope(question)
    info = ENVELOPES[envelope]
    trace.append(f"Retrieval 1 -> envelope '{envelope}'")
    trace.append(f"Reading     -> {info}")

    question = "What are the rules for an external contractor?"
    envelope = retrieve_envelope(question)
    info = ENVELOPES[envelope]
    trace.append(f"New question -> {question}")
    trace.append(f"Retrieval 2  -> envelope '{envelope}'")
    trace.append(f"Reading      -> {info}")

    question = "Is this Friday evening compatible with the building's hours?"
    envelope = retrieve_envelope(question)
    info = ENVELOPES[envelope]
    trace.append(f"New question -> {question}")
    trace.append(f"Retrieval 3  -> envelope '{envelope}'")
    trace.append(f"Reading      -> {info}")

    question = "Who must approve the request?"
    envelope = retrieve_envelope(question)
    info = ENVELOPES[envelope]
    trace.append(f"New question -> {question}")
    trace.append(f"Retrieval 4  -> envelope '{envelope}'")
    trace.append(f"Reading      -> {info}")

    # NOTE: this conclusion is hard-coded, to stay readable. If you change an
    # envelope — "working day" to "public holiday", say — the script does not
    # recompute the conclusion: rewriting it is up to you. Making the conclusion
    # depend on the information read is a good extension exercise, and the
    # starting point of real agentic reasoning.
    trace.append(
        "Conclusion -> X may request a temporary badge this Friday, but the "
        "request must be approved by Sophie Martin."
    )

    return trace


def main() -> None:
    print("=" * 78)
    print("Lab 2-5 — From linear RAG to agentic RAG")
    print("=" * 78)

    trace = solve_case()

    print("\nTHE RESOLUTION TRACE")
    print("-" * 78)
    for step in trace:
        print(step)

    print("\nWHAT TO REMEMBER")
    print("- An agent does not always retrieve every document in one go.")
    print("- Each reading can produce a new question.")
    print("- The trace makes the loop visible: question -> retrieval -> reading -> question.")


if __name__ == "__main__":
    main()
