# -*- coding: utf-8 -*-
"""
Lab 4-1 — TF-IDF against embeddings: the shock of synonyms

Learning objective
------------------
Show that a lexical engine mainly compares words, whereas a semantic
representation brings together phrasings of neighbouring meaning.

The lab deliberately uses a tiny teaching embedding, built by hand, so as to
stay runnable with no model download and no API key.

The message to take away:

    The lexical sees the words.
    The embedding looks for a proximity of meaning.

A note on the lexical trap. In English, "battery" carries two unrelated senses:
a power cell, and "a battery of tests" — a set of trials. The trap document uses
the second sense. It shares the exact word with the question and shares nothing
of its meaning, which is precisely what defeats a lexical engine.
"""

import re
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


QUESTION = "How do I replace a faulty battery?"

DOCUMENTS: List[Dict[str, str]] = [
    {
        "id": "Doc_synonym",
        "text": "Procedure for replacing a lithium accumulator.",
        "expected": "relevant",
    },
    {
        "id": "Doc_off_topic",
        "text": "The battery of acceptance tests comprises three inspection stages.",
        "expected": "lexical trap",
    },
    {
        "id": "Doc_indifferent",
        "text": "The HR department approves annual leave requests.",
        "expected": "off the subject",
    },
]


# ---------------------------------------------------------------------------
# Teaching embeddings
# ---------------------------------------------------------------------------
# Each important word is given a small semantic vector. "Battery" and
# "accumulator" are deliberately close. The sense of "tests / inspection" is
# deliberately far away, on another dimension.
# ---------------------------------------------------------------------------

WORD_VECTORS: Dict[str, np.ndarray] = {
    "battery": np.array([1.0, 0.0, 0.0, 0.0]),
    "accumulator": np.array([0.95, 0.05, 0.0, 0.0]),
    "lithium": np.array([0.90, 0.10, 0.0, 0.0]),
    "replace": np.array([0.75, 0.20, 0.0, 0.0]),
    "replacing": np.array([0.75, 0.20, 0.0, 0.0]),
    "faulty": np.array([0.70, 0.25, 0.0, 0.0]),
    "procedure": np.array([0.60, 0.30, 0.0, 0.0]),

    "tests": np.array([0.0, 0.0, 1.0, 0.0]),
    "acceptance": np.array([0.0, 0.0, 0.95, 0.0]),
    "inspection": np.array([0.0, 0.0, 0.90, 0.0]),
    "stages": np.array([0.0, 0.0, 0.85, 0.0]),

    "hr": np.array([0.0, 0.0, 0.0, 1.0]),
    "leave": np.array([0.0, 0.0, 0.0, 0.90]),
}

EMBEDDING_DIM = 4


def tokenize(text: str) -> List[str]:
    """A simple tokenisation, enough for this lab."""
    return re.findall(r"[a-zA-Z]+", text.lower())


def sentence_embedding(text: str) -> np.ndarray:
    """Average the vectors of the known words.

    Returns a zero vector if no word of the text is known: that is the teaching
    case of the "indifferent" document, which shares no meaning at all.
    """
    vectors = [WORD_VECTORS[token] for token in tokenize(text) if token in WORD_VECTORS]

    if not vectors:
        return np.zeros(EMBEDDING_DIM)

    return np.mean(vectors, axis=0)


def cosine(u: np.ndarray, v: np.ndarray) -> float:
    """A robust cosine similarity: returns 0.0 if either vector is null."""
    nu = float(np.linalg.norm(u))
    nv = float(np.linalg.norm(v))

    if nu == 0.0 or nv == 0.0:
        return 0.0

    return float(np.dot(u, v) / (nu * nv))


def main() -> None:
    print("=" * 78)
    print("Lab 4-1 — TF-IDF against embeddings: the shock of synonyms")
    print("=" * 78)

    print("\nQUESTION")
    print(QUESTION)

    print("\nDOCUMENTS")
    for doc in DOCUMENTS:
        print(f"- {doc['id']:16s} | {doc['text']}")

    # ---------------------------------------------------------------------
    # 1. Lexical TF-IDF
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("1. THE LEXICAL ANALYSIS — TF-IDF")
    print("=" * 78)

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([QUESTION] + [doc["text"] for doc in DOCUMENTS])

    q_vec = matrix[0]
    doc_vecs = matrix[1:]
    tfidf_scores = cosine_similarity(q_vec, doc_vecs).flatten()

    for doc, score in zip(DOCUMENTS, tfidf_scores):
        print(f"{doc['id']:16s} | TF-IDF score = {score:.4f} | {doc['expected']}")

    tfidf_best = DOCUMENTS[int(np.argmax(tfidf_scores))]["id"]
    print(f"\nBest lexical document: {tfidf_best}")

    # ---------------------------------------------------------------------
    # 2. Teaching embeddings
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("2. THE SEMANTIC ANALYSIS — TEACHING EMBEDDINGS")
    print("=" * 78)

    q_emb = sentence_embedding(QUESTION)
    emb_scores: List[float] = []

    for doc in DOCUMENTS:
        d_emb = sentence_embedding(doc["text"])
        score = cosine(q_emb, d_emb)
        emb_scores.append(score)
        print(f"{doc['id']:16s} | embedding score = {score:.4f} | {doc['expected']}")

    emb_best = DOCUMENTS[int(np.argmax(emb_scores))]["id"]
    print(f"\nBest semantic document: {emb_best}")

    # ---------------------------------------------------------------------
    # 3. Interpretation
    # ---------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("INTERPRETATION")
    print("=" * 78)

    if tfidf_best == "Doc_off_topic" and emb_best == "Doc_synonym":
        print("The expected result:")
        print("- TF-IDF favours the document sharing the exact word 'battery'.")
        print("- The embedding brings 'battery' and 'accumulator' together.")
        print("- The semantic engine therefore finds the genuinely relevant document.")
    else:
        print("The result is not the expected one. Check the corpus or the vectors.")

    print("\nWHAT TO REMEMBER")
    print("The lexical compares forms. The embedding approximates a proximity of meaning.")


if __name__ == "__main__":
    main()
