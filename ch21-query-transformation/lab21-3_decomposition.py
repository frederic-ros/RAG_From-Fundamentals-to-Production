# -*- coding: utf-8 -*-
"""
Lab 21-3 — One question or three? (decomposition)

Learning objective
------------------
Some questions are not one question. "Compare the maintenance of pump A and pump
B" is really TWO searches disguised as one. Run as it stands, the single search
mixes the two subjects and answers neither well.

    A compound question often hides several searches.

This lab shows the failure of the single search — neither of the two good
documents at the top — then decomposes the question into sub-questions, searches
for each, and gathers the results. Recall is measured: how many of the relevant
documents are found.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import qtlib as Q

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 21-3 — One question or three? (decomposition)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    R = Q.Search(texts)
    print(f"\nMode de search : {Q.mode()}")

    relevant = [2, 3]  # maintenance pompe A, maintenance pompe B
    question = "Compare the maintenance of pump A and pump B."
    print(f"\nQuestion: \"{question}\"")
    print("Expected correct documents: #2 (pump A) and #3 (pump B).")

    # --- Search directe -------------------------------------------------
    print("\n" + "=" * 78)
    print("1) THE DIRECT SEARCH (one query for two subjects)")
    print("=" * 78)
    for rank, (i, s) in enumerate(R.classer(question)[:5], start=1):
        mark = "  <-- relevant" if i in relevant else ""
        print(f"  rank {rank} : #{i:2d} [{frags[i]['subject']}]{mark}")
    print("\n  The single query returns ONE mixed ranking: the A and B documents")
    print("  compete with each other, with no distinct \"for A... / for B...\" answer.")
    print("  There is no way to compare properly from that single list.")

    # --- Decomposition --------------------------------------------------------
    sous_questions = Q.decomposition(question)
    print("\n" + "=" * 78)
    print("2) WITH DECOMPOSITION (one search per sub-question)")
    print("=" * 78)
    print("  Sub-questions generated:")
    for sq in sous_questions:
        print(f"    - \"{sq}\"")

    print("\n  Each sub-question isolates ITS OWN document:")
    tout_bon = True
    for sq in sous_questions:
        cl = [i for i, _ in R.classer(sq)]
        top = cl[0]
        est_bon = top in relevant
        tout_bon = tout_bon and est_bon
        print(f"    \"{sq}\" -> #{top} [{frags[top]['subject']}]"
              f"{'  (relevant)' if est_bon else ''}")

    decomp = [i for i, _ in R.classer_multi(sous_questions)]
    rappel_decomp = Q.rappel_at_k(decomp, relevant, k=2)

    # --- Metrics ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("THE GAIN: A CLEAN ANSWER PER SUBJECT")
    print("=" * 78)
    print("  Direct search: one mixed ranking for two subjects.")
    print("  Decomposition: each sub-question finds its own document at the top")
    print(f"                      ({'both correct' if tout_bon else 'see above'}),")
    print("                      which allows a real A / B comparison.")
    print(f"  Recall@2 of the decomposed merge: {rappel_decomp:.0%}.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- One query for two subjects dilutes both: neither A nor B comes out")
    print("  cleanly, because their documents compete in the same ranking.")
    print("- To decompose is to ask one question per subject, search separately, then")
    print("  gather. Each sub-search is clean, and the fusion covers everything.")
    print("- It is indispensable as soon as a question holds \"compare\", \"and\", \"or\",")
    print("  or several entities.")

    print("\nWHAT TO REMEMBER")
    print("- A compound question hides several searches.")
    print("- Decomposition handles each sub-question apart, then merges.")
    print("- The cost is several searches instead of one — often a good trade.")


if __name__ == "__main__":
    main()
