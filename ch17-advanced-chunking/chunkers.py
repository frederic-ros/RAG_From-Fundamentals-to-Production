# -*- coding: utf-8 -*-
"""
chunkers.py — the chunking strategies of Chapter 17, gathered in one place.

The chapter sets a BLIND chunking (fixed size) against chunkings that are AWARE
of meaning and of structure. This module gathers those strategies so that the
labs can compare them on the same corpus:

    split_fixed()        — fixed size in characters (the "semantic confetti").
    split_by_sentences() — a clean cut at sentence boundaries.
    split_structural()   — follows the Markdown outline (# and ## headings).
    split_semantic()     — cuts where the similarity between sentences DROPS.

No heavy dependency: sentence segmentation is done by a small offline rule, with
no nltk download. Semantic chunking relies on the embeddings.py module
(sentence-transformers if available, TF-IDF otherwise).
"""

from __future__ import annotations

import re
from typing import List, Tuple

import embeddings


# ---------------------------------------------------------------------------
# Sentence segmentation — a simple offline rule, without nltk.
# ---------------------------------------------------------------------------
def split_into_sentences(text: str) -> List[str]:
    """Split a text into sentences on strong punctuation (. ! ?).

    Deliberately simple: enough for the lab corpus, and with no external
    resource to download.
    """
    text = text.replace("\n", " ")
    # Cut after . ! ? followed by a space and a capital letter or a digit.
    pieces = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-ÖØ-Þ0-9])", text.strip())
    return [p.strip() for p in pieces if p.strip()]


# ---------------------------------------------------------------------------
# 1. FIXED-SIZE chunking (the problem of the chapter)
# ---------------------------------------------------------------------------
def split_fixed(text: str, size: int = 50, overlap: int = 0) -> List[str]:
    """Cut mechanically every `size` characters.

    This is the "blind" cut: it ignores sentences, headings and meaning. It cuts
    in the middle of a word or of a number — hence the "silence" of the chapter.
    """
    text = re.sub(r"\s+", " ", text.replace("\n", " ")).strip()
    chunks = []
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        chunks.append(text[start:start + size])
    return chunks


# ---------------------------------------------------------------------------
# 2. Chunking BY SENTENCES (already much better)
# ---------------------------------------------------------------------------
def split_by_sentences(text: str, sentences_per_chunk: int = 1) -> List[str]:
    """Group whole sentences, never cutting one in two."""
    sentences = split_into_sentences(text)
    chunks = []
    for i in range(0, len(sentences), sentences_per_chunk):
        chunks.append(" ".join(sentences[i:i + sentences_per_chunk]))
    return chunks


# ---------------------------------------------------------------------------
# 3. STRUCTURAL chunking (follows the Markdown outline)
# ---------------------------------------------------------------------------
def split_structural(markdown: str) -> List[Tuple[str, str]]:
    """Split a Markdown document by section (# / ## headings).

    Returns a list of (section_title, content). Each section stays whole: the
    structure of the document IS the chunking plan.
    """
    lines = markdown.splitlines()
    sections: List[Tuple[str, List[str]]] = []
    current_title = "(preamble)"
    buffer: List[str] = []

    def flush():
        if buffer:
            sections.append((current_title, list(buffer)))
            buffer.clear()

    for line in lines:
        if re.match(r"^#{1,6}\s+", line):    # a Markdown heading
            flush()
            current_title = line.lstrip("#").strip()
            buffer.append(line.strip())
        else:
            if line.strip():
                buffer.append(line.strip())
    flush()

    # Merge title and content into one readable chunk.
    chunks = []
    for title, content in sections:
        chunks.append((title, " ".join(content)))
    return chunks


# ---------------------------------------------------------------------------
# 4. SEMANTIC chunking (cuts where the similarity drops)
# ---------------------------------------------------------------------------
def split_semantic(text: str, threshold: float = 0.25,
                   adaptive: bool = False) -> Tuple[List[str], List[float]]:
    """Split a raw text where two consecutive sentences diverge.

    The algorithm of the chapter:
      1. split into sentences;
      2. embed each sentence;
      3. measure the cosine similarity between consecutive sentences;
      4. place a boundary when that similarity falls BELOW the threshold.

    `threshold`: an absolute similarity threshold (the default mode).
    `adaptive` : if True, the threshold is computed from the DISTRIBUTION of the
        similarities in the text, so that boundaries fall at the most marked
        dips. Useful when the scale of the similarities depends on the embedding
        model (dense versus TF-IDF): you cut at the RELATIVE breaks rather than
        at an arbitrary absolute value.

    Returns (chunks, similarities_between_consecutive_sentences).
    """
    sentences = split_into_sentences(text)
    if len(sentences) <= 1:
        return sentences, []

    vectors = embeddings.embed_texts(sentences)
    similarities = [embeddings.cosine(vectors[i], vectors[i + 1])
                    for i in range(len(sentences) - 1)]

    if adaptive:
        threshold = _adaptive_threshold(similarities)

    chunks: List[str] = []
    current = [sentences[0]]
    for i, sim in enumerate(similarities):
        if sim < threshold:      # change of subject -> close the chunk
            chunks.append(" ".join(current))
            current = [sentences[i + 1]]
        else:
            current.append(sentences[i + 1])
    if current:
        chunks.append(" ".join(current))
    return chunks, similarities


def _adaptive_threshold(similarities: List[float]) -> float:
    """Place the threshold below the mean by half a standard deviation, so that
    a cut happens only at dips markedly deeper than the norm of the text.

    A simple but robust heuristic: it adapts to the scale of each embedding
    model, where an absolute threshold of 0.25 would be right for one and wrong
    for the other.
    """
    import numpy as np

    arr = np.asarray(similarities, dtype=float)
    return float(arr.mean() - 0.5 * arr.std())
