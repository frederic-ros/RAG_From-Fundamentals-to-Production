# -*- coding: utf-8 -*-
"""
Lab 2-2 — Building an augmented prompt from documents

Learning objective
------------------
This lab isolates the Augmentation step.

An augmented prompt is not just a question with some documents bolted on. It
has to lay out clearly:

  - the rules for answering;
  - the documents available;
  - the user's question;
  - the format expected.

The lab runs with no API key.
"""

from typing import List


# =============================================================================
# 1. THE DATA OF THE LAB
# =============================================================================

QUESTION = "How many books may a student borrow, and for how long?"

DOCUMENTS = [
    "An enrolled student may borrow up to 10 books.",
    "The normal borrowing period is 21 days.",
    "Reference works must be consulted on the premises.",
]


# =============================================================================
# 2. BUILDING THE PROMPT
# =============================================================================

def format_documents(documents: List[str]) -> str:
    """Number the documents, to make citing them easier."""
    lines = []
    for i, doc in enumerate(documents, start=1):
        lines.append(f"[Document {i}] {doc}")
    return "\n".join(lines)


def build_prompt(question: str, documents: List[str]) -> str:
    """Build an augmented prompt.

    The important idea is to separate the roles: instruction, context,
    question, format.
    """
    context = format_documents(documents)

    prompt = f"""Role:
You are a documentary assistant.

Rules:
- Answer only from the documents provided.
- If the documents do not allow an answer, say so plainly.
- Cite the documents used, in square brackets.

Documents:
{context}

User's question:
{question}

Expected format:
Short answer:
Documents used:
"""

    return prompt


# =============================================================================
# 3. THE MAIN PROGRAM
# =============================================================================

def main() -> None:
    print("=" * 78)
    print("Lab 2-2 — Building an augmented prompt")
    print("=" * 78)

    print("\nQUESTION")
    print(QUESTION)

    print("\nDOCUMENTS")
    for i, doc in enumerate(DOCUMENTS, start=1):
        print(f"{i}. {doc}")

    print("\nTHE AUGMENTED PROMPT")
    print("-" * 78)
    prompt = build_prompt(QUESTION, DOCUMENTS)
    print(prompt)

    print("\nWHAT TO REMEMBER")
    print("- Augmentation structures the context before the generation.")
    print("- The rules must be explicit.")
    print("- The output format can be constrained from the prompt onwards.")


if __name__ == "__main__":
    main()
