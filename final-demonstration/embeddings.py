# -*- coding: utf-8 -*-
"""
embeddings.py — similarity search, shared by the final demonstration.

The demonstration needs a single similarity engine, used identically by every
tier: only the pipeline around it changes. Two backends, on the same
graceful-degradation principle as tokenizer.py:

  1. sentence-transformers, if installed: real dense embeddings, the kind you
     would use in production. A light multilingual model by default.
  2. a TF-IDF fallback otherwise: scikit-learn, deterministic, offline, with
     nothing to download. Enough for every demonstration in the chapter.

The lab code depends only on this module: it runs anywhere, and a reader who
installs sentence-transformers automatically gets the real vectors. No API key
either way.

The point of the demonstration holds just as well with an imperfect backend:
what changes the score from one tier to the next is the chain around the engine,
not the quality of the vectors. The engine is deliberately held constant.
"""

from __future__ import annotations

from typing import List, Sequence
import numpy as np

# ---------------------------------------------------------------------------
# Backend detection, with no network access at import time.
# ---------------------------------------------------------------------------
_MODEL = None
_MODE = None


def _load_st():
    """Try to load sentence-transformers; return True if available."""
    global _MODEL, _MODE
    try:
        from sentence_transformers import SentenceTransformer
        # A light multilingual model. If the weights are not cached and there is
        # no network, instantiation fails and we fall back to TF-IDF.
        _MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        _MODE = "sentence-transformers"
        return True
    except Exception:
        return False


def _init():
    global _MODE
    if _MODE is not None:
        return
    if not _load_st():
        _MODE = "tfidf"


def mode() -> str:
    """Return the active backend: 'sentence-transformers' or 'tfidf'."""
    _init()
    return _MODE


class SimilarityEngine:
    """A similarity index over a set of texts, with a transparent backend."""

    def __init__(self, texts: Sequence[str]):
        _init()
        self.texts: List[str] = list(texts)
        if _MODE == "sentence-transformers":
            self._emb = _MODEL.encode(self.texts, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vec = TfidfVectorizer(lowercase=True, token_pattern=r"(?u)\b\w+\b")
            self._mat = self._vec.fit_transform(self.texts)

    def scores(self, question: str) -> np.ndarray:
        """Vector of cosine similarities between the question and each text."""
        if _MODE == "sentence-transformers":
            q = _MODEL.encode([question], normalize_embeddings=True)
            return (self._emb @ q[0])
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([question])
        return cosine_similarity(q, self._mat)[0]

    def rank(self, question: str) -> List[tuple]:
        """List of (index, score), sorted by decreasing score."""
        s = self.scores(question)
        order = np.argsort(s)[::-1]
        return [(int(i), float(s[i])) for i in order]


if __name__ == "__main__":
    docs = [
        "The applicable rate is five per cent.",
        "The applicable rate is raised to eight per cent.",
    ]
    engine = SimilarityEngine(docs)
    print(f"Backend: {mode()}")
    for i, sc in engine.rank("What is the applicable rate?"):
        print(f"  score {sc:.3f} — {docs[i]}")
