# -*- coding: utf-8 -*-
"""
bm25.py — the LEXICAL search (BM25), implemented by hand.

BM25 is the LITERAL searcher of Chapter 18: give it "E-204" and it finds the
documents holding exactly that run of characters. It understands nothing about
the subject, but it never misses an exact reference. It is the algorithm
inherited from decades of documentary search, ranking documents by the words they
share with the query.

It is implemented here in pure Python, with no dependency, for two reasons:

  1. to make it transparent — you SEE the formula at work;
  2. to keep the labs runnable with nothing to install.

In production you would use a proven library (rank_bm25, Elasticsearch,
OpenSearch); Lab 18-2 shows how to plug rank_bm25 in instead, with an identical
interface. The principle does not change.

The BM25 formula, for a document d and a query q:

    score(d, q) = sum over the terms t of q of:
        IDF(t) * ( f(t,d) * (k1 + 1) ) / ( f(t,d) + k1 * (1 - b + b * |d|/avgdl) )

where f(t,d) is the frequency of term t in d, |d| the length of d, avgdl the mean
document length, and IDF(t) the rarity of the term in the corpus. The usual
parameters: k1 = 1.5 (frequency saturation), b = 0.75 (length normalisation).
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import List, Tuple


def tokenize(text: str) -> List[str]:
    """Split into simple tokens: words and alphanumeric codes, lower-cased.

    Important: codes are kept as they are ("e-204", "p-42"), as tokens in their
    own right. That is exactly what gives BM25 its strength on exact references.
    """
    text = text.lower()
    # A token is a run of letters and digits, possibly joined by - or . or /
    # so as to capture "e-204", "535.86", "bs 7671".
    return re.findall(r"[a-z0-9]+(?:[-./][a-z0-9]+)*", text)


class BM25:
    """A BM25 index over a corpus of documents."""

    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.documents = list(documents)
        self.k1 = k1
        self.b = b
        self._docs_tokens = [tokenize(d) for d in self.documents]
        self._lengths = [len(t) for t in self._docs_tokens]
        self._avgdl = (sum(self._lengths) / len(self._lengths)
                       if self._lengths else 0.0)
        self._freqs = [Counter(t) for t in self._docs_tokens]
        self._idf = self._compute_idf()

    def _compute_idf(self) -> dict:
        """Smoothed IDF: log((N - n + 0.5) / (n + 0.5) + 1), n = docs holding t."""
        n_docs = len(self.documents)
        doc_freq: Counter = Counter()
        for freqs in self._freqs:
            for terme in freqs:
                doc_freq[terme] += 1
        idf = {}
        for terme, n in doc_freq.items():
            idf[terme] = math.log((n_docs - n + 0.5) / (n + 0.5) + 1)
        return idf

    def _score_doc(self, requete_tokens: List[str], i: int) -> float:
        score = 0.0
        freqs = self._freqs[i]
        longueur = self._lengths[i]
        for terme in requete_tokens:
            if terme not in freqs:
                continue
            f = freqs[terme]
            idf = self._idf.get(terme, 0.0)
            numerateur = f * (self.k1 + 1)
            denominateur = f + self.k1 * (1 - self.b + self.b * longueur / self._avgdl)
            score += idf * numerateur / denominateur
        return score

    def rank(self, query: str) -> List[Tuple[int, float]]:
        """Return EVERY document, ordered: (index, score), best to worst."""
        req = tokenize(query)
        scores = [(i, self._score_doc(req, i)) for i in range(len(self.documents))]
        scores.sort(key=lambda t: t[1], reverse=True)
        return scores

    def search_for(self, query: str, k: int = 5) -> List[Tuple[int, float]]:
        """Top-k documents (index, score)."""
        return self.rank(query)[:k]
