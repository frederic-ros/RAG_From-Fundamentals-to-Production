# -*- coding: utf-8 -*-
"""
Lab 2-1 — Assembling a first conceptual RAG: the anatomy

Learning objective
------------------
This lab rebuilds the complete chain of a minimal RAG:

    user question
      -> retrieval
      -> augmentation
      -> generation
      -> final answer

The program does not use an LLM yet. It simulates the generation, so as to make
the structure of the pipeline visible. The point is to understand the
architecture before adding more powerful models.
"""

from typing import List, Tuple


# =============================================================================
# 1. THE MINI CORPUS
# =============================================================================

DOCUMENTS = [
    {
        "id": "doc-1",
        "title": "Library opening hours",
        "text": "The library is open Monday to Friday, from 9 am to 6 pm.",
    },
    {
        "id": "doc-2",
        "title": "Borrowing conditions",
        "text": "A student may borrow up to 10 books for 21 days.",
    },
    {
        "id": "doc-3",
        "title": "Access to the study rooms",
        "text": "Study rooms are booked online, for a maximum of 2 hours.",
    },
]


# =============================================================================
# 2. A VERY SIMPLE RETRIEVAL
# =============================================================================

def tokenize(text: str) -> List[str]:
    """Split a text into lowercase words, very simply."""
    cleaned = (
        text.lower()
        .replace("'", " ")
        .replace(".", " ")
        .replace(",", " ")
        .replace("?", " ")
    )
    return [token for token in cleaned.split() if token]


def lexical_score(question: str, document_text: str) -> int:
    """Count the number of words shared by the question and the document."""
    q_words = set(tokenize(question))
    d_words = set(tokenize(document_text))
    return len(q_words & d_words)


def retrieve(question: str, documents: List[dict]) -> Tuple[dict, int]:
    """Return the document with the highest lexical score.

    If the corpus is empty, (None, 0) is returned rather than raising: a RAG
    pipeline must be able to say "no document" without crashing.
    """
    if not documents:
        return None, 0

    scored = []

    for doc in documents:
        score = lexical_score(question, doc["text"])
        scored.append((score, doc))

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best_document = scored[0]
    return best_document, best_score


# =============================================================================
# 3. AUGMENTATION
# =============================================================================

def build_augmented_prompt(question: str, context: str) -> str:
    """Build the prompt that will be handed to the generator."""
    return f"""You must answer only from the context provided.

Context:
{context}

Question:
{question}

Answer:
"""


# =============================================================================
# 4. A SIMULATED GENERATION
# =============================================================================

def generate_answer(question: str, context: str) -> str:
    """Simulate a generation.

    In a real RAG this function would call an LLM. Here it returns a simple
    answer, so as to isolate the architecture.
    """
    return f"According to the document retrieved: {context}"


# =============================================================================
# 5. THE MAIN PROGRAM
# =============================================================================

def main() -> None:
    print("=" * 78)
    print("Lab 2-1 — Assembling a first conceptual RAG: the anatomy")
    print("=" * 78)

    question = "How many books may a student borrow?"

    print("\nTHE USER'S QUESTION")
    print(question)

    print("\n1. RETRIEVAL")
    best_doc, score = retrieve(question, DOCUMENTS)
    if best_doc is None:
        print("No document available: the pipeline stops here.")
        return
    print(f"Document kept : {best_doc['id']} — {best_doc['title']}")
    print(f"Lexical score : {score}")
    print(f"Passage       : {best_doc['text']}")

    print("\n2. AUGMENTATION")
    prompt = build_augmented_prompt(question, best_doc["text"])
    print(prompt)

    print("\n3. GENERATION")
    answer = generate_answer(question, best_doc["text"])
    print(answer)

    print("\nWHAT TO REMEMBER")
    print("- A RAG is a processing chain, not a single model.")
    print("- A bad retrieval produces a bad context.")
    print("- The generation depends heavily on the context injected.")


if __name__ == "__main__":
    main()
