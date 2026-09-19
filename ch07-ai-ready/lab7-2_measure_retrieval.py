# -*- coding: utf-8 -*-
"""
Lab 7-2 — Measuring the retrieval gain: before and after (Julien)

Learning objective
------------------
Prove, with figures, that an AI-ready document improves the search WITHOUT
changing the model. The hostile sheet is indexed on one side, the AI-ready sheet
on the other, the same set of questions is then run against both, and the recall
compared.

Three vector search engines are offered, to show that the RESULT does not depend
on the technology chosen:

  1. in-house : simple lexical embeddings plus a cosine (zero dependency, as in
                Chapter 4);
  2. faiss    : a FAISS index, if faiss-cpu is installed;
  3. chroma   : ChromaDB, if chromadb is installed.

The script detects what is available and runs the measurements on each engine
present. With nothing installed, the in-house engine is enough to conclude.

Run generate_sample_docs.py first.
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

DOCS = Path(__file__).resolve().parent / "sample_docs"


# ---------------------------------------------------------------------------
# Cutting a pivot into passages (chunks)
# ---------------------------------------------------------------------------
def pivot_to_chunks(pivot: Dict) -> List[str]:
    chunks = []
    for s in pivot.get("sections", []):
        title = s.get("title", "").strip()
        content = s.get("content", "").strip()
        text = (title + ". " + content).strip(". ").strip()
        if text:
            chunks.append(text)
    if not chunks:  # the hostile case: a single block
        block = " ".join(s.get("content", "") for s in pivot.get("sections", []))
        if block.strip():
            chunks = [block.strip()]
    return chunks


# ---------------------------------------------------------------------------
# The in-house embedding: a normalised bag of words (lexical, deterministic)
# ---------------------------------------------------------------------------
# A short stop-word list. Without it, the naive bag of words is dominated by
# "the" and "of": in short English passages the determiners outweigh the content
# words, and every question lands on whichever chunk happens to have the most
# articles. Filtering them is what makes a lexical engine usable at all.
STOP_WORDS = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or",
              "is", "are", "be", "it", "its", "this", "that", "what", "which",
              "should", "do", "does", "after", "before", "by", "with"}


def tokenize(text: str) -> List[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in STOP_WORDS]


def build_vocabulary(texts: List[str]) -> Dict[str, int]:
    vocab: Dict[str, int] = {}
    for t in texts:
        for word in tokenize(t):
            vocab.setdefault(word, len(vocab))
    return vocab


def vectorize(text: str, vocab: Dict[str, int]) -> List[float]:
    vec = [0.0] * len(vocab)
    for word in tokenize(text):
        if word in vocab:
            vec[vocab[word]] += 1.0
    return vec


def cosine(u: List[float], v: List[float]) -> float:
    num = sum(a * b for a, b in zip(u, v))
    nu = math.sqrt(sum(a * a for a in u))
    nv = math.sqrt(sum(b * b for b in v))
    if nu == 0 or nv == 0:
        return 0.0
    return num / (nu * nv)


# ---------------------------------------------------------------------------
# The search engines
# ---------------------------------------------------------------------------
def homemade_search(chunks: List[str], question: str) -> Tuple[int, float]:
    if not chunks:
        return -1, 0.0
    vocab = build_vocabulary(chunks + [question])
    vq = vectorize(question, vocab)
    scores = [cosine(vq, vectorize(c, vocab)) for c in chunks]
    best = max(range(len(scores)), key=lambda i: scores[i])
    return best, scores[best]


def search_faiss(chunks: List[str], question: str) -> Tuple[int, float]:
    import faiss
    import numpy as np

    vocab = build_vocabulary(chunks + [question])
    mat = np.array([vectorize(c, vocab) for c in chunks], dtype="float32")
    # L2 normalisation, so that the dot product equals the cosine.
    faiss.normalize_L2(mat)
    index = faiss.IndexFlatIP(mat.shape[1])
    index.add(mat)
    vq = np.array([vectorize(question, vocab)], dtype="float32")
    faiss.normalize_L2(vq)
    scores, idx = index.search(vq, 1)
    return int(idx[0][0]), float(scores[0][0])


def search_chroma(chunks: List[str], question: str) -> Tuple[int, float]:
    import chromadb

    # We supply OUR OWN embeddings (a bag of words), so that no model has to
    # be downloaded: ChromaDB is used here purely as a vector index.
    vocab = build_vocabulary(chunks + [question])
    emb_chunks = [vectorize(c, vocab) for c in chunks]
    emb_q = vectorize(question, vocab)

    client = chromadb.Client()
    name = "lab72_" + str(abs(hash(" ".join(chunks))) % 100000)
    try:
        client.delete_collection(name)
    except Exception:
        pass
    col = client.create_collection(name, metadata={"hnsw:space": "cosine"})
    col.add(
        ids=[f"c{i}" for i in range(len(chunks))],
        embeddings=emb_chunks,
        documents=chunks,
    )
    res = col.query(query_embeddings=[emb_q], n_results=1)
    doc = res["documents"][0][0]
    idx = chunks.index(doc)
    distance = res["distances"][0][0]
    return idx, 1.0 - distance  # distance cosinus -> similarity


import importlib.util

ENGINES = [("in-house", homemade_search)]
if importlib.util.find_spec("faiss") is not None:
    ENGINES.append(("faiss", search_faiss))
if importlib.util.find_spec("chromadb") is not None:
    ENGINES.append(("chroma", search_chroma))


# ---------------------------------------------------------------------------
# The evaluation set: a question -> the word(s) expected in the right passage
# ---------------------------------------------------------------------------
QUESTIONS = [
    ("Which procedure should be consulted before work?", ["assessment", "rams", "preliminary"]),
    ("What is the tightening torque of the MX-201?", ["torque", "85"]),
    ("What should be done after the intervention?", ["closing", "reset", "counter"]),
    ("What is the maximum pressure of the MX-200?", ["12.5", "pressure"]),
]


def passage_is_relevant(chunk: str, expected: List[str], other_questions: List) -> bool:
    """A passage is relevant if it holds the answer AND stays focused.

    A catch-all block that ALSO holds the keywords of several other questions
    discriminates nothing: it "answers" everything, and therefore nothing. It is
    penalised, because that is exactly the defect of an undivided hostile
    document.
    """
    c = chunk.lower()
    holds_answer = any(a.lower() in c for a in expected)
    if not holds_answer:
        return False
    # Count how many OTHER questions this same passage also covers.
    others_covered = 0
    for _, other_expected in other_questions:
        if other_expected is expected:
            continue
        if any(a.lower() in c for a in other_expected):
            others_covered += 1
    # A focused passage covers few other subjects; a blob covers them all.
    return others_covered <= 1


def measure(engine_name, function, chunks: List[str]) -> float:
    hits = 0
    for question, expected in QUESTIONS:
        idx, _ = function(chunks, question)
        if 0 <= idx < len(chunks) and passage_is_relevant(chunks[idx], expected, QUESTIONS):
            hits += 1
    return hits / len(QUESTIONS)


def main() -> None:
    print("=" * 78)
    print("Lab 7-2 — Measuring the retrieval gain: before and after (Julien)")
    print("=" * 78)

    if not (DOCS / "julien_hostile_sheet.json").exists():
        print("\nDocuments not found. Run this first: python generate_sample_docs.py")
        return

    hostile = json.loads((DOCS / "julien_hostile_sheet.json").read_text(encoding="utf-8"))
    ai_ready = json.loads((DOCS / "julien_ai_ready_sheet.json").read_text(encoding="utf-8"))

    hostile_chunks = pivot_to_chunks(hostile)
    ready_chunks = pivot_to_chunks(ai_ready)

    print(f"\nPassages indexed — hostile: {len(hostile_chunks)} | "
          f"AI-ready: {len(ready_chunks)}")
    print(f"Questions in the evaluation set: {len(QUESTIONS)}")
    print(f"Engines available: {', '.join(name for name, _ in ENGINES)}")

    print("\n" + "=" * 78)
    print(f"{'Engine':10s} | {'hostile recall':16s} | {'AI-ready recall':16s} | gain")
    print("-" * 78)
    for name, function in ENGINES:
        r_hostile = measure(name, function, hostile_chunks)
        r_ready = measure(name, function, ready_chunks)
        gain = r_ready - r_hostile
        print(f"{name:10s} | {r_hostile:>13.0%}    | {r_ready:>13.0%}    | {gain:+.0%}")

    print("\nWHAT TO REMEMBER")
    print("- The hostile sheet, one block with no structure, answers targeted questions badly.")
    print("- The AI-ready sheet, cut into clean sections, brings the right passage back.")
    print("- The gain is the same whatever the engine: it comes from the DOCUMENT, not the tech.")


if __name__ == "__main__":
    main()
