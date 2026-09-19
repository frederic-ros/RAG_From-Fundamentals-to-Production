# -*- coding: utf-8 -*-
"""
Lab 3-4 — Before the question, and at the moment of the question

Learning objective
------------------
This lab distinguishes two timescales inside a RAG system:

  1. The offline phase: preparation, chunking, indexing. It happens before any
     question is asked.

  2. The online phase: receiving the question, retrieval, augmentation,
     generation. It is replayed at every query.

Understanding that separation is essential for reasoning about costs,
performance and errors.
"""

from typing import List, Dict


RAW_DOCUMENTS = [
    "Badge procedure: visitors must be registered at reception.",
    "Network procedure: VPN access expires after 90 days.",
    "Equipment procedure: any computer loan must be approved by a manager.",
]


INDEX: List[Dict[str, object]] = []


def offline_indexation(raw_documents: List[str]) -> None:
    """Prepare and index the documents, before any question."""
    print("=" * 78)
    print("THE OFFLINE PHASE — BEFORE THE QUESTIONS")
    print("=" * 78)

    for i, text in enumerate(raw_documents, start=1):
        chunk = text.strip()
        indexed_item = {
            "id": f"chunk-{i}",
            "text": chunk,
            "tokens": set(chunk.lower().replace(":", "").replace(".", "").split()),
        }
        INDEX.append(indexed_item)

        print(f"Indexed: {indexed_item['id']} -> {indexed_item['text']}")

    print("\nThe index is built once. It will serve many questions.")


def online_query(question: str) -> None:
    """Handle a user question, at query time."""
    print("\n" + "=" * 78)
    print("THE ONLINE PHASE — AT THE WHEN OF THE QUESTION")
    print("=" * 78)

    print(f"Question: {question}")

    q_tokens = set(question.lower().replace("?", "").replace("-", " ").split())

    # NOTE: the retrieval here rests on shared keywords, an intersection of
    # tokens. So that the demonstration of the two timescales stays readable,
    # the questions deliberately share the vocabulary of the documents. A single
    # absent word — "visitor" in the singular against "visitors" — would be
    # enough to make this matching fail. That is the lexical limit seen in
    # Chapter 1, and the embeddings of Chapter 4 will lift it.
    if not INDEX:
        print("The index is empty: no answer is possible. Did you run the indexing?")
        return

    scored = []
    for item in INDEX:
        score = len(q_tokens & item["tokens"])
        scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    best_score, best_item = scored[0]

    print(f"Retrieval: {best_item['id']} with score {best_score}")
    print(f"Context  : {best_item['text']}")

    prompt = f"Context: {best_item['text']}\nQuestion: {question}\nAnswer:"
    print(f"Augmented prompt:\n{prompt}")

    print(f"Simulated answer: According to the context, {best_item['text']}")


def main() -> None:
    offline_indexation(RAW_DOCUMENTS)

    online_query("Where must visitors be registered?")
    online_query("How long does VPN access last?")

    print("\nWHAT TO REMEMBER")
    print("- Indexing builds the memory before the questions.")
    print("- Retrieval and generation are replayed at every question.")
    print("- An offline error can propagate to every future answer.")


if __name__ == "__main__":
    main()
