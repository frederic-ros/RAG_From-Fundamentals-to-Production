# -*- coding: utf-8 -*-
"""
Lab 21-5 — The router: choosing the right transformation

Learning objective
------------------
We now have a whole arsenal: HyDE, expansion, decomposition, step-back,
rewriting. But applying them ALL, all the time, would be expensive and sometimes
harmful. The mature approach is to ROUTE: examine the question, then choose THE
transformation that suits it.

    A mature system does not transform every question the same way.
    It chooses the strategy according to the problem it meets.

This lab presents five questions of different natures, shows the router's
decision for each, applies the chosen transformation, and checks that it brings
the right document to the top.

THIS IS THE LAB TO RUN AFTER EDITING ANY QUESTION OR ANY WORD LIST. It prints
the routing decision for all five, and a wrong branch shows up immediately.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import qtlib as Q

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def appliquer(strategie: str, question: str, history, R):
    """Apply the chosen transformation and return (ranking, detail)."""
    if strategie == "rewriting":
        q = Q.rewriting(question, history)
        return [i for i, _ in R.classer(q)], f"rewritten: \"{q}\""
    if strategie == "decomposition":
        subs = Q.decomposition(question)
        return [i for i, _ in R.classer_multi(subs)], f"sous-questions : {subs}"
    if strategie == "hyde":
        doc = Q.hyde(question)
        return [i for i, _ in R.classer(doc)], f"hypothetical doc: \"{doc[:55]}…\""
    if strategie == "step_back":
        q = Q.step_back(question)
        return [i for i, _ in R.classer(q)], f"step-back question: \"{q}\""
    if strategie == "expansion":
        reforms = Q.expansion(question)
        return [i for i, _ in R.classer_multi(reforms)], f"reformulations : {reforms}"
    return [i for i, _ in R.classer(question)], "no transformation"


def main() -> None:
    print("=" * 78)
    print("Lab 21-5 — Which tool to choose? (the adaptive router)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    R = Q.Search(texts)
    print(f"\nMode de search : {Q.mode()}")
    print("\nThe router examines each question and chooses ONE transformation:")
    print("  pronoun -> rewriting | comparison -> decomposition | individual case -> step-back")
    print("  problem vocabulary -> HyDE | otherwise (vague) -> expansion")

    queries = data["queries"]
    hits = 0
    print("\n" + "=" * 78)
    print("ROUTER DECISIONS AND RESULTS")
    print("=" * 78)

    for req in queries:
        question = req["question"]
        history = req.get("history", [])
        best = req["relevant"][0]
        attendu = req["type"]

        # The router's decision, without cheating: it does not know the answer.
        choix = Q.router(question, history)
        accord = "OK" if choix == attendu else f"(attendu : {attendu})"

        # Direct rank (before) versus rank after transformation.
        rank_before = Q.rank_of([i for i, _ in R.classer(question)], best)
        ranking, detail = appliquer(choix, question, history, R)
        rank_after = Q.rank_of(ranking, best)
        if rank_after == 1:
            hits += 1

        print(f"\n  Question: \"{question[:60]}\"")
        print(f"    Routeur -> {choix}  {accord}")
        print(f"    {detail}")
        print(f"    Rank of the right document: {rank_before} (before) -> {rank_after} (after)")

    print("\n" + "=" * 78)
    print("BILAN")
    print("=" * 78)
    print(f"  Right document in first place after transformation: "
          f"{hits}/{len(queries)} queries.")
    print("  The router chose the strategy suited to each kind of question.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- No transformation is universally the best: each answers one kind of")
    print("  problem — vocabulary, composition, pronoun, over-specificity.")
    print("- The router reads the question and engages the right strategy, instead of")
    print("  applying everything blindly, which would cost dearly and sometimes harm.")
    print("- This is the move from a fixed pipeline to an ADAPTIVE one.")

    print("\nWHAT TO REMEMBER")
    print("- Routing = diagnose the question, then choose the transformation.")
    print("- A mature system adapts its strategy to the problem it meets.")
    print("- One question stays open: what if a single pass were not enough? (Lab 21-6)")


if __name__ == "__main__":
    main()
