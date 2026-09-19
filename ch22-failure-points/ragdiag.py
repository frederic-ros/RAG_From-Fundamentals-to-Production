# -*- coding: utf-8 -*-
"""
ragdiag.py — shared building blocks for the labs of Chapter 22 (the points of failure).

Chapter 22 does not build: it DIAGNOSES. It draws the map of the ways a
retrieval system fails, sorted into three moments — BEFORE the question
(ingestion, chunking, representation), DURING the search (intent, ranking, bias,
consolidation), AT the answer (context not used, redundancy, format,
incompleteness, misleading assurance, instability). Its thesis: four of the seven
"historical" failures are RETRIEVAL failures, visible WITHOUT any LLM.

This module provides, transparently, the minimal pipeline that will be
sabotaged, measured and diagnosed:

  - Search: a retrieval engine (TF-IDF by default, or sentence-transformers if
    it is available);
  - the SABOTAGE LEVERS of the chapter, one per failure, reproducible without an
    LLM (missing content, shattered chunking, misleading representation, missed
    at ranking, context not used, incompleteness, instability);
  - an ANSWER GENERATOR: Ollama if present (a real local LLM), otherwise a
    deterministic extractive generator, so as to stay reproducible;
  - RAGAS-style JUDGES: faithfulness, context precision, and an LLM judge
    (Ollama) with a deterministic fallback;
  - retrieval METRICS: mrr(), recall_at_k(), ndcg_at_k(), rank_of().

As close as possible to real usage
----------------------------------
At this point in the book — diagnosis, evaluation, agents — real usage is what
matters. This module therefore follows the same contract as Chapter 21 for the
embeddings, extended to REASONING:

  * RETRIEVAL:  sentence-transformers if present, otherwise deterministic TF-IDF;
  * GENERATION: Ollama (a local model, for instance llama3.2) if present,
                otherwise a deterministic extractive fallback;
  * JUDGE:      Ollama if present (the real "LLM-as-judge" of RAGAS), otherwise a
                deterministic judge based on term overlap.

The teaching point of each failure appears clearly OFFLINE; as soon as Ollama is
running, you get the production behaviour, with answers and judgements from a
real model. No API key is ever required: Ollama runs locally.
"""

from __future__ import annotations

import os
import re
from typing import List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# Optional detection of an embedding model (retrieval)
# ===========================================================================
_ST_MODEL = None
_MODE = None


def mode_retrieval() -> str:
    """The active retrieval mode: 'sentence-transformers' or 'tfidf'."""
    global _ST_MODEL, _MODE
    if _MODE is not None:
        return _MODE
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2")
        m.encode(["test"])
        _ST_MODEL, _MODE = m, "sentence-transformers"
    except Exception:
        _MODE = "tfidf"
    return _MODE


# ===========================================================================
# Optional detection of a local LLM (Ollama) — the "real usage" path
# ===========================================================================
# Default model, overridable through the OLLAMA_MODEL environment variable.
# For instance: OLLAMA_MODEL=llama3.2:3b python lab22-2_ragas.py
_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
_OLLAMA_OK: Optional[bool] = None


def ollama_available() -> bool:
    """True if an Ollama server answers AND serves the requested model.

    The connection is actually exercised, with a short call, so as not to
    announce a mode that would fail later. When absent, the whole module falls
    back to the deterministic path: the labs run with nothing installed.
    """
    global _OLLAMA_OK
    if _OLLAMA_OK is not None:
        return _OLLAMA_OK
    try:
        import ollama  # noqa: F401
        # A minimal call: if the server or the model is missing, this raises.
        ollama.chat(
            model=_OLLAMA_MODEL,
            messages=[{"role": "user", "content": "ping"}],
            options={"num_predict": 1, "temperature": 0.0},
        )
        _OLLAMA_OK = True
    except Exception:
        _OLLAMA_OK = False
    return _OLLAMA_OK


def generation_mode() -> str:
    """Generation and judgement mode: 'ollama' (a real local LLM) or 'extractive'."""
    return "ollama" if ollama_available() else "extractive"


def _llm(prompt: str, *, temperature: float = 0.0, num_predict: int = 256) -> str:
    """Call the local LLM (Ollama). Do NOT call without checking availability.

    temperature=0.0 by default: the labs are meant to be reproducible. The
    instability lab varies this parameter ON PURPOSE.
    """
    import ollama
    r = ollama.chat(
        model=_OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": temperature, "num_predict": num_predict},
    )
    return r["message"]["content"].strip()


# ===========================================================================
# The search engine (retrieval)
# ===========================================================================
class Search:
    """Index a corpus and rank the documents by relevance to a query.

    In 'tfidf' mode (the fallback) the index is lexical, and that is precisely
    what makes the retrieval failures of the chapter visible — missing content,
    shattered chunking, missed at ranking — without any LLM. In
    'sentence-transformers' mode real dense embeddings are used, which is useful
    for the "misleading representation" failure, a flaw of the vector space.
    """

    def __init__(self, corpus: Sequence[str]) -> None:
        self.corpus = list(corpus)
        self.mode = mode_retrieval()
        if self.mode == "sentence-transformers":
            self._vecs = _ST_MODEL.encode(self.corpus, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            # Single-character tokens are kept ("A", "B", part codes):
            # otherwise "pump P-12" and "pump P-42" would collapse together at
            # tokenisation time.
            self._vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                        token_pattern=r"(?u)\b\w+\b")
            self._mat = self._vec.fit_transform(self.corpus)

    def scores(self, query: str) -> np.ndarray:
        if self.mode == "sentence-transformers":
            q = _ST_MODEL.encode([query], normalize_embeddings=True)[0]
            return self._vecs @ q
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([query])
        return cosine_similarity(q, self._mat)[0]

    def rank(self, query: str, k: Optional[int] = None,
             noise: float = 0.0, seed: Optional[int] = None
             ) -> List[Tuple[int, float]]:
        """Rank the corpus for a query: [(index, score)], decreasing.

        `noise` injects Gaussian randomness into the scores, for the instability
        lab: tiny differences are enough to flip the order of near-identical
        fragments. `seed` makes that noise reproducible when needed.
        """
        s = self.scores(query).astype(float)
        if noise > 0.0:
            rng = np.random.default_rng(seed)
            s = s + rng.normal(0.0, noise, size=s.shape)
        order = np.argsort(-s)
        res = [(int(i), float(s[i])) for i in order]
        return res[:k] if k else res


# ===========================================================================
# SABOTAGE LEVERS — one reproducible failure at a time
# ===========================================================================
# Lab 22-1 starts from a healthy corpus, then pulls ONE lever at a time to
# provoke ONE failure, and observes the symptom. Each lever returns a modified
# corpus, and possibly some metadata, without touching the original.

def sabotage_missing_content(frags: List[dict], target_id: int
                             ) -> Tuple[List[dict], str]:
    """BEFORE the question — Missing content: the good document is removed from
    the index.

    Symptom: a recall failure. The good fragment is not even a candidate; for
    want of anything better, the model cobbles an answer out of an off-topic
    neighbour.
    """
    remaining = [f for f in frags if f["id"] != target_id]
    return remaining, ("The relevant document was removed from the index: "
                       "it can no longer be retrieved (a recall failure).")


def sabotage_shattered_chunking(text: str, size: int = 7) -> List[str]:
    """BEFORE the question — Shattered chunking: a text is cut into fragments
    that are too small, in packets of `size` words. The complete answer is then
    spread over several pieces; none of them, taken alone, holds it. Symptom:
    every fragment looks relevant, but the whole answer is never recovered in
    one go.
    """
    words = text.split()
    return [" ".join(words[i:i + size]) for i in range(0, len(words), size)]


def sabotage_ranking(frags: List[dict], target_id: int, decoys: List[dict]
                     ) -> Tuple[List[dict], str]:
    """DURING the search — Missed at ranking: the good document is drowned under
    decoys that are semantically very close. The good fragment IS retrieved, but
    ranked too low to be passed to the model. Symptom: the answer existed, the
    retrieval had it, but the ordering set it aside.
    """
    return frags + decoys, ("Near-synonymous decoys were added: the good "
                            "document is pushed further down the ranking.")


def context_with_distractors(good: str, distractors: List[str],
                             position: str = "middle") -> List[str]:
    """AT the answer — Context not used: the good fragment is placed in the
    MIDDLE of a long, noisy context, the "lost in the middle" effect. The good
    passage is there, but drowned.

    `position` is one of 'start', 'middle', 'end', so that the effect of the
    placement can be observed.
    """
    if position == "start":
        return [good] + distractors
    if position == "end":
        return distractors + [good]
    middle = len(distractors) // 2
    return distractors[:middle] + [good] + distractors[middle:]


# ===========================================================================
# ANSWER GENERATION — Ollama (a real LLM) or an extractive fallback
# ===========================================================================
_ANSWER_TEMPLATE = (
    "You are a maintenance assistant. Using ONLY the extracts provided, answer "
    "the question briefly and factually. If the extracts do not contain the "
    "answer, say so plainly.\n\n"
    "Extracts:\n{context}\n\nQuestion: {question}\nAnswer:"
)


def generate_answer(question: str, context: Sequence[str]) -> str:
    """Generate an answer from a context.

    With Ollama, a real local LLM writes it, which is the production behaviour.
    Without Ollama, a deterministic extractive fallback returns the passages
    most tied to the question, which is enough to REVEAL the failures —
    incompleteness, context not used — without depending on a model.
    """
    ctx = "\n".join(f"- {c}" for c in context)
    if ollama_available():
        return _llm(_ANSWER_TEMPLATE.format(context=ctx, question=question),
                    temperature=0.0, num_predict=200)
    # --- Deterministic extractive fallback ---------------------------------
    if not context:
        return ("I cannot find the information in the documents supplied "
                "(no relevant extract).")
    qtok = set(_tokens(question))
    ranked = sorted(context,
                     key=lambda c: len(qtok & set(_tokens(c))), reverse=True)
    best = [c for c in ranked if qtok & set(_tokens(c))][:2]
    if not best:
        return ("I cannot find the information in the documents supplied "
                "(the extracts are off the subject).")
    return " ".join(best)


# ===========================================================================
# RAGAS-STYLE JUDGES — faithfulness, context precision, LLM judge
# ===========================================================================
def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[\.\!\?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def context_precision(context: Sequence[str], relevant: Sequence[str]) -> float:
    """RAGAS — context precision (a proxy): the share of the supplied extracts
    that are genuinely relevant. Low means the model was drowned in noise —
    retrieval bias, or context not used. `relevant` holds the reference texts.
    """
    if not context:
        return 0.0
    ref = [set(_tokens(p)) for p in relevant]
    good = 0
    for c in context:
        ct = set(_tokens(c))
        # "Relevant" means a strong overlap with at least one reference text.
        if any(len(ct & r) / max(1, len(r)) >= 0.5 for r in ref):
            good += 1
    return good / len(context)


def faithfulness(answer: str, context: Sequence[str]) -> float:
    """RAGAS — faithfulness: is the answer GROUNDED in the context supplied?

    With Ollama, an LLM judge checks each assertion, the real "LLM-as-judge".
    Without Ollama, a deterministic proxy: the share of the answer's sentences
    whose content words are covered by the context. Low means the model
    embroidered — "false but confident".
    """
    sentences = _sentences(answer)
    if not sentences:
        return 1.0
    if ollama_available():
        return _faithfulness_llm(sentences, context)
    # --- Deterministic fallback --------------------------------------------
    ctx_vocab = set()
    for c in context:
        ctx_vocab |= set(_tokens(c))
    stop = _STOP_WORDS
    grounded = 0
    for sentence in sentences:
        content = [w for w in _tokens(sentence) if w not in stop and len(w) > 2]
        if not content:
            grounded += 1
            continue
        covered = sum(1 for w in content if w in ctx_vocab)
        if covered / len(content) >= 0.6:
            grounded += 1
    return grounded / len(sentences)


def _faithfulness_llm(sentences: List[str], context: Sequence[str]) -> float:
    """LLM judge (Ollama): for each assertion, is it supported by the context?"""
    ctx = "\n".join(f"- {c}" for c in context)
    supported = 0
    for sentence in sentences:
        prompt = (
            "Here are some reference extracts, then an assertion. Is the "
            "assertion DIRECTLY supported by the extracts? Answer YES or NO, "
            "nothing else.\n\n"
            f"Extracts:\n{ctx}\n\nAssertion: {sentence}\nAnswer (YES/NO):"
        )
        verdict = _llm(prompt, temperature=0.0, num_predict=3).upper()
        if verdict.startswith("YES"):
            supported += 1
    return supported / len(sentences)


def covers_question(answer: str, parts: Sequence[str]) -> Tuple[float, List[str]]:
    """RAGAS-like — coverage of the expected parts, for incompleteness.

    With Ollama, the LLM judge says which parts are missing, a real judgement.
    Without Ollama, a part is "covered" if its label appears in the answer.
    Returns (coverage_rate, missing_parts).
    """
    if ollama_available():
        return _covers_question_llm(answer, parts)
    # Deterministic fallback: a part is "covered" if its label appears verbatim,
    # case-insensitively, in the answer. Overlap on isolated tokens is avoided
    # ("P-12" -> {p, 12}), which would make "p" match everywhere.
    normalised = answer.lower()
    missing = [p for p in parts if p.lower() not in normalised]
    covered = len(parts) - len(missing)
    return (covered / max(1, len(parts)), missing)


def _covers_question_llm(answer: str, parts: Sequence[str]) -> Tuple[float, List[str]]:
    listed = ", ".join(parts)
    prompt = (
        "An answer is expected to address ALL of these subjects: " + listed + ".\n"
        "Here is the answer:\n" + answer + "\n\n"
        "List ONLY the subjects NOT addressed, separated by commas. "
        "If all of them are addressed, answer STRICTLY: NONE."
    )
    verdict = _llm(prompt, temperature=0.0, num_predict=40)
    if "NONE" in verdict.upper():
        return (1.0, [])
    raw = [v.strip() for v in re.split(r"[,;]", verdict) if v.strip()]
    missing = [p for p in parts if any(p.lower() in b.lower() or b.lower() in p.lower()
                                       for b in raw)]
    covered = len(parts) - len(missing)
    return (covered / max(1, len(parts)), missing)


# English stop words, filtered out before measuring whether a sentence is
# grounded in the context. Without this list, "the", "of" and "and" would count
# as content words and would inflate every overlap score.
_STOP_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "by", "with", "without",
    "and", "or", "is", "are", "was", "were", "be", "been", "this", "that",
    "these", "those", "it", "its", "he", "she", "they", "them", "their",
    "which", "who", "what", "when", "where", "how", "not", "no", "more",
    "must", "may", "can", "shall", "should", "would", "has", "have", "had",
    "at", "as", "from", "into", "than", "then", "there", "here", "all", "any",
    "each", "every", "per", "out", "up", "if", "so", "such", "but", "also",
}


# ===========================================================================
# Metrics of retrieval
# ===========================================================================
def rank_of(ranking: Sequence[int], doc: int) -> Optional[int]:
    """The 1-based rank of a document in a ranking, or None if it is absent."""
    for r, d in enumerate(ranking, start=1):
        if d == doc:
            return r
    return None


def mrr(ranking: Sequence[int], relevant: Sequence[int]) -> float:
    """Mean reciprocal rank: 1 over the rank of the first relevant document."""
    rel = set(relevant)
    for rank, doc in enumerate(ranking, start=1):
        if doc in rel:
            return 1.0 / rank
    return 0.0


def recall_at_k(ranking: Sequence[int], relevant: Sequence[int],
                k: int = 5) -> float:
    """Recall@k: the share of relevant documents present in the top k."""
    rel = set(relevant)
    if not rel:
        return 1.0
    found = sum(1 for d in ranking[:k] if d in rel)
    return found / len(rel)


def ndcg_at_k(ranking: Sequence[int], relevant: Sequence[int],
              k: int = 5) -> float:
    """nDCG@k: rewards the relevant documents the more highly they are placed.

    Binary relevance, 1 if relevant. The DCG is normalised by the ideal DCG.
    """
    rel = set(relevant)
    dcg = 0.0
    for i, doc in enumerate(ranking[:k], start=1):
        if doc in rel:
            dcg += 1.0 / np.log2(i + 1)
    ideal = sum(1.0 / np.log2(i + 1) for i in range(1, min(len(rel), k) + 1))
    return float(dcg / ideal) if ideal > 0 else 0.0
