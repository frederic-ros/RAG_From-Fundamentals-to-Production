# -*- coding: utf-8 -*-
"""
embeddings.py — the shared similarity search of the Chapter 16 labs.

This module supplies a minimal semantic search engine, reused by every lab for:

  - the similarity search (finding documents that "resemble" a question),
  - and, above all, showing its LIMIT when the answer lies between documents.

Two implementations, chosen automatically:

  1. sentence-transformers, if installed: real dense embeddings, as in
     production. Only activated if the model loads with no network access.
  2. a deterministic TF-IDF fallback otherwise: a weighted bag of words,
     offline, with no API key. The teaching point holds in both cases, because
     the lesson of Chapter 16 does not depend on the quality of the embeddings:
     even perfect ones would not chain facts together.

The labs depend ONLY on this module: they run anywhere.
"""

from __future__ import annotations

from typing import List, Tuple

_MODEL = None
_MODE = None


def _load_transformer():
    """Try to load sentence-transformers, without ever blocking on the network."""
    global _MODEL, _MODE
    try:
        from sentence_transformers import SentenceTransformer

        # A small multilingual model; only used if already in the local cache.
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model.encode(["test"])  # check that the encoding really works
        _MODEL = model
        _MODE = "sentence-transformers"
        return True
    except Exception:
        return False


def _init():
    global _MODE
    if _MODE is not None:
        return
    if not _load_transformer():
        _MODE = "tfidf"


def mode() -> str:
    """Return the active mode: 'sentence-transformers' or 'tfidf'."""
    _init()
    return _MODE


class SimilarityEngine:
    """Index a list of documents and answer queries by similarity.

    The interface is deliberately tiny: build with the documents, then call
    `search_for(question, k)`. That is all the labs need in order to show that a
    retrieval, even a successful one, cannot chain facts together.
    """

    def __init__(self, documents: List[str]):
        _init()
        self.documents = list(documents)
        self._mode = _MODE
        if self._mode == "sentence-transformers":
            self._vectors = _MODEL.encode(self.documents, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._vectorizer = TfidfVectorizer()
            self._matrix = self._vectorizer.fit_transform(self.documents)

    def search_for(self, question: str, k: int = 3) -> List[Tuple[int, float]]:
        """Return the indices of the k closest documents, with their scores.

        The list is sorted from the most relevant to the least.
        """
        if self._mode == "sentence-transformers":
            import numpy as np

            q = _MODEL.encode([question], normalize_embeddings=True)[0]
            scores = self._vectors @ q  # the dot product is the cosine (normed vectors)
            order = np.argsort(-scores)[:k]
            return [(int(i), float(scores[i])) for i in order]
        else:
            from sklearn.metrics.pairwise import cosine_similarity

            qv = self._vectorizer.transform([question])
            scores = cosine_similarity(qv, self._matrix)[0]
            order = scores.argsort()[::-1][:k]
            return [(int(i), float(scores[i])) for i in order]
