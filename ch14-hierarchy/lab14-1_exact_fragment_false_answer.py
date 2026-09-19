# -*- coding: utf-8 -*-
"""
Lab 14-1 — The exact fragment that answers falsely (Claire)

Learning objective
------------------
The emblematic lab of the chapter. No architecture, no technique: a SHOCK. An
ordinary question is asked, the system finds a perfectly exact fragment, and it
answers... falsely.

  The quality of the retrieval does not guarantee the quality of the answer.

The document says two things, in two distinct subsections:

  General rule            -> two days of remote work.
  Exceptional provisions  -> three days for employees who are carers.

To the question "how many days may I take?", the search lands on the "three
days" fragment — exact, quite real, but it was the EXCEPTION. Presented alone,
without the mention of carers that qualified it, it answers "three days" to
everyone. Exact, and false.

No API key. Uses tree.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple

import tree as T

CORPUS = Path(__file__).resolve().parent / "corpus"
DOC = CORPUS / "remote_work_agreement.json"


def score(leaves: List[T.Leaf], question: str) -> List[Tuple[T.Leaf, float]]:
    """Score each leaf by TF-IDF similarity with the question.

    Every score is printed: the reader watches the search separate the
    fragments, and understands why the system keeps the one it keeps.
    """
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
    print("Lab 14-1 — The exact fragment that answers falsely (Claire)")
    print("=" * 78)

    if not DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    tree = T.load(DOC)

    print("\nWHAT THE DOCUMENT ACTUALLY SAYS")
    print("-" * 78)
    for leaf in tree.leaves:
        print(f"  [{leaf.path[-1]}]  \"{leaf.text}\"")

    # The question of an employee who is a CARER: it uses the word "carers",
    # which appears ONLY in the exception. The search, focused on the small
    # fragments, therefore returns the exception — exact for that employee. The
    # trap: the system is about to serve it as it stands, even to someone who
    # is not a carer.
    question = "How many days are granted to employees who are carers?"
    print("\n" + "=" * 78)
    print("THE QUESTION")
    print("=" * 78)
    print(f"  \"{question}\"")

    ranking = score(tree.leaves, question)

    print("\n" + "=" * 78)
    print("WHAT THE SEARCH SEPARATES (scores on the small fragments)")
    print("=" * 78)
    for leaf, s in ranking:
        print(f"  score {s:.2f} — {leaf.path[-1]}")
        print(f"             \"{leaf.text}\"")

    leaf, best = ranking[0]

    print("\n" + "=" * 78)
    print("WHAT THE SYSTEM KEEPS")
    print("=" * 78)
    print(f"  fragment (score {best:.2f}) — {leaf.breadcrumb}:")
    print(f"    \"{leaf.text}\"")

    is_exception = "exception" in leaf.text.lower() or \
                   "exception" in leaf.path[-1].lower()
    literal_answer = "three days" if "three" in leaf.text.lower() else "two days"

    print("\n" + "=" * 78)
    print("THE VERDICT")
    print("=" * 78)
    print(f"  Literal answer of the fragment: \"{literal_answer}\".")
    print("  Is the fragment EXACT? Yes: that text exists, word for word.")
    if is_exception:
        print("  The problem: this fragment is the EXCEPTION. In isolation, nothing tells")
        print("  the model that a different general rule exists (\"two days\").")
        print("  A system that restores only this leaf will answer \"three days\"")
        print("  even to an ordinary employee. Exact for the carer, false for the rest.")
    print("\n  Search succeeded. Context lost. That is the paradox of the chapter.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- A fragment can be perfectly exact and still lead to a wrong answer:")
    print("  it is enough that it was cut off from what qualified it.")
    print("- The danger is not the FALSE fragment, which is spottable, but the TRUE")
    print("  one out of context, which presents itself with the authority of a fact.")

    print("\nWHAT TO REMEMBER")
    print("- Retrieval quality does not guarantee answer quality.")
    print("- Here the error does not come from the cut: it comes from the LOST CONTEXT.")
    print("- In the next lab: how to recover that context, by climbing the tree.")


if __name__ == "__main__":
    main()
