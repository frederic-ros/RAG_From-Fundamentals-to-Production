# -*- coding: utf-8 -*-
"""
Lab 14-2 — Recovering the lost context (Claire)

Learning objective
------------------
The previous lab set up the shock: an exact fragment, "three days", stripped of
the context that made it an exception. Here we repair it — without yet talking
about architecture. We simply show that, inside a tree, a fragment can RECOVER
ITS ADDRESS.

  A fragment must be able to recover its address.

When the system retrieves the "three days" leaf, it CLIMBS its hierarchy, node
by node:

    three days
      ^
    Exceptional provisions      (so it is an exception!)
      ^
    Remote work                 (which also contains the general rule)
      ^
    HR agreement                (the document)

The moment "Exceptional provisions" is reached, the ambiguity lifts: "three
days" appears for what it is — an exception, not the rule.

No API key. Uses tree.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple

import tree as T

CORPUS = Path(__file__).resolve().parent / "corpus"
DOC = CORPUS / "remote_work_agreement.json"


def score(leaves: List[T.Leaf], question: str) -> List[Tuple[T.Leaf, float]]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    texts = [leaf.text for leaf in leaves]
    vec = TfidfVectorizer()
    mat = vec.fit_transform(texts + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    pairs = list(zip(leaves, (float(s) for s in sims)))
    return sorted(pairs, key=lambda p: p[1], reverse=True)


def main() -> None:
    print("=" * 78)
    print("Lab 14-2 — Recovering the lost context (Claire)")
    print("=" * 78)

    if not DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    tree = T.load(DOC)

    # The same query that brought back the exception.
    question = "How many days are granted to employees who are carers?"
    leaf, best = score(tree.leaves, question)[0]

    print(f"\n  question: \"{question}\"")
    print(f"  fragment retrieved (score {best:.2f}): \"{leaf.text}\"")

    print("\n" + "=" * 78)
    print("THE CLIMB THROUGH THE HIERARCHY")
    print("=" * 78)
    print("  Start from the leaf and climb its path, level by level:\n")

    # Unroll the breadcrumb from the bottom upwards.
    levels = leaf.path[:]        # e.g. [HR agreement, Remote work, Exceptional provisions]
    order = list(reversed(levels))
    for indent, title in enumerate(order):
        print(f"  {'  ' * indent}{title}")
        if indent < len(order) - 1:
            print(f"  {'  ' * indent}^")

    print("\n" + "=" * 78)
    print("WHAT THE CLIMB REVEALS")
    print("=" * 78)
    # At which level does the ambiguity lift?
    revealing_level = None
    for title in levels:
        if "exception" in title.lower():
            revealing_level = title
            break
    if revealing_level:
        print(f"  On reaching \"{revealing_level}\", everything changes: we understand that")
        print("  \"three days\" is not the rule but an exception. The same text suddenly")
        print("  says something else — because we finally know where it comes from.")

    # The context parent (the section) holds the rule AND the exception.
    context = tree.context_of(leaf)
    print(f"\n  Climbing as far as the section \"{context.title}\" even recovers")
    print("  the complete neighbourhood — general rule AND exception together:")
    print(f"    \"{context.text}\"")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- A fragment placed in a tree is never truly lost: it can climb its path")
    print("  until it finds the context that makes sense of it.")
    print("- That is exactly what a human reader does: they locate a sentence, then")
    print("  their eye climbs to the paragraph, the section, the chapter.")

    print("\nWHAT TO REMEMBER")
    print("- A fragment must be able to recover its address.")
    print("- The hierarchy preserved at chunking time (Chapter 13) makes that climb possible.")
    print("- In the next lab it becomes an architecture: search small, answer large.")


if __name__ == "__main__":
    main()
