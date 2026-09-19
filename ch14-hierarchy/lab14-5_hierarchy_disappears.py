# -*- coding: utf-8 -*-
"""
Lab 14-5 — When the hierarchy disappears (bonus)

Learning objective
------------------
An experimental lab. The same documents are processed in two ways:

  Version A: hierarchy PRESERVED
      each fragment knows its section; the parent can be reached.

  Version B: hierarchy REMOVED
      the parent-child links are thrown away; nothing remains but a flat bag of
      indistinguishable fragments.

They are then compared, on a set of trap questions mixing rules and exceptions,
along three symptoms:

  - false positives: an exception fragment returned as though it were the rule;
  - ambiguous answers: no way to decide between rule and exception;
  - rule/exception confusion: the context no longer lets them be told apart.

  The hierarchy is not a piece of metadata.
  It is part of the information.

No API key. Uses tree.py and BOTH documents of the corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple, Dict

import tree as T

CORPUS = Path(__file__).resolve().parent / "corpus"
DOCS = [CORPUS / "remote_work_agreement.json", CORPUS / "procurement_thresholds.json"]


# Trap questions: each targets a GENERAL RULE, while the corpus holds a
# neighbouring exception that can be confused with it.
EVAL = [
    {
        "question": "What is the limit on days of remote work in the general case?",
        "rule": "two days",
        "exception": "three days",
    },
    {
        "question": "Above what threshold does the formal procedure apply in general?",
        "rule": "forty thousand",
        "exception": "eighty thousand",
    },
]


def load_all() -> T.Tree:
    """Merge the leaves and parents of every document into a single space."""
    leaves: List[T.Leaf] = []
    parents: dict = {}
    for d in DOCS:
        if not d.exists():
            continue
        tree = T.load(d)
        leaves.extend(tree.leaves)
        parents.update(tree.parents)
    return T.Tree(root={"title": "corpus"}, leaves=leaves, parents=parents)


class Index:
    def __init__(self, leaves: List[T.Leaf]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.leaves = leaves
        self._vec = TfidfVectorizer()
        self._mat = self._vec.fit_transform([leaf.text for leaf in leaves])

    def top(self, question: str, k: int = 2) -> List[Tuple[T.Leaf, float]]:
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([question])
        sims = cosine_similarity(q, self._mat)[0]
        order = sims.argsort()[::-1][:k]
        return [(self.leaves[i], float(sims[i])) for i in order]


def version_a(tree: T.Tree, index: Index, question: str) -> str:
    """Hierarchy preserved: climb to the context parent of the best child."""
    child, _ = index.top(question, 1)[0]
    return tree.context_of(child).text


def version_b(index: Index, question: str) -> str:
    """Hierarchy removed: only the flat fragment is available."""
    child, _ = index.top(question, 1)[0]
    return child.text


def diagnose(context: str, case: Dict) -> str:
    c = context.lower()
    has_rule = case["rule"].lower() in c
    has_exc = case["exception"].lower() in c
    if has_rule and has_exc:
        return "CORRECT (rule and exception tellable apart)"
    if has_exc and not has_rule:
        return "FALSE POSITIVE (exception taken for the rule)"
    if has_rule and not has_exc:
        return "PARTIAL (rule alone, exception invisible)"
    return "AMBIGUOUS (neither one clearly)"


def main() -> None:
    print("=" * 78)
    print("Lab 14-5 — When the hierarchy disappears (bonus)")
    print("=" * 78)

    if not all(d.exists() for d in DOCS):
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    tree = load_all()
    index = Index(tree.leaves)

    res_a = {"false_positives": 0, "ambiguous": 0, "correct": 0, "partial": 0, "details": []}
    res_b = {"false_positives": 0, "ambiguous": 0, "correct": 0, "partial": 0, "details": []}

    for case in EVAL:
        ctx_a = version_a(tree, index, case["question"])
        ctx_b = version_b(index, case["question"])
        d_a = diagnose(ctx_a, case)
        d_b = diagnose(ctx_b, case)
        res_a["details"].append((case["question"], d_a))
        res_b["details"].append((case["question"], d_b))
        for res, d in ((res_a, d_a), (res_b, d_b)):
            if d.startswith("CORRECT"):
                res["correct"] += 1
            elif d.startswith("FALSE"):
                res["false_positives"] += 1
            elif d.startswith("AMBIGUOUS"):
                res["ambiguous"] += 1
            elif d.startswith("PARTIAL"):
                res["partial"] += 1

    print("\n" + "=" * 78)
    print("VERSION A — HIERARCHY PRESERVED")
    print("=" * 78)
    for q, d in res_a["details"]:
        print(f"  - \"{q[:58]}…\"")
        print(f"      -> {d}")

    print("\n" + "=" * 78)
    print("VERSION B — HIERARCHY REMOVED")
    print("=" * 78)
    for q, d in res_b["details"]:
        print(f"  - \"{q[:58]}…\"")
        print(f"      -> {d}")

    n = len(EVAL)
    print("\n" + "=" * 78)
    print(f"SUMMARY (over {n} trap questions)")
    print("=" * 78)
    print(f"{'':28}{'version A':>14}{'version B':>14}")
    print(f"  correct answers {'':10} {res_a['correct']:>8}/{n}   {res_b['correct']:>8}/{n}")
    print(f"  partial context {'':10} {res_a['partial']:>8}/{n}   {res_b['partial']:>8}/{n}")
    print(f"  false positives {'':10} {res_a['false_positives']:>8}/{n}   "
          f"{res_b['false_positives']:>8}/{n}")
    print(f"  ambiguous answers {'':8} {res_a['ambiguous']:>8}/{n}   {res_b['ambiguous']:>8}/{n}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Without hierarchy (version B), only an isolated fragment comes back: the")
    print("  general rule arrives alone and its exception stays invisible — and the")
    print("  reverse is just as possible, the exception then passing for the rule.")
    print("- With hierarchy (version A), climbing to the parent restores the")
    print("  neighbourhood, and rule and exception become tellable apart again.")
    print("- The difference lies neither in the model nor in the search: it lies in the")
    print("  STRUCTURE that was, or was not, preserved.")

    print("\nWHAT TO REMEMBER")
    print("- The hierarchy is not decorative metadata.")
    print("- It is part of the information: removing it loses meaning.")
    print("- Keeping the tree keeps the ability to tell a rule from an exception.")


if __name__ == "__main__":
    main()
