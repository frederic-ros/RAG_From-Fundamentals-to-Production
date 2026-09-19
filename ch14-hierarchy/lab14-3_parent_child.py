# -*- coding: utf-8 -*-
"""
Lab 14-3 — Parent-child: search small, answer large (Claire)

Learning objective
------------------
The first real architecture lab. We build a two-level index, exactly as the
modern frameworks do under the name Parent Document Retrieval:

  - a vector index holding the CHILDREN (small, precise): that is what the
    search runs against;
  - a key-value store keeping the PARENTS (the sections, rich in context): that
    is what gets restored in order to answer.

  We search in the detail. We answer with the context.

Two systems are compared on the same question:

  Classic search : index and restore the SAME small fragment.
                   -> partial answer (the exception, alone).
  Parent-child   : index the child, but restore its PARENT.
                   -> contextualised answer (rule AND exception).

No API key. Uses tree.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple

import tree as T

CORPUS = Path(__file__).resolve().parent / "corpus"
DOC = CORPUS / "remote_work_agreement.json"


class ChildrenIndex:
    """A vector index built ONLY on the child fragments."""

    def __init__(self, leaves: List[T.Leaf]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.leaves = leaves
        self._vec = TfidfVectorizer()
        self._mat = self._vec.fit_transform([leaf.text for leaf in leaves])

    def search(self, question: str) -> Tuple[T.Leaf, float]:
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([question])
        sims = cosine_similarity(q, self._mat)[0]
        idx = int(sims.argmax())
        return self.leaves[idx], float(sims[idx])


def show_answer(title: str, text: str):
    print(f"  {title}")
    print(f"    \"{text}\"")


def main() -> None:
    print("=" * 78)
    print("Lab 14-3 — Parent-child: search small, answer large (Claire)")
    print("=" * 78)

    if not DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    tree = T.load(DOC)
    index = ChildrenIndex(tree.leaves)

    question = "How many days are granted to employees who are carers?"
    print(f"\n  question put to both systems: \"{question}\"")

    # Common step: the search finds the right CHILD, a precise entry point.
    child, best = index.search(question)
    print(f"\n  entry point found (score {best:.2f}) — {child.breadcrumb}:")
    print(f"    \"{child.text}\"")

    print("\n" + "=" * 78)
    print("SYSTEM 1 — CLASSIC SEARCH (restore the child that was found)")
    print("=" * 78)
    show_answer("context given to the model:", child.text)
    print("\n  The model sees only the exception. Nothing tells it that a different")
    print("  general rule exists. A partial answer, and a risk of misreading.")

    print("\n" + "=" * 78)
    print("SYSTEM 2 — PARENT-CHILD (climb to the parent, restore the large one)")
    print("=" * 78)
    parent = tree.context_of(child)
    show_answer(f"context given to the model — section \"{parent.title}\":", parent.text)
    print("\n  The model sees the general rule AND the exception. It can answer")
    print("  \"two days in general, three for carers\". A contextualised answer.")

    print("\n" + "=" * 78)
    print("COMPARISON")
    print("=" * 78)
    print(f"  Classic search : in = child, out = child   "
          f"({len(parent.text.split())} words of context lost).")
    print("  Parent-child   : in = child, out = parent  "
          "(complete context restored).")
    print("\n  The same entry point. Two answers. Only the RESTITUTION changed.")

    print("\nWHAT TO REMEMBER")
    print("- Vectorise the small children, for search precision...")
    print("- ... but restore the large parents, for the richness of the answer.")
    print("- The child locates; the parent contextualises. You win on both counts.")


if __name__ == "__main__":
    main()
