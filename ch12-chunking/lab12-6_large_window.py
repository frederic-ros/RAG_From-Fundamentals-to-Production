# -*- coding: utf-8 -*-
"""
Lab 12-6 — The large context window does not save a bad chunking (a myth dismantled)

Learning objective
------------------
"Why bother cutting, when everything can be handed to the model at once?" The
chapter dismantles that myth: beyond a certain volume, more context makes the
model LESS reliable (context degradation), and information placed in the MIDDLE
of a long context is missed far more often — the "lost in the middle" effect,
Liu et al. 2023.

  Giving a model more context does not make it more intelligent.
  Beyond a certain volume, it makes it less reliable.

Two situations are simulated:
  Case 1: good chunking, a short tight context -> the useful fact sits at the
          head and is found.
  Case 2: no chunking, a huge context -> the useful fact is drowned in the
          middle and missed, despite an enormous window.

The model is simulated by a reliability function sensitive to POSITION (the
"lost in the middle" effect), deterministically and with no API.

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"


def reliability_by_position(relative_position: float) -> float:
    """U-shaped curve of the "lost in the middle" effect (Liu et al. 2023).

    relative_position in [0, 1]: 0 = start, 0.5 = middle, 1 = end.
    Reliability is high at the ends, low in the middle.
    """
    # A U: high at the edges, minimal at 0.5 (one minus a bell centred on 0.5).
    import math
    dip = math.exp(-((relative_position - 0.5) ** 2) / (2 * 0.18 ** 2))
    return 1.0 - 0.6 * dip  # between about 0.4 (middle) and 1.0 (edges)


def degradation_by_length(n_tokens: int) -> float:
    """The longer the context, the lower the overall reliability."""
    # 1.0 up to about 150 tokens, then a gentle decline.
    if n_tokens <= 150:
        return 1.0
    return max(0.55, 1.0 - (n_tokens - 150) / 1200)


def build_long_context(texts: List[str], useful_fact: str) -> Tuple[str, float]:
    """Place the useful fact IN THE MIDDLE of a large context: the worst case."""
    middle = len(texts) // 2
    block = texts[:middle] + [useful_fact] + texts[middle:]
    context = "\n\n".join(block)
    # Relative position of the useful fact.
    before = tk.count("\n\n".join(block[:middle]))
    total = tk.count(context)
    pos = before / total if total else 0.5
    return context, pos


def build_tight_context(useful_fact: str, distractors: List[str]) -> Tuple[str, float]:
    """Good chunking: the useful fact is placed at the HEAD of a short,
    relevant context."""
    block = [useful_fact] + distractors[:1]   # short, targeted context
    context = "\n\n".join(block)
    return context, 0.0                       # the fact is at the head


def answer_probability(context: str, position: float) -> float:
    """Simulated reliability = position effect times length effect."""
    n = tk.count(context)
    return reliability_by_position(position) * degradation_by_length(n)


def main() -> None:
    print("=" * 78)
    print("Lab 12-6 — The large context window does not save a bad chunking")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    # The useful information to be found, and the distractor texts.
    useful_fact = ("Remote work is authorised up to a ceiling of two days per week, "
                   "agreed with the line manager.")
    distractors = []
    for name in ("technical_manual.txt", "blog_article.txt", "public_procurement.txt"):
        distractors.append((CORPUS / name).read_text(encoding="utf-8"))
    # Inflate the context by repeating the distractors, to simulate a big corpus.
    big = distractors * 3

    question = "How many days of remote work per week?"
    print(f"\nQuestion: \"{question}\"")
    print("Useful information, present in BOTH cases: \"…two days per week…\"")

    # Case 1: good chunking, tight context (fact at the head, context short).
    ctx1, pos1 = build_tight_context(useful_fact, distractors)
    p1 = answer_probability(ctx1, pos1)

    # Case 2: no chunking, huge context (fact in the middle).
    ctx2, pos2 = build_long_context(big, useful_fact)
    p2 = answer_probability(ctx2, pos2)

    print("\n" + "=" * 78)
    print("TWO STRATEGIES, THE SAME INFORMATION AVAILABLE")
    print("=" * 78)
    print("\nCASE 1 — Good chunking + tight context")
    print(f"  context size       : {tk.count(ctx1)} tokens")
    print(f"  position of the fact: at the head (pos {pos1:.2f})")
    print(f"  estimated reliability: {p1*100:.0f} %")

    print("\nCASE 2 — No chunking + enormous window")
    print(f"  context size       : {tk.count(ctx2)} tokens")
    print(f"  position of the fact: in the middle (pos {pos2:.2f})")
    print(f"  estimated reliability: {p2*100:.0f} %")

    print("\n" + "=" * 78)
    print("WHAT THE MYTH FORGETS")
    print("=" * 78)
    print("The information is present IN BOTH CASES. Yet the large context is")
    print(f"less reliable ({p2*100:.0f} % against {p1*100:.0f} %), for two cumulative reasons:")
    print("- context degradation: the longer it is, the less reliable the model;")
    print("- the \"lost in the middle\" effect: a fact buried at the centre is often missed.")
    print("\nEnlarging the window does not repair a broken cut: a short, right context")
    print("beats a long, approximate one.")

    print("\nWHAT TO REMEMBER")
    print("- The large window does not kill RAG: it recalibrates it.")
    print("- You still have to RETRIEVE and ORDER the right fragments — placement counts.")
    print("- Filling the window is not a strategy, it is a surrender.")


if __name__ == "__main__":
    main()
