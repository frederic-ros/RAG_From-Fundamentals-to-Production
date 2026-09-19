# -*- coding: utf-8 -*-
"""
Lab 12-5 — Is semantic chunking really worth its cost? (a critical look)

Learning objective
------------------
Many people assume that semantic necessarily means better. The chapter unsettles
that idea: a simple, well-tuned chunking often equals a far more expensive
semantic one. This lab puts the two side by side and measures the real GAIN
against the COST.

  The lesson is not that semantic chunking is useless, but that it must prove
  its gain before being adopted. Sophistication is not a virtue in itself.

Recursive chunking (the good default) and semantic chunking (cut where the
meaning changes) are compared on the same corpora: retrieval quality on one
side, time and number of fragments on the other.

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

import re
import time
from pathlib import Path
from typing import Dict, List

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"


def split_recursive(text: str, size: int = 70) -> List[str]:
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


def split_semantic(text: str, size: int = 70, threshold: float = 0.12) -> List[str]:
    """Cut where the similarity between consecutive sentences drops, that is
    where the subject changes."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]
    if len(sentences) <= 1:
        return [text.strip()]
    vec = TfidfVectorizer().fit_transform(sentences)
    chunks, current = [], sentences[0]
    for i in range(1, len(sentences)):
        sim = float(cosine_similarity(vec[i], vec[i - 1])[0][0])
        if sim < threshold or tk.count(current + " " + sentences[i]) > size:
            chunks.append(current.strip())
            current = sentences[i]
        else:
            current += " " + sentences[i]
    if current.strip():
        chunks.append(current.strip())
    return chunks


def search_ok(chunks: List[str], question: str, expected: List[str]) -> bool:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    frag = chunks[int(sims.argmax())].lower()
    return all(e.lower() in frag for e in expected)


QUESTIONS = {
    "remote_work.txt": [
        ("How many days of remote work?", ["two days"]),
        ("What are the general principles of remote work?", ["volunteering"]),
        ("Who provides the equipment?", ["authority"]),
        ("Who is eligible?", ["probationary period"]),
    ],
    "technical_manual.txt": [
        ("Maximum temperature?", ["seventy-five"]),
        ("Supply voltage?", ["400 volts"]),
        ("How often to check the connections?", ["six months"]),
        ("What to do on a shutdown?", ["power supply"]),
    ],
    "blog_article.txt": [
        ("What does the quality depend on?", ["documents"]),
        ("What must be demanded?", ["citations"]),
        ("Do they replace expertise?", ["equip"]),
        ("What makes a deployment successful?", ["business"]),
    ],
}


def measure(function, text: str, questions: List) -> Dict:
    t0 = time.perf_counter()
    chunks = function(text)
    elapsed = (time.perf_counter() - t0) * 1000
    hits = sum(search_ok(chunks, q, exp) for q, exp in questions)
    return {"n_chunks": len(chunks), "hits": hits, "total": len(questions),
            "elapsed_ms": elapsed}


def main() -> None:
    print("=" * 78)
    print("Lab 12-5 — Is semantic chunking really worth its cost?")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    total_rec = {"hits": 0, "total": 0, "elapsed": 0.0}
    total_sem = {"hits": 0, "total": 0, "elapsed": 0.0}

    print("\n" + "=" * 78)
    print("RECURSIVE (the good default) AGAINST SEMANTIC (the expensive one)")
    print("=" * 78)
    print(f"{'corpus':22s} | {'recursive':>20s} | {'semantic':>22s}")
    print(f"{'':22s} | {'found    time':>20s} | {'found    time    cost':>22s}")
    print("-" * 78)

    for name, questions in QUESTIONS.items():
        text = (CORPUS / name).read_text(encoding="utf-8")
        r = measure(split_recursive, text, questions)
        s = measure(split_semantic, text, questions)
        total_rec["hits"] += r["hits"]; total_rec["total"] += r["total"]; total_rec["elapsed"] += r["elapsed_ms"]
        total_sem["hits"] += s["hits"]; total_sem["total"] += s["total"]; total_sem["elapsed"] += s["elapsed_ms"]
        factor = s["elapsed_ms"] / r["elapsed_ms"] if r["elapsed_ms"] else 0
        print(f"{name:22s} | {r['hits']}/{r['total']}   {r['elapsed_ms']:>6.1f}ms | "
              f"{s['hits']}/{s['total']}   {s['elapsed_ms']:>6.1f}ms   x{factor:.0f}")

    print("-" * 78)
    overall = total_sem["elapsed"] / total_rec["elapsed"] if total_rec["elapsed"] else 0
    print(f"{'TOTAL':22s} | {total_rec['hits']}/{total_rec['total']}   "
          f"{total_rec['elapsed']:>6.1f}ms | {total_sem['hits']}/{total_sem['total']}   "
          f"{total_sem['elapsed']:>6.1f}ms   x{overall:.0f}")

    print("\n" + "=" * 78)
    print("THE VERDICT")
    print("=" * 78)
    gain = total_sem["hits"] - total_rec["hits"]
    print(f"Retrieval gain of semantic chunking: {gain:+d} answer(s) out of {total_rec['total']}.")
    print(f"Extra cost in time: about x{overall:.0f}.")
    if gain <= 0:
        print("=> Semantic does no better here, for a far higher cost.")
    else:
        print("=> Semantic gains a little, but is the extra cost justified at your scale?")
    print("   Sophistication has to prove its gain: it is not adopted on principle.")

    print("\nWHAT TO REMEMBER")
    print("- \"Semantic means better\" is a myth: recursive often equals it, for less.")
    print("- Start simple, measure, and add complexity only when the gain is real and needed.")
    print("- Cost — time, complexity, maintenance — is part of the decision, not just quality.")


if __name__ == "__main__":
    main()
