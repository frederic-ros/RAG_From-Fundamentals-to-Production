# -*- coding: utf-8 -*-
"""
Lab 12-1 — the information is there, but unfindable (Claire)

Learning objective
------------------
The flagship lab of the chapter: showing that chunking decides what the system
is able to find. Information that is perfectly present in the corpus can become
UNFINDABLE because of a badly placed cut.

  Chunking is not a preprocessing setting.
  It is a decision that determines what the system will be able to find.

The same question — "how many days of remote work per week?" — is put under
three conditions:

  Version A: the whole document, as a single unit -> correct answer.
  Version B: catastrophic chunking, a blind cut   -> answer unfindable.
  Version C: improved chunking, paragraph-aware   -> correct answer.

The reader sees it at once: chunking changes the operational truth of the
system.

No API key. Uses the tokenizer.py module and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"
DOC = CORPUS / "remote_work.txt"


# ---------------------------------------------------------------------------
# Three chunkings
# ---------------------------------------------------------------------------
def whole_document(text: str) -> List[str]:
    """The whole document: a single unit of search."""
    return [text]


def chunk_fixed_size(text: str, size: int) -> List[str]:
    """Cut every `size` tokens, with no regard for meaning."""
    tokens = tk.encode(text)
    return [tk.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]


def chunk_by_paragraph(text: str, max_size: int) -> List[str]:
    """Simple paragraph-aware chunking (a minimal recursive splitter)."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    for p in paragraphs:
        if tk.count(p) <= max_size:
            chunks.append(p)
        else:
            # A paragraph that is too long is cut at sentence boundaries.
            sentences = p.replace(". ", ".\n").split("\n")
            current = ""
            for s in sentences:
                if tk.count(current + " " + s) > max_size and current:
                    chunks.append(current.strip())
                    current = s
                else:
                    current += " " + s
            if current.strip():
                chunks.append(current.strip())
    return chunks


# ---------------------------------------------------------------------------
# Search (TF-IDF) and evaluation of the answer
# ---------------------------------------------------------------------------
def search_for(chunks: List[str], question: str) -> Tuple[str, float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return chunks[idx], float(sims[idx])


def answers_correctly(fragment: str) -> bool:
    """The answer is complete only if the fragment holds BOTH the number of days
    AND the words "remote work": that is what proves "two days" refers to remote
    work and not to something else. A cut that separates the two leaves an
    ambiguous answer, and therefore a false one as far as the system goes."""
    f = fragment.lower()
    return "two days" in f and "remote work" in f


def evaluate(name: str, chunks: List[str], question: str) -> Dict:
    fragment, score = search_for(chunks, question)
    correct = answers_correctly(fragment)
    return {"name": name, "n_chunks": len(chunks), "fragment": fragment,
            "score": score, "correct": correct}


def main() -> None:
    print("=" * 78)
    print("Lab 12-1 — The information is there, but unfindable (Claire)")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    text = DOC.read_text(encoding="utf-8")
    question = "How many days of remote work per week?"
    print(f"Question put to all three versions: \"{question}\"")
    print("Expected answer: two days per week, with its context.")

    a = evaluate("A — whole document", whole_document(text), question)
    b = evaluate("B — blind cut (40 tokens)", chunk_fixed_size(text, 40), question)
    c = evaluate("C — by paragraph (120 tokens)", chunk_by_paragraph(text, 120), question)

    print("\n" + "=" * 78)
    print("RESULTS: THE SAME QUESTION, THREE CHUNKINGS")
    print("=" * 78)
    for r in (a, b, c):
        verdict = "CORRECT" if r["correct"] else "UNFINDABLE"
        print(f"\nVersion {r['name']}  ({r['n_chunks']} fragment(s))")
        print(f"  fragment retrieved: \"{r['fragment'][:80].strip()}…\"")
        print(f"  answer: {verdict}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Version A (whole document): the answer is there, and it is found.")
    print("- Version B (blind cut): the information still exists in the corpus,")
    print("  but the fragment that says \"two days\" has lost the words \"remote work\",")
    print("  or the other way round. The search can no longer connect question to answer.")
    print("- Version C (by paragraph): the fragment matches the idea, and the answer returns.")
    print("\n  => The same corpus, three chunkings, three different operational truths.")

    print("\nWHAT TO REMEMBER")
    print("- \"It is all there, but nothing comes back\" is the signature of a bad cut.")
    print("- Chunking is not a technical detail: it is a design decision.")
    print("- Before tuning the model, check that your fragments CAN answer.")


if __name__ == "__main__":
    main()
