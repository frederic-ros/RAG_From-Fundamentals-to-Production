# -*- coding: utf-8 -*-
"""
Lab 21-1 — Julien asks the wrong question (the vocabulary gap)

Learning objective
------------------
Open the chapter on its founding observation: a good question can be a bad
search. The user and the document do not speak the same language. The user uses
the language of the PROBLEM ("it is making an odd noise"), the document that of
the SOLUTION ("the vibration signature of a bearing defect").

    A good question is not always a good search.

This lab stages Julien: his raw question ranks the right document far down the
list. Then the question is transformed — a simple expansion into the technical
vocabulary — and the right document rises at once. The gain is put in figures:
the rank of the right document, and the MRR.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import qtlib as Q

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 21-1 — Julien asks the wrong question (the vocabulary gap)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    R = Q.Search(texts)
    print(f"\nMode de search : {Q.mode()}")

    best = 0
    question = "The motor is making an odd noise at start-up."
    print(f"\nJulien's question: \"{question}\"")
    print(f"Expected right document: #{best} — \"{texts[best][:60].strip()}…\"")
    print("Both speak of the same thing, but share almost no word.")

    # --- Search directe -------------------------------------------------
    direct = [i for i, _ in R.classer(question)]
    rank_direct = Q.rank_of(direct, best)

    print("\n" + "=" * 78)
    print("1) DIRECT SEARCH (with the raw question)")
    print("=" * 78)
    print(f"  {'rank':>4s} | {'id':>3s} | subject")
    print("  " + "-" * 45)
    for rank, (i, s) in enumerate(R.classer(question)[:5], start=1):
        mark = "  <-- le best" if i == best else ""
        print(f"  {rank:4d} | {i:3d} | {frags[i]['subject']}{mark}")
    print("  ...")
    print(f"\n  The best document #{best} sits at rank {rank_direct}: the raw question,")
    print("  phrased in the language of the problem, is a bad key.")

    # --- With transformation (expansion toward the vocabulary solution) -------
    reforms = Q.expansion(question)
    fusion = [i for i, _ in R.classer_multi(reforms)]
    reform_rank = Q.rank_of(fusion, best)

    print("\n" + "=" * 78)
    print("2) WITH REFORMULATION (towards the language of the solution)")
    print("=" * 78)
    print("  Reformulations generated:")
    for r in reforms:
        print(f"    - \"{r}\"")
    print(f"\n  {'rank':>4s} | {'id':>3s} | subject")
    print("  " + "-" * 45)
    for rank, (i, s) in enumerate(R.classer_multi(reforms)[:3], start=1):
        mark = "  <-- the good one, lifted" if i == best else ""
        print(f"  {rank:4d} | {i:3d} | {frags[i]['subject']}{mark}")
    print(f"\n  The right document #{best} is now at rank {reform_rank}.")

    # --- Metrics ---------------------------------------------------------
    mrr_direct = Q.mrr(direct, [best])
    mrr_reform = Q.mrr(fusion, [best])
    print("\n" + "=" * 78)
    print("3) THE GAIN, IN FIGURES")
    print("=" * 78)
    print(f"  {'method':<20s} | {'rank of right doc':>17s} | {'MRR':>6s}")
    print("  " + "-" * 48)
    print(f"  {'directe':<20s} | {str(rank_direct):>15s} | {mrr_direct:6.3f}")
    print(f"  {'reformulation':<20s} | {str(reform_rank):>15s} | {mrr_reform:6.3f}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The retrieval was not at fault: the right document was there, indexed.")
    print("- The question, written in the language of the problem, shared none of the")
    print("  words of the document, written in the language of the solution.")
    print("- Transforming the question towards the right vocabulary is enough to lift")
    print("  the right answer: we changed the key, not the lock.")

    print("\nWHAT TO REMEMBER")
    print("- The user speaks the language of the PROBLEM, the document that of the SOLUTION.")
    print("- The raw question is often a bad search key.")
    print("- What remains is the most counter-intuitive transformation: HyDE (Lab 21-2).")


if __name__ == "__main__":
    main()
