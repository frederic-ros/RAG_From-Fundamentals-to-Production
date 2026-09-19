# -*- coding: utf-8 -*-
"""
embeddings.py — embeddings and similarity, shared by the labs of Chapter 17.

Chapter 17 needs two things from embeddings:

  1. comparing two sentences (semantic chunking: cut when the similarity
     drops);
  2. indexing chunks and answering a query (measuring retrieval before and
     after a better chunking).

As in Chapter 16, there are two implementations, chosen automatically:

  - sentence-transformers (all-MiniLM-L6-v2) if present and loadable offline;
  - otherwise a deterministic TF-IDF fallback (scikit-learn), with no network
    and no API key.

The teaching point of the chapter — a good CHUNKING makes information findable,
a bad one makes it invisible — holds either way: it is about how you cut, not
about the quality of the vectors.

An important honesty note: in TF-IDF mode a "sentence embedding" is a
bag-of-words vector. That is enough to show the DROP in similarity between two
sentences about different subjects, and therefore enough to drive semantic
chunking. With sentence-transformers you get real dense contextualised vectors.
"""

from __future__ import annotations

from typing import List, Tuple

_MODEL = None
_MODE = None


def _load_transformer() -> bool:
    global _MODEL, _MODE
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        model.encode(["test"])
        _MODEL = model
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
    """Return 'sentence-transformers' or 'tfidf'."""
    _init()
    return _MODE


def embed_texts(texts: List[str]):
    """Return a matrix of vectors, one per text, L2-normalised.

    In TF-IDF mode the vocabulary is fitted on the whole set of texts supplied,
    so the vectors returned are comparable WITH EACH OTHER, in one space.
    """
    _init()
    if _MODE == "sentence-transformers":
        return _MODEL.encode(texts, normalize_embeddings=True)
    else:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer

        vect = TfidfVectorizer()
        mat = vect.fit_transform(texts).toarray()
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return mat / norms


def cosine(u, v) -> float:
    """Cosine similarity between two vectors."""
    import numpy as np

    u = np.asarray(u, dtype=float)
    v = np.asarray(v, dtype=float)
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu == 0 or nv == 0:
        return 0.0
    return float(u @ v / (nu * nv))


class SimilarityEngine:
    """Index chunks and answer queries by cosine similarity."""

    def __init__(self, chunks: List[str]):
        _init()
        self.chunks = list(chunks)
        self._mode = _MODE
        if self._mode == "sentence-transformers":
            self._vectors = _MODEL.encode(self.chunks, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer

            self._vect = TfidfVectorizer()
            self._matrix = self._vect.fit_transform(self.chunks)

    def search_for(self, query: str, k: int = 3) -> List[Tuple[int, float]]:
        """Indices of the k closest chunks, sorted, with their score."""
        if self._mode == "sentence-transformers":
            import numpy as np

            q = _MODEL.encode([query], normalize_embeddings=True)[0]
            scores = self._vectors @ q
            order = np.argsort(-scores)[:k]
            return [(int(i), float(scores[i])) for i in order]
        else:
            from sklearn.metrics.pairwise import cosine_similarity

            qv = self._vect.transform([query])
            scores = cosine_similarity(qv, self._matrix)[0]
            order = scores.argsort()[::-1][:k]
            return [(int(i), float(scores[i])) for i in order]

    def best_score(self, query: str) -> float:
        """Similarity score of the best chunk, for comparing strategies."""
        res = self.search_for(query, k=1)
        return res[0][1] if res else 0.0


# ---------------------------------------------------------------------------
# Late Chunking — contextualise BEFORE splitting, on the vectors
# ---------------------------------------------------------------------------
def late_chunking(document: str, chunks: List[str]):
    """Return one vector per chunk, Late Chunking style.

    The principle of the chapter: the WHOLE document is contextualised first,
    and the vector of each chunk is then derived while taking the whole document
    into account. Each chunk therefore keeps the trace of what was read
    elsewhere — "the P-42 pump" mentioned ten pages earlier.

    Two implementations:
      - sentence-transformers: the whole document is encoded into token vectors,
        each of which sees the entire context, and the token vectors making up
        each chunk are then averaged. That is real Late Chunking.
      - TF-IDF (fallback): the effect is APPROXIMATED by mixing the chunk's own
        vector with the global vector of the document. That is not the exact
        mechanism, but it reproduces the observable SYMPTOM: a chunk "inherits"
        the context of the document. The lab states this approximation openly.
    """
    _init()
    if _MODE == "sentence-transformers":
        return _late_chunking_dense(document, chunks)
    return _late_chunking_tfidf(document, chunks)


def _late_chunking_dense(document: str, chunks: List[str]):
    import numpy as np

    # Tokenisation plus token embeddings contextualised over the whole document.
    tok = _MODEL.tokenizer(document, return_offsets_mapping=True,
                           truncation=True, max_length=8192)
    offsets = tok["offset_mapping"]
    # Embeddings per token, the model output before pooling.
    import torch

    enc = _MODEL.tokenize([document])
    with torch.no_grad():
        output = _MODEL.forward(enc)
    token_emb = output["token_embeddings"][0].cpu().numpy()  # (n_tokens, d)

    # For each chunk, locate its tokens by character position and average them.
    vectors = []
    for chunk in chunks:
        start = document.find(chunk[:30])   # approximate anchoring
        end = start + len(chunk) if start >= 0 else len(document)
        idxs = [i for i, (a, b) in enumerate(offsets) if a >= start and b <= end and b > a]
        if not idxs:
            idxs = list(range(len(token_emb)))
        v = token_emb[idxs].mean(axis=0)
        n = np.linalg.norm(v)
        vectors.append(v / n if n else v)
    return np.array(vectors)


def _late_chunking_tfidf(document: str, chunks: List[str]):
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer

    # A TF-IDF space shared by the document and the chunks.
    vect = TfidfVectorizer()
    vect.fit([document] + chunks)
    doc_vec = vect.transform([document]).toarray()[0]
    chunk_vecs = vect.transform(chunks).toarray()

    # Approximation: each chunk inherits a share of the document's global context.
    alpha = 0.7   # weight of the chunk itself; (1 - alpha) is inherited context
    vectors = []
    for cv in chunk_vecs:
        v = alpha * cv + (1 - alpha) * doc_vec
        n = np.linalg.norm(v)
        vectors.append(v / n if n else v)
    return np.array(vectors)


def compare_late_chunking(document: str, chunks: List[str], query: str) -> float:
    """Late Chunking score of the best chunk for a query, in a shared space.

    Document, chunks and query are all embedded in the SAME space, so that the
    vectors are comparable. This is the API the labs should use for Late
    Chunking; it avoids the vocabulary traps of separate spaces.
    """
    _init()
    if _MODE == "sentence-transformers":
        vecs = _late_chunking_dense(document, chunks)
        q = _MODEL.encode([query], normalize_embeddings=True)[0]
        scores = [cosine(q, v) for v in vecs]
        return float(max(scores)) if scores else 0.0

    # TF-IDF: a single vectoriser for the document, the chunks and the query.
    from sklearn.feature_extraction.text import TfidfVectorizer

    vect = TfidfVectorizer()
    vect.fit([document] + chunks + [query])
    doc_vec = vect.transform([document]).toarray()[0]
    chunk_vecs = vect.transform(chunks).toarray()
    q = vect.transform([query]).toarray()[0]

    alpha = 0.7   # share of the chunk; (1 - alpha) is context inherited from the document
    scores = []
    for cv in chunk_vecs:
        v = alpha * cv + (1 - alpha) * doc_vec
        scores.append(cosine(q, v))
    return float(max(scores)) if scores else 0.0


def best_shared_score(chunks: List[str], query: str) -> float:
    """Score of the best chunk for a query, in a shared space.

    Unlike SimilarityEngine, which fits its space on the chunks alone, the query
    is included in the vocabulary here, so that scores are comparable from one
    chunking strategy to another.
    """
    _init()
    if _MODE == "sentence-transformers":
        import numpy as np

        q = _MODEL.encode([query], normalize_embeddings=True)[0]
        vecs = _MODEL.encode(chunks, normalize_embeddings=True)
        scores = vecs @ q
        return float(np.max(scores)) if len(scores) else 0.0

    from sklearn.feature_extraction.text import TfidfVectorizer

    vect = TfidfVectorizer()
    vect.fit(chunks + [query])
    chunk_vecs = vect.transform(chunks).toarray()
    q = vect.transform([query]).toarray()[0]
    scores = [cosine(q, cv) for cv in chunk_vecs]
    return float(max(scores)) if scores else 0.0
