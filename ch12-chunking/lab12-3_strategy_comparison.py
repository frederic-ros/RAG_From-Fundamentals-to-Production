# -*- coding: utf-8 -*-
"""
Lab 12-3 — Comparing the chunking strategies: the test bench

Learning objective
------------------
No strategy is universal. The four families of the chapter are applied to
several corpora and their effect on retrieval, their cost and their robustness
are measured. The aim is to dispel the idea that semantic chunking is always
better, and to show that recursive chunking, properly tuned, is often enough.

The four strategies:
  1. fixed size — cut every N tokens.
  2. fixed size with overlap — overlapping windows, to soften the boundary cuts.
  3. recursive — respect paragraphs, then sentences (the good default).
  4. semantic (approximate) — group sentences by closeness of meaning (TF-IDF).

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

import re
import time
from pathlib import Path
from typing import Callable, Dict, List

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"


# ---------------------------------------------------------------------------
# The four strategies
# ---------------------------------------------------------------------------
def s_fixed(text: str, size: int = 60) -> List[str]:
    tokens = tk.encode(text)
    return [tk.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]


def s_overlap(text: str, size: int = 60, overlap: float = 0.2) -> List[str]:
    tokens = tk.encode(text)
    step = max(1, int(size * (1 - overlap)))
    chunks = []
    for i in range(0, len(tokens), step):
        piece = tokens[i:i + size]
        if piece:
            chunks.append(tk.decode(piece))
        if i + size >= len(tokens):
            break
    return chunks


def s_recursive(text: str, size: int = 60) -> List[str]:
    """Respect a hierarchy of separators: paragraphs, then sentences."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for p in paragraphs:
        if tk.count(p) <= size:
            chunks.append(p)
            continue
        sentences = re.split(r"(?<=[.!?])\s+", p)
        current = ""
        for s in sentences:
            if current and tk.count(current + " " + s) > size:
                chunks.append(current.strip())
                current = s
            else:
                current = (current + " " + s).strip()
        if current:
            chunks.append(current)
    return chunks


def s_semantic(text: str, size: int = 60) -> List[str]:
    """Approximate semantic chunking: cut where the subject CHANGES, that is
    where similarity between consecutive sentences drops, bounded by the size.
    More expensive, because it vectorises."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]
    if len(sentences) <= 1:
        return [text.strip()]
    vec = TfidfVectorizer().fit_transform(sentences)
    chunks, current = [], sentences[0]
    for i in range(1, len(sentences)):
        sim = float(cosine_similarity(vec[i], vec[i - 1])[0][0])
        too_long = tk.count(current + " " + sentences[i]) > size
        # A break in meaning (low similarity) or an overrun of the size -> cut.
        if sim < 0.12 or too_long:
            chunks.append(current.strip())
            current = sentences[i]
        else:
            current += " " + sentences[i]
    if current.strip():
        chunks.append(current.strip())
    return chunks


# ---------------------------------------------------------------------------
# Evaluation: mid-sentence cuts, duplication and cost
# ---------------------------------------------------------------------------
def duplication_rate(chunks: List[str], text: str) -> float:
    total = sum(tk.count(c) for c in chunks)
    base = tk.count(text)
    return (total - base) / base if base else 0.0


def mid_sentence_cuts(chunks: List[str]) -> int:
    """Count the fragments that begin or end in the middle of a sentence."""
    n = 0
    for c in chunks:
        c = c.strip()
        if not c:
            continue
        # Ends mid-sentence: does not finish on strong punctuation.
        if c[-1] not in ".!?:":
            n += 1
        # Begins mid-sentence: starts on a lowercase letter.
        if c[0].islower():
            n += 1
    return n


def search_ok(chunks: List[str], question: str, expected: List[str]) -> bool:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    frag = chunks[int(sims.argmax())].lower()
    return all(e.lower() in frag for e in expected)


# Question sets per corpus. An answer is judged on the presence of key elements.
QUESTIONS = {
    "remote_work.txt": [
        ("How many days of remote work?", ["two days"]),
        ("What are the general principles of remote work?", ["volunteering"]),
        ("Who provides the computer equipment?", ["authority"]),
        ("Who is eligible for remote work?", ["probationary period"]),
    ],
    "public_procurement.txt": [
        ("What is the standard delivery time for the supplies?", ["thirty days"]),
        ("Payment period for a health establishment?", ["sixty days"]),
        ("Is subcontracting possible?", ["subcontract"]),
        ("When may the contract be terminated?", ["default"]),
    ],
    "technical_manual.txt": [
        ("Maximum operating temperature?", ["seventy-five"]),
        ("Supply voltage?", ["400 volts"]),
        ("How often should the connections be checked?", ["six months"]),
        ("What to do on an unexpected shutdown?", ["power supply"]),
    ],
    "blog_article.txt": [
        ("What does the quality of a retrieval system depend on?", ["documents"]),
        ("What must be demanded for trust?", ["citations"]),
        ("Do these systems replace expertise?", ["equip"]),
        ("What sets a successful deployment apart?", ["business"]),
    ],
}

STRATEGIES: Dict[str, Callable[[str], List[str]]] = {
    "fixed": s_fixed,
    "overlap": s_overlap,
    "recursive": s_recursive,
    "semantic": s_semantic,
}


def benchmark_corpus(name: str, text: str) -> Dict:
    results = {}
    for strategy_name, function in STRATEGIES.items():
        t0 = time.perf_counter()
        chunks = function(text)
        elapsed = (time.perf_counter() - t0) * 1000
        questions = QUESTIONS[name]
        hits = sum(search_ok(chunks, q, exp) for q, exp in questions)
        results[strategy_name] = {
            "n_chunks": len(chunks),
            "hits": hits,
            "total": len(questions),
            "cuts": mid_sentence_cuts(chunks),
            "duplication": duplication_rate(chunks, text),
            "elapsed_ms": elapsed,
        }
    return results


def main() -> None:
    print("=" * 78)
    print("Lab 12-3 — Comparing the chunking strategies: the test bench")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    for name in ("remote_work.txt", "public_procurement.txt",
                 "technical_manual.txt", "blog_article.txt"):
        text = (CORPUS / name).read_text(encoding="utf-8")
        res = benchmark_corpus(name, text)
        print("\n" + "=" * 78)
        print(f"CORPUS: {name}")
        print("=" * 78)
        print(f"{'strategy':14s} | {'found':>7s} | {'chunks':>6s} | "
              f"{'cuts':>8s} | {'duplic.':>7s} | {'time':>8s}")
        print("-" * 78)
        for strategy, r in res.items():
            print(f"{strategy:14s} | {r['hits']}/{r['total']:<5d} | {r['n_chunks']:>6d} | "
                  f"{r['cuts']:>8d} | {r['duplication']*100:>6.0f}% | {r['elapsed_ms']:>6.1f}ms")

    print("\n" + "=" * 78)
    print("READING THE TEST BENCH")
    print("=" * 78)
    print("- Recursive respects the structure: few cuts, good retrieval, low cost.")
    print("- Overlap softens the boundary cuts of fixed size, at the price of about a fifth")
    print("  more tokens indexed — worth paying only when those cuts actually hurt.")
    print("- Semantic is the most expensive, because it vectorises; its gain is not systematic.")
    print("- On continuous prose (the blog), every strategy performs alike: do not over-engineer.")

    print("\nWHAT TO REMEMBER")
    print("- No strategy is universal: the right one depends on the corpus and on the questions.")
    print("- Recursive is the best starting point; add complexity only when measurement justifies it.")
    print("- Measure before choosing: a test bench beats an intuition.")


if __name__ == "__main__":
    main()
