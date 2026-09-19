# -*- coding: utf-8 -*-
"""
Lab 12-2 — The clause cut in two: when RAG becomes legally false (Sophie)

Learning objective
------------------
There is a case where chunking stops being a compromise and becomes an absolute
rule: regulatory corpora. The unit of meaning — the article, the clause — is not
negotiable. Cutting it amounts to producing false information.

  In a regulatory corpus, you never cut a clause in two.
  An obligation severed from its exception becomes a misreading, and a legally
  dangerous one.

Each article of the corpus states an OBLIGATION and then, in its second half, a
decisive EXCEPTION ("however...", "by way of exception..."). We compare:

  Fixed-size chunking: cuts between the obligation and the exception -> false answer.
  Chunking by article: matches the legal unit -> correct and complete answer.

No API key. Uses tokenizer.py and the local regulatory corpus.
Run generate_corpus.py first.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"
DOC = CORPUS / "public_procurement.txt"


# ---------------------------------------------------------------------------
# Two chunkings
# ---------------------------------------------------------------------------
def chunk_fixed_size(text: str, size: int) -> List[str]:
    tokens = tk.encode(text)
    return [tk.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]


def chunk_by_article(text: str) -> List[str]:
    """Chunking that matches the legal unit: one article, one fragment."""
    # Cut before each "Article N —".
    pieces = re.split(r"(?=Article\s+\d+\s*—)", text)
    return [p.strip() for p in pieces if p.strip() and p.strip().startswith("Article")]


# ---------------------------------------------------------------------------
# Trap questions: the answer requires the obligation AND its exception
# ---------------------------------------------------------------------------
QUESTIONS = [
    {
        "question": "What is the delivery time in the event of force majeure?",
        "obligation": "thirty days",
        "exception": "fifteen days",      # +15 days under force majeure
        "article": "Article 5",
    },
    {
        "question": "Is a late-delivery penalty due if the delay comes from the purchaser?",
        "obligation": "penalty",
        "exception": "no penalty",        # exception: none if the purchaser caused it
        "article": "Article 6",
    },
    {
        "question": "What is the payment period for a public health establishment?",
        "obligation": "thirty days",
        "exception": "sixty days",        # health-sector exception
        "article": "Article 7",
    },
]


def search_for(chunks: List[str], question: str) -> Tuple[str, float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return chunks[idx], float(sims[idx])


def full_answer(fragment: str, q: Dict) -> bool:
    """The answer is correct only if the fragment holds the obligation AND its
    exception: otherwise the system states the rule without its decisive
    qualification."""
    f = fragment.lower()
    return q["obligation"].lower() in f and q["exception"].lower() in f


def main() -> None:
    print("=" * 78)
    print("Lab 12-2 — The clause cut in two: when RAG becomes legally false")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    text = DOC.read_text(encoding="utf-8")

    fixed = chunk_fixed_size(text, 45)
    by_article = chunk_by_article(text)

    print(f"\nFixed-size chunking (45 tokens): {len(fixed)} fragments.")
    print(f"Chunking by article: {len(by_article)} fragments, one per article.")

    print("\n" + "=" * 78)
    print("THE SAME QUESTIONS, TWO CHUNKINGS")
    print("=" * 78)

    fixed_errors = 0
    for q in QUESTIONS:
        frag_fixed, _ = search_for(fixed, q["question"])
        frag_art, _ = search_for(by_article, q["question"])
        ok_fixed = full_answer(frag_fixed, q)
        ok_art = full_answer(frag_art, q)
        if not ok_fixed:
            fixed_errors += 1

        print(f"\nQ ({q['article']}): {q['question']}")
        print(f"  fixed size  -> {'complete' if ok_fixed else 'INCOMPLETE (obligation without its exception)'}")
        if not ok_fixed:
            print(f"     risk: the system states \"{q['obligation']}\" without \"{q['exception']}\"")
        print(f"  by article  -> {'complete' if ok_art else 'incomplete'}")

    print("\n" + "=" * 78)
    print("RISK ANALYSIS")
    print("=" * 78)
    print(f"Incomplete answers under fixed-size chunking: {fixed_errors}/{len(QUESTIONS)}")
    print("Each one is legally dangerous: an obligation quoted without its exception")
    print("leads to a mistake — a period miscalculated, a penalty claimed wrongly.")
    print("Chunking by article restores the integrity of the unit of law.")

    print("\nWHAT TO REMEMBER")
    print("- In a regulatory corpus the fragment matches the article: never less, never straddling two.")
    print("- An obligation severed from its exception is a misreading, not half an answer.")
    print("- Here the chunking rule submits to the structure of the document, not the other way round.")


if __name__ == "__main__":
    main()
