# -*- coding: utf-8 -*-
"""
Lab 20-7 (BONUS) -- Compressing the context: how much can you cut before the
answer breaks?

Learning objective
-------------------
Chapter 20 sorts and re-ranks fragments, but never questions their SIZE. In
production, the re-ranked top-k is still often too large: more tokens than
needed, more cost, more chance the model buries the one sentence that
matters in the middle of the rest ("lost in the middle", Chapter 22). This
lab builds a small, deterministic EXTRACTIVE compressor: score every
sentence of the retrieved context against the query, keep only the
best-scoring ones under a token budget, and measure -- not assume -- how far
you can compress before the fact the question needs is gone.

This mirrors the *extractive* half of RECOMP (Xu, Shi & Choi, 2024): select
sentences rather than generate a summary, so the result stays a direct
quote, auditable like this book's whole retrieval pipeline. Production
systems often go further with a trained compressor (RECOMP's abstractive
half) or token-level perplexity filtering (LLMLingua, Jiang et al., 2023);
the mechanism you tune by hand here is the same one they automate.

No API key. No network. Fully deterministic.
"""

import math
import re
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# 1. A realistic post-retrieval scenario: the re-ranked top-k already exists
# ---------------------------------------------------------------------------
# Four fragments, as if Chapter 20's pipeline had already retrieved and
# re-ranked them for this query. Each mixes sentences that answer the
# question with sentences that do not -- exactly what real retrieval hands
# to generation: relevant, but not every word of it.
QUERY = "What is the prescribed reassembly torque for motor M-18?"

FRAGMENTS: List[Dict] = [
    {"id": "frag_01", "source": "maintenance-M18-2024.md", "text": (
        "Motor M-18 has been in service since 2019 and is inspected quarterly. "
        "The maintenance procedure requires cutting power before any intervention. "
        "The prescribed reassembly torque for M-18 is 45 Newton-meters, applied in three even passes. "
        "Operators should log every intervention in the site register."
    )},
    {"id": "frag_02", "source": "safety-brief-line4.md", "text": (
        "Line 4 hosts motors M-16 through M-20 along the north wall. "
        "Safety glasses and gloves are mandatory in this zone at all times. "
        "A fire extinguisher is located at the east exit, near the control panel."
    )},
    {"id": "frag_03", "source": "torque-spec-table.md", "text": (
        "Torque specifications vary by motor model and bolt size. "
        "For M-18's housing bolts (M10), the reassembly torque is 45 N.m, never exceeding 50 N.m. "
        "For M-16, the equivalent value is 38 N.m. "
        "Over-torquing is a leading cause of housing micro-fractures reported in 2023."
    )},
    {"id": "frag_04", "source": "changelog-2025.md", "text": (
        "The maintenance changelog for 2025 lists twelve revisions across all line-4 motors. "
        "Most changes concern inspection frequency, not torque values. "
        "No torque specification was revised for M-18 during this period."
    )},
]

STOPWORDS = {"the", "a", "an", "is", "are", "of", "in", "on", "to", "for", "and",
             "at", "as", "this", "that", "with", "by", "be", "was", "were", "what"}


# ---------------------------------------------------------------------------
# 2. The compressor: score sentences, keep the best under a token budget
# ---------------------------------------------------------------------------
def split_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def tokenize(text: str) -> List[str]:
    # Alphanumeric tokens, so a specific figure ("45") or a model number
    # ("18" in "M-18") can match the query exactly like a word would --
    # dropping digits would silently blind the scorer to the very facts a
    # maintenance corpus is full of.
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def word_count(text: str) -> int:
    """A word count stands in for a token count here -- close enough for a
    pedagogical order of magnitude, and it keeps the lab dependency-free."""
    return len(tokenize(text))


def document_frequencies(fragments: List[Dict]) -> Dict[str, int]:
    """How many sentences (across the whole retrieved context) each term
    appears in. Feeds the IDF weighting below: a term present everywhere
    ("motor", "line") is nearly meaningless as a signal, while a term
    present in a single sentence ("45", "reassembly") is exactly what
    distinguishes the one sentence that answers the question."""
    doc_freq: Dict[str, int] = {}
    for frag in fragments:
        for sentence in split_sentences(frag["text"]):
            for term in set(tokenize(sentence)):
                doc_freq[term] = doc_freq.get(term, 0) + 1
    return doc_freq


def score_sentence(sentence: str, query_terms: set, doc_freq: Dict[str, int], n_sentences: int) -> float:
    """Extractive scoring, TF-IDF in spirit: sum, over the query terms this
    sentence contains, of an inverse-document-frequency weight. A shared
    generic word barely moves the score; a shared rare, specific word moves
    it a lot -- exactly the principle Chapter 1 built for whole-document
    search, applied here one sentence at a time."""
    terms = set(tokenize(sentence))
    matched = terms & query_terms
    if not matched:
        return 0.0
    score = 0.0
    for term in matched:
        df = doc_freq.get(term, 1)
        score += math.log((n_sentences + 1) / df)
    return score


def compress(fragments: List[Dict], query: str, budget_words: int) -> Tuple[str, List[Tuple[str, float]]]:
    """Score every sentence from every fragment against the query, then keep
    the best-scoring ones, highest first, until the word budget is spent."""
    query_terms = set(tokenize(query)) - STOPWORDS
    all_sentences = [s for frag in fragments for s in split_sentences(frag["text"])]
    doc_freq = document_frequencies(fragments)

    scored: List[Tuple[str, float]] = [
        (s, score_sentence(s, query_terms, doc_freq, len(all_sentences)))
        for s in all_sentences
    ]
    scored.sort(key=lambda x: -x[1])

    kept: List[str] = []
    spent = 0
    for sentence, score in scored:
        cost = word_count(sentence)
        if spent + cost > budget_words:
            continue
        kept.append(sentence)
        spent += cost
    return " ".join(kept), scored


def contains_answer(text: str) -> bool:
    """Fidelity check: does the compressed context still state the specific
    fact the question needs? Deterministic substring check, same spirit as
    the fidelity checks used throughout the book's evaluation labs."""
    return "45" in text and ("n.m" in text.lower() or "newton" in text.lower())


def main() -> None:
    print("=" * 78)
    print("Lab 20-7 (BONUS) -- Compressing the context: how much can you cut")
    print("before the answer breaks?")
    print("=" * 78)

    raw_context = " ".join(f["text"] for f in FRAGMENTS)
    raw_words = word_count(raw_context)
    print(f'\nQuery: "{QUERY}"')
    print(f"\nRaw re-ranked context: {len(FRAGMENTS)} fragments, {raw_words} words.")
    print("Answer needed: the M-18 reassembly torque (45 N.m) -- stated once,")
    print("inside frag_01 and again inside frag_03, buried among sentences")
    print("about safety gear, changelogs, and other motors.")

    print("\n" + "=" * 78)
    print("1) SWEEP THE BUDGET: from generous to aggressive")
    print("=" * 78)
    budgets = [raw_words, 40, 25, 15, 8]
    print(f"  {'budget (words)':>15s} | {'kept (words)':>13s} | {'compression':>11s} | answer present?")
    print("  " + "-" * 66)

    results = []
    for budget in budgets:
        compressed, _ = compress(FRAGMENTS, QUERY, budget)
        kept_words = word_count(compressed)
        ratio = 1 - kept_words / raw_words
        ok = contains_answer(compressed)
        results.append((budget, kept_words, ratio, ok, compressed))
        flag = "yes" if ok else "NO -- LOST"
        print(f"  {budget:15d} | {kept_words:13d} | {ratio:10.0%} | {flag}")

    print("\n" + "=" * 78)
    print("2) READ THE COMPRESSED CONTEXT AT THE TIGHTEST SAFE BUDGET")
    print("=" * 78)
    safe = [r for r in results if r[3]]
    tightest = min(safe, key=lambda r: r[1]) if safe else None
    if tightest:
        budget, kept_words, ratio, ok, compressed = tightest
        print(f"  Budget {budget} words -> kept {kept_words} words ({ratio:.0%} cut), answer intact:")
        print(f'  "{compressed}"')
    else:
        print("  No budget in this sweep preserved the answer.")

    print("\n" + "=" * 78)
    print("3) WHAT BREAKS AT THE NEXT STEP DOWN")
    print("=" * 78)
    broken = [r for r in results if not r[3]]
    if broken:
        budget, kept_words, ratio, ok, compressed = broken[0]
        print(f"  At budget {budget} words ({ratio:.0%} cut), the torque value drops out:")
        print(f'  "{compressed}"')
        print("  What survives is still on-topic (M-18, maintenance) -- but the one")
        print("  specific number ('45 N.m') the question actually needs no longer fits")
        print("  the budget: a plausible, confident-sounding, WRONG-by-omission context.")

    print("\n" + "=" * 78)
    print("WHAT THIS REVEALS")
    print("=" * 78)
    print("- Compression is not a free lunch with a single safe setting: there is a")
    print("  budget below which the specific fact needed to answer silently drops out,")
    print("  while the context still LOOKS reasonable (on-topic sentences remain).")
    print("- The failure is quiet. Nothing crashes; the model is simply handed a")
    print("  context that is on-topic but no longer sufficient -- and may answer")
    print("  fluently, and wrong.")
    print("- Measuring where that line sits (as this lab does, sweeping the budget)")
    print("  is the only way to set it with intent, rather than by accident of an")
    print("  arbitrary token limit.")

    print("\nKEY TAKEAWAYS")
    print("- Extractive compression scores sentences against the query and keeps only")
    print("  the best ones under a token budget -- the same idea as RECOMP's")
    print("  extractive compressor, tuned by hand here instead of trained.")
    print("- A compression ratio alone says nothing about safety: always pair it with")
    print("  a fidelity check on the specific fact the question needs.")
    print("- References: Xu, Shi & Choi (2024), RECOMP: Improving Retrieval-Augmented")
    print("  LMs with Compression and Selective Augmentation, ICLR. Jiang et al.")
    print("  (2023), LLMLingua: Compressing Prompts for Accelerated Inference of")
    print("  Large Language Models, EMNLP (token-level, model-based compression).")


if __name__ == "__main__":
    main()
