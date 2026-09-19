# -*- coding: utf-8 -*-
"""
Lab 24-4 — Adaptive-RAG: choosing the right depth

Learning objective
------------------
Not every question deserves a loop. The Adaptive-RAG router judges the complexity
of a question BEFORE any search, and sends it down one of three paths:

    direct    -> a direct answer from the model, NO search (a trivial question);
    simple    -> one pass of classic RAG (one search is enough);
    iterative -> the complete loop (a complex, multi-facet question).

The router is built (linguistic rules, then an LLM prompt if Ollama is present),
the routing is displayed over a set of heterogeneous questions, and the cost
saved against a "loop for everything" policy is measured.

    The best architecture is the one that uses just enough resources.

THIS IS THE VERIFICATION LAB OF THE CHAPTER. It prints, for all nine questions,
the route decided against the route expected. Run it after editing any question
or any word list in cragkit.py: a wrong branch shows up immediately.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import cragkit as C

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"

# The indicative cost of each path, in operations, to put a figure on the saving.
COUT_VOIE = {"direct": 1, "simple": 2, "iterative": 5}


def main() -> None:
    print("=" * 78)
    print("Lab 24-4 — Adaptive-RAG : choisir la bonne profondeur")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    requetes = data["queries"]
    print(f"\nMode routeur : {C.mode_jugement()}")
    if C.mode_jugement() == "regle":
        print("Router = linguistic rules. For the LLM prompt router:")
        print("  OLLAMA_MODEL=llama3.2 python lab24-4_router.py")

    # --- Visualisation of the routing -------------------------------------------
    print("\n" + "=" * 78)
    print("ROUTING THE QUESTIONS")
    print("=" * 78)
    print(f"  {'route':<10s} | {'expected':<10s} | question")
    print("  " + "-" * 68)
    repartition = {"direct": 0, "simple": 0, "iterative": 0}
    cout_adaptatif = 0
    accord = 0
    for r in requetes:
        voie, just = C.routeur(r["question"])
        attendu = r.get("expected_route", "?")
        repartition[voie] += 1
        cout_adaptatif += COUT_VOIE[voie]
        ok = "OK" if voie == attendu else "!!"
        if voie == attendu:
            accord += 1
        print(f"  {voie:<10s} | {attendu:<10s} | {ok} {r['question'][:48]}")

    # --- The split -----------------------------------------------------------
    print("\n" + "=" * 78)
    print("THE SPLIT AND THE COST")
    print("=" * 78)
    n = len(requetes)
    for voie in ("direct", "simple", "iterative"):
        c = repartition[voie]
        barre = "█" * c
        print(f"  {voie:<10s} : {c}/{n}  {barre}")
    cout_tout_boucle = n * COUT_VOIE["iterative"]
    economie = 100 * (1 - cout_adaptatif / cout_tout_boucle)
    print(f"\n  Cost of \"a loop for everything\": {cout_tout_boucle} operations")
    print(f"  Cost with the adaptive router : {cout_adaptatif} operations")
    print(f"  Saving: {economie:.0f}%  (the loop is paid for only where it counts)")
    print(f"\n  Concordance routeur / annotation : {accord}/{n}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  The router sorts questions by the effort they need and avoids opening an")
    print("  expensive loop for a trivial one. The saving is substantial as soon as")
    print("  the traffic mixes simple and complex questions.")
    print("\n  WHAT TO REMEMBER: Adaptive-RAG is not one more block, it is the")
    print("  switch Self-RAG and CRAG should have had. You pay the right price.")
    print("  A rule router and a prompt router may diverge: that is the signal that")
    print("  something more robust may need training.")


if __name__ == "__main__":
    main()
