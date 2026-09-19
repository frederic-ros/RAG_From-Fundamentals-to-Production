# -*- coding: utf-8 -*-
"""
Lab 3-5 — Tracing a RAG execution end to end

Learning objective
------------------
This lab builds a minimal execution trace.

Without a trace, a RAG answer is hard to diagnose:

  - which question was received?
  - which documents were candidates?
  - which scores were computed?
  - which context was injected?
  - which answer was produced?

The lab introduces a minimal observability of the pipeline.

Note on what you will see: with this deliberately naive lexical score, the three
documents all come out at zero, and the system refuses to answer. That refusal
is the point. The trace is what lets you see WHY it refused — the question says
"visitor" and "register" where the document says "visitors" and "registered".
Without the trace, the refusal would look like a mystery.
"""

from typing import Dict, Any
import json


DOCUMENTS = [
    {"id": "doc-1", "text": "Visitors must be registered at reception."},
    {"id": "doc-2", "text": "VPN access expires after 90 days."},
    {"id": "doc-3", "text": "Permanent badges are reserved for employees."},
]


def tokenize(text: str) -> set:
    """A very simple tokenisation."""
    return set(text.lower().replace(".", "").replace("?", "").replace("'", " ").split())


def score_document(question: str, document: Dict[str, str]) -> int:
    """An elementary lexical score.

    NOTE: as in Chapter 1, this score counts only the words that match exactly.
    It exists here to make the trace readable, not to be robust: a synonym, or a
    plural that is not shared, drops the score to zero — hence the "score == 0"
    guard below, which triggers an explicit refusal.
    """
    return len(tokenize(question) & tokenize(document["text"]))


def run_rag_with_trace(question: str) -> Dict[str, Any]:
    """Run a mini RAG and return a complete trace."""
    trace: Dict[str, Any] = {
        "question": question,
        "candidates": [],
        "selected_context": None,
        "prompt": None,
        "answer": None,
    }

    for doc in DOCUMENTS:
        score = score_document(question, doc)
        trace["candidates"].append(
            {
                "id": doc["id"],
                "score": score,
                "text": doc["text"],
            }
        )

    ranked = sorted(trace["candidates"], key=lambda item: item["score"], reverse=True)
    selected = ranked[0]
    trace["selected_context"] = selected

    trace["prompt"] = (
        "Answer only from the context.\n\n"
        f"Context: {selected['text']}\n"
        f"Question: {question}\n"
        "Answer:"
    )

    if selected["score"] == 0:
        trace["answer"] = "I do not know from the context provided."
    else:
        trace["answer"] = f"According to the context: {selected['text']}"

    return trace


def show_trace(trace: Dict[str, Any]) -> None:
    """Print the trace in a readable way."""
    print("=" * 78)
    print("RAG EXECUTION TRACE")
    print("=" * 78)

    print("\nQUESTION")
    print(trace["question"])

    print("\nCANDIDATE DOCUMENTS")
    for candidate in trace["candidates"]:
        print(
            f"- {candidate['id']} | score={candidate['score']} | {candidate['text']}"
        )

    print("\nSELECTED CONTEXT")
    selected = trace["selected_context"]
    print(f"{selected['id']} | score={selected['score']} | {selected['text']}")

    print("\nPROMPT")
    print(trace["prompt"])

    print("\nANSWER")
    print(trace["answer"])


def main() -> None:
    question = "How do I register a visitor?"
    trace = run_rag_with_trace(question)
    show_trace(trace)

    print("\nTHE TRACE AS JSON")
    print("-" * 78)
    print(json.dumps(trace, ensure_ascii=False, indent=2))

    print("\nWHAT TO REMEMBER")
    print("- A trace makes the answer explainable.")
    print("- Scores and candidate documents help diagnose the retrieval.")
    print("- In production, observability is a condition of trust.")


if __name__ == "__main__":
    main()
