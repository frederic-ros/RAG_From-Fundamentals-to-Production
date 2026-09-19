# -*- coding: utf-8 -*-
"""
reranklib.py — the shared building blocks of Chapter 20 (re-ranking).

The chapter tells how to turn a good LIST into a good TOP of the list. This
module supplies the chapter's two "searchers" and its measurement tools,
transparently and offline:

  - BiEncoder    : fast, COARSE. It encodes the question and the document
                   SEPARATELY, one vector each, then compares by distance. This
                   is the first-stage retrieval.
  - CrossEncoder : slow, FINE. It reads the PAIR (question, document) TOGETHER
                   and produces a relevance score directly. This is the
                   re-ranker.
  - mmr          : the diversification (Maximal Marginal Relevance).
  - mrr, ndcg    : the standard metrics for measuring a ranking.

No API key, no network. Two implementations of "meaning" are possible:

  1. sentence-transformers (real bi- and cross-encoders) if installed;
  2. a deterministic fallback, TF-IDF plus a weighted lexical overlap, which
     faithfully REPRODUCES the phenomenon of the chapter: the bi-encoder confuses
     close subjects, while the cross-encoder, which "re-reads" the pair, settles
     it better.

The fallback is deliberately built so the chapter's lessons appear even without a
heavy model — exactly as the Chapter 18 companion does for the hybrid search.

A NOTE ON THE WORD LISTS BELOW. In fallback mode, the stop-word set and the code
family map are not decoration: they ARE the mechanism. They are matched against
the corpus text, so they must be written in the corpus language and kept in step
with generate_corpus.py.
"""

from __future__ import annotations

import re
from typing import List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# Optional detection of sentence-transformers
# ===========================================================================
_ST_BI = None
_ST_CROSS = None
_MODE = None


def _init_models() -> str:
    """Try to load real models; otherwise fall back to TF-IDF.

    Returns the active mode: 'sentence-transformers' or 'tfidf'.
    """
    global _ST_BI, _ST_CROSS, _MODE
    if _MODE is not None:
        return _MODE
    try:
        from sentence_transformers import CrossEncoder, SentenceTransformer
        bi = SentenceTransformer("all-MiniLM-L6-v2")
        cross = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        # A minimal test: this can fail offline, at the download step.
        bi.encode(["test"])
        cross.predict([("a", "b")])
        _ST_BI, _ST_CROSS, _MODE = bi, cross, "sentence-transformers"
    except Exception:
        _MODE = "tfidf"
    return _MODE


def mode() -> str:
    """The active model mode: 'sentence-transformers' or 'tfidf'."""
    return _init_models()


# ===========================================================================
#  Simple tokenisation (fallback)
# ===========================================================================
_MOTIF = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> List[str]:
    return _MOTIF.findall(text.lower())


# ===========================================================================
# THE BI-ENCODER — fast and coarse (separate encoding)
# ===========================================================================
class BiEncoder:
    """Encode each text SEPARATELY into a vector, then compare by cosine.

    In 'tfidf' mode (the fallback) a TF-IDF is fitted on the corpus: a purely
    lexical and SEPARATE encoding. It captures the general closeness of subject
    but stays coarse on detail, exactly like a dense bi-encoder.

    An honest teaching note: the blind spot on codes ("M-18" against "M-17") is
    fundamentally a phenomenon of DENSE embeddings — raw TF-IDF would see the
    codes as distinct tokens and would not reproduce it. To stay faithful to the
    chapter offline, the codes of one family are folded onto a generic token
    ("M-17" and "M-18" both become "motorseries"): the bi-encoder can no longer
    tell them apart, like a real dense model. With sentence-transformers the
    phenomenon is native and this folding is not applied.
    """

    _FAMILY = re.compile(r"\b([a-zA-Z]+)-?\d+\b")

    def __init__(self, corpus: Sequence[str]) -> None:
        self.corpus = list(corpus)
        self.mode = mode()
        if self.mode == "sentence-transformers":
            self._vecs = _ST_BI.encode(self.corpus, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2))
            corpus_replie = [self._fold_codes(t) for t in self.corpus]
            self._mat = self._vec.fit_transform(corpus_replie)

    def _fold_codes(self, text: str) -> str:
        """Replace any code (letters and digits) by a family token.

        "M-18" and "M-17" both become "motorseries"; "P-42" becomes
        "pumpseries". The bi-encoder no longer sees anything but the FAMILY, not
        the precise number: that is what recreates its confusion between
        neighbouring codes.
        """
        families = {"m": "motorseries", "p": "pumpseries"}
        def _sub(m):
            letter = m.group(1).lower()[0]
            return families.get(letter, "refseries")
        return self._FAMILY.sub(_sub, text)

    def rank(self, query: str, k: Optional[int] = None) -> List[Tuple[int, float]]:
        """Return [(index, score)] sorted by decreasing score (the first k)."""
        if self.mode == "sentence-transformers":
            q = _ST_BI.encode([query], normalize_embeddings=True)[0]
            scores = self._vecs @ q
        else:
            from sklearn.metrics.pairwise import cosine_similarity
            q = self._vec.transform([self._fold_codes(query)])
            scores = cosine_similarity(q, self._mat)[0]
        order = np.argsort(-scores)
        res = [(int(i), float(scores[i])) for i in order]
        return res[:k] if k else res

    def vectors(self) -> np.ndarray:
        """The document vectors (dense, or densified TF-IDF) for MMR."""
        if self.mode == "sentence-transformers":
            return np.asarray(self._vecs)
        return self._mat.toarray()

    def query_vector(self, query: str) -> np.ndarray:
        if self.mode == "sentence-transformers":
            return _ST_BI.encode([query], normalize_embeddings=True)[0]
        return self._vec.transform([self._fold_codes(query)]).toarray()[0]


# ===========================================================================
# THE CROSS-ENCODER — slow and fine (it reads the pair together)
# ===========================================================================
class CrossEncoder:
    """Read the PAIR (question, document) together and produce a relevance score.

    In 'tfidf' mode (the fallback), that "joint re-reading" is simulated by a
    score which does LOOK at the question and the document at the SAME TIME:

      - the overlap of important terms, including exact codes and references;
      - a strong bonus if a code from the question appears as such in the
        document;
      - a penalty if a NEIGHBOURING but DIFFERENT code is present — the
        bi-encoder's trap, corrected here.

    This is not a real transformer, but it faithfully reproduces the chapter's
    point: the cross-encoder settles what the bi-encoder confuses.
    """

    _CODE = re.compile(r"\b([a-zA-Z]+-?\d+)\b")

    def __init__(self) -> None:
        self.mode = mode()
        self.last_calls = 0

    def _codes(self, text: str) -> List[str]:
        return [c.lower() for c in self._CODE.findall(text)]

    def score_pair(self, query: str, document: str) -> float:
        """The relevance score of ONE document for the query (counts as 1 call)."""
        self.last_calls += 1
        if self.mode == "sentence-transformers":
            return float(_ST_CROSS.predict([(query, document)])[0])

        # --- The deterministic fallback: a simulated joint re-reading ---------
        q_tokens = [t for t in _tokens(query)]
        q_set = set(q_tokens)
        d_tokens = _tokens(document)
        d_set = set(d_tokens)
        if not q_set:
            return 0.0

        # The content words of the question: the very common empty words are
        # ignored, so the score reflects shared MEANING rather than grammatical
        # noise. This list must match the language of the corpus; left in French
        # against an English corpus it filters nothing, every question word
        # counts as content, and the scores flatten out.
        stop = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or",
                "is", "are", "be", "it", "its", "this", "that", "what", "which",
                "how", "when", "must", "should", "does", "do", "need", "at",
                "by", "with", "from", "about", "there"}
        content = [t for t in q_set if t not in stop]
        if not content:
            content = list(q_set)

        # 1) The overlap of content words: how many of the question's ideas the
        #    document actually covers.
        common = [t for t in content if t in d_set]
        base = len(common) / len(content)

        # 2) Fine handling of codes and references: the heart of the chapter.
        q_codes = set(self._codes(query))
        d_codes = set(self._codes(document))
        bonus = 0.0
        if q_codes:
            exacts = q_codes & d_codes
            voisins = d_codes - q_codes
            # The right code present as such -> a strong bonus.
            bonus += 0.8 * (len(exacts) / len(q_codes))
            # The right code ABSENT but neighbouring codes present -> a clear
            # penalty: the document is about something else that resembles it,
            # M-17 in place of M-18.
            if voisins and not exacts:
                bonus -= 0.5

        # 3) A small completeness bonus: a document covering SEVERAL content
        #    terms beyond the code is probably the reference fragment.
        coverage = len(common)
        bonus += 0.05 * coverage

        return float(base + bonus)

    def rerank(self, query: str, candidates: Sequence[Tuple[int, str]]
               ) -> List[Tuple[int, float]]:
        """Re-score each candidate (index, text) and return the sorted ranking."""
        scored = [(i, self.score_pair(query, txt)) for i, txt in candidates]
        scored.sort(key=lambda x: -x[1])
        return scored


# ===========================================================================
#  MMR — diversification (relevance against redundancy)
# ===========================================================================
def mmr(query_vec: np.ndarray, vectors: np.ndarray, candidates: List[int],
        k: int, lam: float = 0.7) -> List[int]:
    """Select k documents, balancing relevance against diversity.

    At each step the candidate added is the one maximising
    lam * sim(d, query) - (1 - lam) * max over the already chosen s of sim(d, s).
    lam = 1.0 gives pure relevance; lam = 0.0 gives pure diversity.
    """
    def _sim(a, b):
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(a @ b / (na * nb))

    chosen: List[int] = []
    remaining = list(candidates)
    while remaining and len(chosen) < k:
        best, best_score = None, -1e9
        for c in remaining:
            relevance = _sim(vectors[c], query_vec)
            if chosen:
                redundancy = max(_sim(vectors[c], vectors[s]) for s in chosen)
            else:
                redundancy = 0.0
            score = lam * relevance - (1 - lam) * redundancy
            if score > best_score:
                best, best_score = c, score
        chosen.append(best)
        remaining.remove(best)
    return chosen


# ===========================================================================
# The metrics: MRR and nDCG
# ===========================================================================
def mrr(ranking: Sequence[int], relevant: Sequence[int]) -> float:
    """Mean Reciprocal Rank for ONE query: 1/rank of the first good document."""
    relevant = set(relevant)
    for rank, doc in enumerate(ranking, start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0


def ndcg(ranking: Sequence[int], relevant: Sequence[int], k: int = 5) -> float:
    """nDCG@k: rewards the good documents AND their position near the top."""
    relevant = set(relevant)
    dcg = 0.0
    for i, doc in enumerate(ranking[:k]):
        if doc in relevant:
            dcg += 1.0 / np.log2(i + 2)  # a gain of 1, discounted by the rank
    # The ideal: every relevant document at the top.
    ideal = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant), k)))
    return float(dcg / ideal) if ideal else 0.0


def rank_of(ranking: Sequence[int], doc: int) -> Optional[int]:
    """The 1-based rank of a document in a ranking, or None if it is absent."""
    for r, d in enumerate(ranking, start=1):
        if d == doc:
            return r
    return None
