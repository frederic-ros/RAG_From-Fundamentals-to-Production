# -*- coding: utf-8 -*-
"""
Lab 14-4 — Small-to-big in practice (Claire)

Learning objective
------------------
The complete pipeline is finally assembled, and MEASURED. Small-to-big is the
strategy of the previous lab turned into a reproducible chain:

    Question
      v
    Search over the small fragments (precision)
      v
    Identification of the best fragment
      v
    Climb towards the parent (context)
      v
    Construction of the final context
      v
    Answer

Two pipelines are evaluated on a small question set, and three things are
quantified:

  - answer quality: does the supplied context hold EVERYTHING needed to answer
    correctly (the rule and, where needed, its exception)?
  - error rate: the proportion of answers where the context misleads — an
    exception presented as a rule, for instance;
  - hallucinations: here in the sense of "the model would have to fill a gap the
    context does not cover" — a truncated context invites invention.

  Small fragments improve the search.
  Large fragments improve the understanding.

No API key. No generative model: what is measured is the QUALITY OF THE CONTEXT
supplied to the model, which is what chunking actually controls.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple, Dict

import tree as T

CORPUS = Path(__file__).resolve().parent / "corpus"
DOC = CORPUS / "remote_work_agreement.json"


# Evaluation set: question -> what the context MUST hold in order to answer
# correctly. The requirement is expressed as markers present in the source text.
EVAL = [
    {
        "question": "How many days of remote work for an ordinary employee?",
        "must_contain": ["two days"],
        "must_not_mislead": ["three days"],   # if ONLY "three days" comes back -> error
    },
    {
        "question": "How many days are granted to employees who are carers?",
        "must_contain": ["three days", "carers"],
        "must_not_mislead": [],
    },
    {
        "question": "What are the remote work rules, general case and exceptions?",
        "must_contain": ["two days", "three days"],
        "must_not_mislead": [],
    },
]


class Pipeline:
    def __init__(self, leaves: List[T.Leaf]):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.leaves = leaves
        self._vec = TfidfVectorizer()
        self._mat = self._vec.fit_transform([leaf.text for leaf in leaves])

    def best_child(self, question: str) -> Tuple[T.Leaf, float]:
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([question])
        sims = cosine_similarity(q, self._mat)[0]
        idx = int(sims.argmax())
        return self.leaves[idx], float(sims[idx])


def flat_context(tree: T.Tree, pipe: Pipeline, question: str) -> str:
    """Flat system: restore the small fragment that was found, as it stands."""
    child, _ = pipe.best_child(question)
    return child.text


def small_to_big_context(tree: T.Tree, pipe: Pipeline, question: str) -> str:
    """Small-to-big: search small, then climb to the context parent."""
    child, _ = pipe.best_child(question)
    parent = tree.context_of(child)
    return parent.text


def evaluate(name: str, supply_context) -> Dict:
    tree = T.load(DOC)
    pipe = Pipeline(tree.leaves)
    ok, errors, gaps = 0, 0, 0
    details = []
    for case in EVAL:
        ctx = supply_context(tree, pipe, case["question"]).lower()
        complete = all(m.lower() in ctx for m in case["must_contain"])
        # Error: the context holds a misleading marker WITHOUT the correct one.
        misleads = False
        for trap in case["must_not_mislead"]:
            if trap.lower() in ctx and not all(
                m.lower() in ctx for m in case["must_contain"]
            ):
                misleads = True
        if complete and not misleads:
            ok += 1
            verdict = "CORRECT"
        elif misleads:
            errors += 1
            verdict = "ERROR (misleading context)"
        else:
            gaps += 1
            verdict = "GAP (incomplete context -> risk of hallucination)"
        details.append((case["question"], verdict))
    n = len(EVAL)
    return {
        "name": name, "n": n, "ok": ok, "errors": errors, "gaps": gaps,
        "quality": ok / n, "error_rate": errors / n, "halluc": gaps / n,
        "details": details,
    }


def bar(p: float, width: int = 20) -> str:
    filled = int(round(p * width))
    return "█" * filled + "·" * (width - filled)


def main() -> None:
    print("=" * 78)
    print("Lab 14-4 — Small-to-big in practice (Claire)")
    print("=" * 78)

    if not DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    print("\nTHE SMALL-TO-BIG PIPELINE")
    print("-" * 78)
    print("  Question -> search over small fragments -> best fragment")
    print("           -> climb to the parent -> final context -> answer")

    flat = evaluate("Flat system (search small, answer small)", flat_context)
    s2b = evaluate("Small-to-big (search small, answer large)", small_to_big_context)

    print("\n" + "=" * 78)
    print("RESULTS, QUESTION BY QUESTION")
    print("=" * 78)
    for res in (flat, s2b):
        print(f"\n{res['name']}")
        for q, verdict in res["details"]:
            print(f"  - \"{q[:54]}…\"")
            print(f"      -> {verdict}")

    print("\n" + "=" * 78)
    print("MEASUREMENTS (over 3 questions)")
    print("=" * 78)
    print(f"{'':42}{'flat':>10}{'small-to-big':>16}")
    print(f"  answer quality {'':22} {flat['quality']:>6.0%}     "
          f"{s2b['quality']:>10.0%}")
    print(f"  error rate {'':26} {flat['error_rate']:>6.0%}     "
          f"{s2b['error_rate']:>10.0%}")
    print(f"  hallucination risk (gaps) {'':11} {flat['halluc']:>6.0%}     "
          f"{s2b['halluc']:>10.0%}")

    print("\n  Answer quality:")
    print(f"    flat          {bar(flat['quality'])} {flat['quality']:.0%}")
    print(f"    small-to-big  {bar(s2b['quality'])} {s2b['quality']:.0%}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The entry point is IDENTICAL in both pipelines: the search over small")
    print("  fragments is precise either way.")
    print("- What changes is the CONTEXT restored. The flat system delivers truncated")
    print("  fragments; small-to-big delivers the parent, complete.")
    print("- A measurable result: more correct answers, fewer errors, fewer gaps that")
    print("  the model would be tempted to fill by inventing.")

    print("\nWHAT TO REMEMBER")
    print("- Small fragments improve the search.")
    print("- Large fragments improve the understanding.")
    print("- Small-to-big reconciles the two: search small, answer large.")


if __name__ == "__main__":
    main()
