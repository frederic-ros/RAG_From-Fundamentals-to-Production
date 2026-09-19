# -*- coding: utf-8 -*-
"""
annlib.py — the shared building blocks of the Chapter 19 labs.

The chapter tells a single story: how to find the nearest neighbours among
millions of vectors WITHOUT walking through them all. This module supplies the
tools common to every lab, in pure Python (NumPy only), so that the mechanisms
stay TRANSPARENT:

  - generate_corpus() : a deterministic corpus of vectors (fixed seeds);
  - exact_search()    : the "brute force" reference, comparing against EVERYTHING;
  - recall()          : the quality metric, how many true neighbours were found;
  - HNSWMini          : a teaching implementation of HNSW, readable and
                        instrumented — it COUNTS the distances computed and the
                        hops taken.

No heavy dependency, no API key, no network. Everything is deterministic: two
runs give the same figures, which is what makes the labs reproducible.

A teaching note
---------------
HNSWMini is NOT a production index (faiss and hnswlib are). It is a faithful
mock-up of the chapter's PRINCIPLE: enter at the top, descend layer by layer,
visit only a handful of nodes. Clarity is preferred to raw performance
throughout.
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Tuple

import numpy as np


# ===========================================================================
# 1. A corpus of vectors
# ===========================================================================
def generate_corpus(n: int, dim: int = 64, n_clusters: int = 12,
                   seed: int = 42) -> np.ndarray:
    """Generate `n` vectors of dimension `dim`, grouped into `n_clusters` clusters.

    The vectors are not drawn purely at random: a real corpus of embeddings forms
    CLUSTERS, because documents close in meaning group together. That is
    simulated here with Gaussians around randomly drawn centres. The vectors are
    normalised, so Euclidean distance becomes equivalent to cosine similarity, as
    with real embeddings.
    """
    rng = np.random.default_rng(seed)
    centres = rng.normal(0.0, 1.0, size=(n_clusters, dim))
    membership = rng.integers(0, n_clusters, size=n)
    noise = rng.normal(0.0, 0.25, size=(n, dim))
    vectors = centres[membership] + noise
    # L2 normalisation -> every vector on the unit sphere.
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return (vectors / norms).astype(np.float32)


def normalize(v: np.ndarray) -> np.ndarray:
    """Normalise a vector, or a batch of vectors, to L2 norm."""
    v = np.asarray(v, dtype=np.float32)
    if v.ndim == 1:
        n = np.linalg.norm(v)
        return v / n if n else v
    n = np.linalg.norm(v, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return v / n


# ===========================================================================
# 2. Exact search (the reference) and the recall metric
# ===========================================================================
def exact_search(corpus: np.ndarray, query: np.ndarray,
                     k: int = 10) -> Tuple[List[int], int]:
    """"Brute force" search: compare the query against EVERY vector.

    This is the ground truth — the true k nearest neighbours — and the target to
    beat on speed. Returns the indices of the k nearest AND the number of
    comparisons made, which equals the corpus size: everything was looked at.
    """
    query = normalize(query)
    # Cosine similarity is the dot product, for normalised vectors.
    sims = corpus @ query
    order = np.argsort(-sims)[:k]
    return order.tolist(), corpus.shape[0]


def recall(approximate: List[int], exact: List[int]) -> float:
    """The proportion of true neighbours (exact) actually found (approximate).

    This is THE quality measure of an approximate search: 1.0 is perfect, nothing
    missed; 0.9 means 9 of the 10 true neighbours were found.
    """
    if not exact:
        return 1.0
    return len(set(approximate) & set(exact)) / len(exact)


# ===========================================================================
# 3. A teaching HNSW, instrumented
# ===========================================================================
class HNSWMini:
    """A teaching implementation of HNSW (Hierarchical Navigable Small World).

    The chapter's idea in one sentence: a graph with several layers. You ENTER at
    the top layer — sparse, with long links, the motorway — approach roughly, and
    then DESCEND layer by layer towards shorter and shorter links (the local
    streets) to refine. The whole corpus is never visited, only a handful of
    nodes along the way.

    The parameters, the "dials" of the chapter:

        M               : the number of neighbours per node in each layer, the
                          density of the graph. Larger means better recall, but
                          more memory.
        ef_construction : the exploration width at BUILD time, the quality of the
                          graph.
        ef_search       : the exploration width at QUERY time. This is the
                          central dial: larger means better recall, but more
                          distances computed, and so more latency.

    Instrumentation: the counter `last_distances` records how many distances were
    computed during the last search — the figure that makes "HNSW does not look
    at everything" concrete.
    """

    def __init__(self, corpus: np.ndarray, M: int = 8, ef_construction: int = 50,
                 seed: int = 7) -> None:
        self.corpus = corpus
        self.M = M
        self.M0 = 2 * M  # the bottom layer is denser, as is common practice.
        self.ef_construction = ef_construction
        self.rng = random.Random(seed)
        # layers[l] = a dict {node_id -> list of neighbours} for layer l.
        self.layers: List[Dict[int, List[int]]] = []
        self.entry: Optional[int] = None
        self.max_level = -1
        self.last_distances = 0
        self._build()

    # -- distance (instrumented) ---------------------------------------------
    def _sim(self, i: int, q: np.ndarray) -> float:
        """Cosine similarity between the vector i and the query q. Counts 1 calcul."""
        self.last_distances += 1
        return float(self.corpus[i] @ q)

    # -- drawing the level of a new node --------------------------------------
    def _draw_level(self) -> int:
        """A random level, on a decreasing geometric distribution.

        The great majority of nodes live only in layer 0; a few climb one storey,
        very few climb two. That is what gives the pyramid its shape: sparse at
        the top, dense at the bottom. This follows the law of the HNSW paper:
        level = floor(-ln(u) * mL), with mL = 1/ln(M).
        """
        mL = 1.0 / math.log(self.M) if self.M > 1 else 1.0
        u = self.rng.random()
        if u <= 0.0:
            u = 1e-12
        return min(int(-math.log(u) * mL), 5)

    # -- greedy search within ONE layer ---------------------------------------
    def _search_layer(self, q: np.ndarray, entries: List[int],
                         ef: int, level: int) -> List[Tuple[float, int]]:
        """Explore layer `level` from the entry nodes given.

        The canonical HNSW algorithm, a best-first search bounded by ef:

          - `candidates`: the queue of nodes to visit, most promising first;
          - `found`: the `ef` best neighbours met so far.

        The walk stops when the best remaining candidate is worse than the worst
        of `found`: no point going further, we are moving away from the query. It
        is `ef` that sets the width of the exploration — and therefore the
        recall-against-latency trade-off of the chapter.
        """
        import heapq
        graph = self.layers[level]
        visited = set(entries)
        # The candidate queue: a max-heap on similarity, storing -sim.
        candidates: List[Tuple[float, int]] = []
        # The heap of those found: a min-heap on similarity, worst at the top.
        found: List[Tuple[float, int]] = []
        for e in entries:
            s = self._sim(e, q)
            heapq.heappush(candidates, (-s, e))
            heapq.heappush(found, (s, e))

        while candidates:
            neg_sim_c, c = heapq.heappop(candidates)
            sim_c = -neg_sim_c
            pire = found[0][0]  # more low similarity retenue
            # Stopping criterion: the best candidate is already worse than the
            # worst retained candidate, so no further progress is possible.
            if sim_c < pire:
                break
            for voisin in graph.get(c, []):
                if voisin in visited:
                    continue
                visited.add(voisin)
                s = self._sim(voisin, q)
                if len(found) < ef or s > found[0][0]:
                    heapq.heappush(candidates, (-s, voisin))
                    heapq.heappush(found, (s, voisin))
                    if len(found) > ef:
                        heapq.heappop(found)  # retire the pire
        return sorted(found, reverse=True)

    # -- insertion of a node ------------------------------------------------
    def _insert(self, node_id: int) -> None:
        q = self.corpus[node_id]
        level = self._draw_level()

        # Extend the stack of layers if this node climbs higher than any other.
        while len(self.layers) <= level:
            self.layers.append({})

        if self.entry is None:
            for l in range(level + 1):
                self.layers[l][node_id] = []
            self.entry = node_id
            self.max_level = level
            return

        # 1) Descendre depuis the sommet jusqu'to level+1 in mode glouton (1 input).
        ep = [self.entry]
        for l in range(self.max_level, level, -1):
            res = self._search_layer(q, ep, ef=1, level=l)
            ep = [res[0][1]] if res else ep

        # 2) layers level..0, we look for large then on connecte the M meilleurs.
        for l in range(min(level, self.max_level), -1, -1):
            res = self._search_layer(q, ep, ef=self.ef_construction, level=l)
            candidates = [idx for _, idx in res]
            m = self.M0 if l == 0 else self.M
            voisins = self._select_neighbors(node_id, candidates, m)
            self.layers[l].setdefault(node_id, [])
            for v in voisins:
                self.layers[l][node_id].append(v)
                self.layers[l].setdefault(v, []).append(node_id)
                # Prune the neighbourhood of v if it exceeds capacity.
                if len(self.layers[l][v]) > m:
                    self._prune(v, l, m)
            ep = candidates or ep

        if level > self.max_level:
            self.max_level = level
            self.entry = node_id

    def _select_neighbors(self, node: int, candidates: List[int],
                              m: int) -> List[int]:
        """HNSW's diversity heuristic: varied neighbours are preferred.

        Rather than blindly taking the m nearest, which might all point the same
        way, a candidate is added only if it is closer to the node than to the
        neighbours already kept. That avoids redundant links and preserves the
        "shortcuts" that are useful for navigation.
        """
        q = self.corpus[node]
        ordered = sorted(candidates, key=lambda v: -float(self.corpus[v] @ q))
        kept: List[int] = []
        for c in ordered:
            if c == node:
                continue
            if len(kept) >= m:
                break
            sim_q = float(self.corpus[c] @ q)
            # Keep c if it is closer to q than to any already-retained candidate.
            diverse = True
            for r in kept:
                if float(self.corpus[c] @ self.corpus[r]) > sim_q:
                    diverse = False
                    break
            if diverse:
                kept.append(c)
        # Top up if the heuristic pruned too hard.
        if len(kept) < m:
            for c in ordered:
                if c != node and c not in kept:
                    kept.append(c)
                if len(kept) >= m:
                    break
        return kept[:m]

    def _prune(self, node: int, level: int, m: int) -> None:
        """Garde the m voisins the closest of the node (heuristique simple)."""
        q = self.corpus[node]
        voisins = self.layers[level][node]
        scored = sorted(voisins, key=lambda v: -float(self.corpus[v] @ q))
        self.layers[level][node] = scored[:m]

    def _build(self) -> None:
        for i in range(self.corpus.shape[0]):
            self._insert(i)

    # -- the public search -----------------------------------------------------
    def search_for(self, query: np.ndarray, k: int = 10,
                   ef_search: int = 50) -> Tuple[List[int], int]:
        """Search for the k approximate nearest neighbours of `query`.

        Returns (indices, number of distances computed). That second number is
        the heart of the demonstration: it stays small even on a large corpus.
        """
        q = normalize(query)
        self.last_distances = 0
        if self.entry is None:
            return [], 0
        # Descend layer by layer, with a single entry point: the motorway.
        ep = [self.entry]
        for l in range(self.max_level, 0, -1):
            res = self._search_layer(q, ep, ef=1, level=l)
            ep = [res[0][1]] if res else ep
        # Layer 0: a wide exploration, governed by the ef_search dial.
        res = self._search_layer(q, ep, ef=max(ef_search, k), level=0)
        indices = [idx for _, idx in res[:k]]
        return indices, self.last_distances

    # -- introspection, for the labs -------------------------------------------
    def layer_sizes(self) -> List[int]:
        """The number of nodes present in each layer, bottom to top."""
        return [len(c) for c in self.layers]


# ===========================================================================
# 4. Scalar int8 quantisation (for the bonus lab)
# ===========================================================================
def quantize_int8(corpus: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compress float32 vectors into int8, dimension by dimension.

    For each dimension the interval [min, max] observed across the whole corpus
    is mapped onto [-127, 127]. One byte is stored per value instead of four, so
    memory is divided by four. Returns (int8 codes, minimum, scale); the last two
    are used to rebuild an approximation of the vectors.
    """
    minimum = corpus.min(axis=0)
    maximum = corpus.max(axis=0)
    scale = (maximum - minimum)
    scale[scale == 0] = 1.0
    codes = np.round((corpus - minimum) / scale * 254.0 - 127.0)
    codes = np.clip(codes, -127, 127).astype(np.int8)
    return codes, minimum.astype(np.float32), scale.astype(np.float32)


def dequantize_int8(codes: np.ndarray, minimum: np.ndarray,
                    scale: np.ndarray) -> np.ndarray:
    """Rebuild a float32 approximation of the quantised vectors."""
    approx = (codes.astype(np.float32) + 127.0) / 254.0 * scale + minimum
    return normalize(approx)


# ===========================================================================
# 5. IVF (Inverted File): the cluster-based family of ANN indexes
# ===========================================================================
def kmeans(vectors: np.ndarray, n_clusters: int, n_iter: int = 15,
           seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """A minimal Lloyd's k-means, used to build the IVF partition (its
    "coarse quantizer"). Returns (centroids, assignment): assignment[i] is
    the cluster index of vectors[i].

    Since our vectors are L2-normalized, ranking by cosine similarity
    (a dot product) is equivalent to ranking by Euclidean distance, so we
    reuse the same similarity convention as the rest of this module.
    """
    rng = np.random.default_rng(seed)
    n = vectors.shape[0]
    init_idx = rng.choice(n, size=min(n_clusters, n), replace=False)
    centroids = vectors[init_idx].copy()
    assignment = np.full(n, -1, dtype=np.int64)

    for iteration in range(n_iter):
        sims = vectors @ centroids.T
        new_assignment = np.argmax(sims, axis=1)
        if iteration > 0 and np.array_equal(new_assignment, assignment):
            break
        assignment = new_assignment
        for c in range(centroids.shape[0]):
            members = vectors[assignment == c]
            if len(members) > 0:
                centroids[c] = normalize(members.mean(axis=0))

    return centroids, assignment


class IVFMini:
    """Educational IVF index (Inverted File).

    The idea, in one sentence: partition the corpus into `n_clusters` groups
    with k-means, then at query time compare the query only to the centroids
    (cheap), and fully scan only the `n_probe` closest clusters (a small
    fraction of the corpus) instead of every vector.

    This is not a production index (FAISS's ``IndexIVFFlat`` is): it is a
    transparent, instrumented stand-in for the mechanism described by
    Jégou, Douze & Schmid (2011), whose original IVFADC combines exactly
    this partitioning with the product quantization seen in Lab 19-6.
    """

    def __init__(self, corpus: np.ndarray, n_clusters: int, seed: int = 42):
        self.corpus = corpus
        self.n_clusters = min(n_clusters, corpus.shape[0])
        self.centroids, self.assignment = kmeans(corpus, self.n_clusters, seed=seed)
        self.lists: Dict[int, np.ndarray] = {
            c: np.where(self.assignment == c)[0] for c in range(self.n_clusters)
        }

    def cluster_sizes(self) -> List[int]:
        """Number of vectors stored in each inverted list (for diagnostics:
        a very uneven partition means some queries will probe near-empty
        clusters while others scan a cluster almost as large as the corpus)."""
        return [len(self.lists[c]) for c in range(self.n_clusters)]

    def search(self, query: np.ndarray, k: int = 10,
               n_probe: int = 1) -> Tuple[List[int], int]:
        """Search only the `n_probe` clusters whose centroid is nearest the
        query. Returns (indices, comparisons) where comparisons counts both
        the cheap centroid comparisons and the full scan of the probed
        clusters, exactly as ``exact_search`` counts the full corpus.
        """
        query = normalize(query)
        centroid_sims = self.centroids @ query
        probed = np.argsort(-centroid_sims)[:n_probe]

        candidates = (np.concatenate([self.lists[c] for c in probed])
                      if len(probed) else np.array([], dtype=int))
        if len(candidates) == 0:
            return [], self.n_clusters

        sims = self.corpus[candidates] @ query
        order = np.argsort(-sims)[:k]
        comparisons = self.n_clusters + len(candidates)
        return candidates[order].tolist(), comparisons
