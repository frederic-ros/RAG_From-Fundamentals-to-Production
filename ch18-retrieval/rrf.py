# -*- coding: utf-8 -*-
"""
rrf.py — Reciprocal Rank Fusion.

The problem: merge a BM25 list with a dense list. Adding their scores is absurd —
a BM25 score is unbounded (12, 18, 30...) while a cosine similarity sits between
0 and 1. They do not live in the same world. It would be adding kilometres to
degrees.

The solution is elegant: IGNORE the scores, keep only the RANKS. A rank means the
same thing for both methods — to be first is to be first.

    RRF(d) = sum over the methods r of 1 / (k + rank_r(d))

where rank_r(d) is the 1-based position of document d in method r's list, and k a
small damping constant, typically 60. A document ranked well by SEVERAL methods
accumulates several contributions; a document ranked badly everywhere stays at
the bottom.

A nuance from the chapter: fusion only helps if the methods are REALLY different.
Merging two variants of BM25 brings almost nothing — they go wrong in the same
places.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def ranks_from_ranking(ranking: List[Tuple[int, float]]) -> Dict[int, int]:
    """Convert a ranking [(index, score), ...] into {index: rank}, 1-based."""
    return {idx: position for position, (idx, _score) in enumerate(ranking, start=1)}


def rrf(rankings: List[List[Tuple[int, float]]], k: int = 60
        ) -> List[Tuple[int, float]]:
    """Merge several rankings by RRF.

    `rankings`: a list of rankings, each in the form [(index, score), ...], best
    first, as returned by BM25.rank() or DenseSearch.rank().
    `k`: the damping constant, 60 by default.

    Returns a merged ranking [(index, rrf_score), ...], best first.
    """
    contributions: Dict[int, float] = {}
    for ranking in rankings:
        ranks = ranks_from_ranking(ranking)
        for idx, rank in ranks.items():
            contributions[idx] = contributions.get(idx, 0.0) + 1.0 / (k + rank)
    merged = sorted(contributions.items(), key=lambda t: t[1], reverse=True)
    return merged


def contribution(rank: int, k: int = 60) -> float:
    """The RRF contribution of a document at a given rank (a teaching helper)."""
    return 1.0 / (k + rank)
