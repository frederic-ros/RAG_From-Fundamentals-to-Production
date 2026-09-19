# -*- coding: utf-8 -*-
"""
embeddings.py — the DENSE (semantic) search for the Chapter 18 labs.

Dense search finds "what the user MEANT": it compares the meaning of the query
with the meaning of the fragments, through vectors. It is one of the two
searchers in a hybrid search, the other being BM25, the literal searcher.

Two implementations, as in the earlier chapters:

  - sentence-transformers (all-MiniLM-L6-v2) if present and loadable offline;
  - otherwise a deterministic TF-IDF fallback (scikit-learn), with no network and
    no API key.

The teaching point of the chapter — that dense search is almost BLIND to exact
codes and references such as "E-204" — holds in both cases. Better still: under
TF-IDF the phenomenon is sharper, because a rare code weighs little in a bag of
words.

A NOTE ON THE WORD LISTS BELOW. _CODE_PATTERNS and _SYNONYMS are not decoration:
in fallback mode they ARE the mechanism that simulates dense behaviour. They are
matched against the corpus text, so they must be written in the corpus language
and kept in step with generate_corpus.py. Left in French against an English
corpus, they match nothing: the dense search loses its semantic reach and the
chapter's demonstration inverts.

Minimal interface: index a corpus, then obtain a COMPLETE ranking of every
document, because rank fusion (RRF) needs ranks, not only the top-k.
"""

from __future__ import annotations

from typing import List, Tuple

_MODEL = None
_MODE = None


def _load_transformer() -> bool:
    global _MODEL, _MODE
    try:
        from sentence_transformers import SentenceTransformer

        modele = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        modele.encode(["test"])
        _MODEL = modele
        _MODE = "sentence-transformers"
        return True
    except Exception:
        return False


def _init() -> None:
    global _MODE
    if _MODE is not None:
        return
    if not _load_transformer():
        _MODE = "tfidf"


def mode() -> str:
    """'sentence-to transforms' or 'tfidf'."""
    _init()
    return _MODE


import re as _re

# Code and reference patterns, folded onto a generic token for their family, to
# SIMULATE the dense search's blind spot in TF-IDF mode (see DenseSearch).
_CODE_PATTERNS = [
    (_re.compile(r"\bs(?:ection)?\.?\s?\d{2,4}\b", _re.I), " lawref "),      # section 172
    (_re.compile(r"\b[a-z]-\d{2,4}\b", _re.I), " faultcode "),               # E-204, P-42
    (_re.compile(r"\b\d+\.\d+(?:\.\d+)?\b"), " versionnum "),               # 535.86
    (_re.compile(r"\bbs\s?\d{3,4}\b", _re.I), " standardref "),             # BS 7671
]


def _normalise_semantics(text: str) -> str:
    """Fold exact codes onto generic family tokens, and bring a few synonyms
    together — to SIMULATE dense behaviour under TF-IDF.

    Two effects, faithful to the chapter:

      - THE BLIND SPOT on codes: "E-204" and "E-205" both become "faultcode",
        so the fallback can no longer tell them apart;
      - THE SEMANTIC STRENGTH: families of synonyms ("telecommuting", "working
        away from the office", "working from home") are brought back to a common
        concept, as a real embedding would do.

    With sentence-transformers this function is not used: the real dense
    behaviour is observed instead.
    """
    t = text.lower()
    for pattern, replacement in _CODE_PATTERNS:
        t = pattern.sub(replacement, t)
    for family, concept in _SYNONYMS:
        for variant in family:
            t = t.replace(variant, concept)
    return t


# Families of synonyms folded onto a common concept: the strength of the
# simulated dense search. Each family must cover BOTH the wording of the
# documents and the wording of the queries in generate_corpus.py, since it is
# the bridge between the two.
_SYNONYMS = [
    (("telecommuting", "working away from the office", "away from the office",
      "working from home", "disconnect"),
     " conceptremotework "),
    (("motor that runs hot", "runs hot", "overheating", "excessive heating",
      "cooling", "thermal"),
     " conceptoverheating "),
    (("draws too much power", "too much power", "consumption", "current drawn",
      "energy efficiency", "efficiency", "output", "rated values"),
     " conceptefficiency "),
    (("demotivated", "losing heart", "lost its momentum", "momentum",
      "re-engage", "re-engaging", "re-energising", "motivate"),
     " conceptmotivation "),
]


class DenseSearch:
    """Index a corpus and rank it by semantic similarity to a query.

    An important note on the fallback mode (TF-IDF). A real dense search is
    almost BLIND to exact codes such as "E-204", because an embedding captures
    MEANING, and a code has no meaning in vector space — two neighbouring codes,
    E-204 and E-205, are near-identical to the model. Raw TF-IDF, however, SEES
    codes as tokens, so it would not reproduce the chapter's blind spot at all.
    To stay faithful to the phenomenon in the absence of sentence-transformers,
    the fallback applies a SEMANTIC NORMALISATION: codes and references (E-204,
    section 172, 535.86, P-42) are folded onto a generic token for their family.
    The result: the fallback search "understands" that it is looking at a code,
    but can no longer tell E-204 from E-205 — exactly the blind spot the chapter
    describes.

    With sentence-transformers no normalisation is applied: the real dense
    behaviour is observed. The lesson holds in both cases.
    """

    def __init__(self, documents: List[str]):
        _init()
        self.documents = list(documents)
        self._mode = _MODE
        if self._mode == "sentence-transformers":
            self._vecteurs = _MODEL.encode(self.documents, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._vect = TfidfVectorizer()
            corpus_norm = [_normalise_semantics(d) for d in self.documents]
            self._matrice = self._vect.fit_transform(corpus_norm)

    def _scores(self, query: str):
        if self._mode == "sentence-transformers":
            q = _MODEL.encode([query], normalize_embeddings=True)[0]
            return self._vecteurs @ q
        else:
            from sklearn.metrics.pairwise import cosine_similarity

            qv = self._vect.transform([_normalise_semantics(query)])
            return cosine_similarity(qv, self._matrice)[0]

    def rank(self, query: str) -> List[Tuple[int, float]]:
        """Return EVERY document, ordered: (index, score), best to worst."""
        scores = self._scores(query)
        ordre = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        return [(i, float(scores[i])) for i in ordre]

    def search_for(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Top-k documents (index, score)."""
        return self.rank(query)[:k]
