# -*- coding: utf-8 -*-
"""
Lab 23-3 — Predefined against agentic reasoning: who decides?

Learning objective
------------------
The chapter places systems on a SLIDER. At one end, PREDEFINED reasoning: the
human writes the loop (multi-query, for instance — N reformulations generated in
advance, all searched in parallel, then merged; a fixed number, no judgement
between turns). At the other end, the AGENTIC: the model judges its own answer
and decides whether to relaunch (reflexive RAG, or Self-RAG).

Both are implemented and compared on two questions:

  - a simple one (1 facet): both succeed; multi-query wastes calls;
  - a complex one (3 facets): both succeed, but Self-RAG ADAPTS — it pays only
    for the turns it needs, and stops early.

What separates them: WHO holds the decision to search again — the engineer
(predefined) or the model (agentic). The distinction holds whether or not an LLM
is running: the regime does not depend on the brain, but on who decides.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentlib as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def neuf_outil(frags):
    return A.SearchTool(A.Search([f["text"] for f in frags]), frags)


def ligne(name, couv, cost, regime):
    etat = "complete" if couv >= 0.999 else f"incomplet ({couv*100:.0f}%)"
    print(f"  {name:<26s} | {etat:<16s} | {cost:>2d} call(s) | {regime}")


def main() -> None:
    print("=" * 78)
    print("Lab 23-3 — Predefined reasoning (multi-query) against agentic (Self-RAG)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Self-RAG brain: {A.mode_brain()}")

    cas = [
        ("SIMPLE (1 volet)",
         "What is the emergency stop procedure for pump P-42?", ["P-42"]),
        ("COMPLEXE (3 facets)",
         "Compare the emergency stop procedures of pumps P-12, P-42 and P-88.",
         ["P-12", "P-42", "P-88"]),
    ]

    for titre, question, facets in cas:
        print("\n" + "=" * 78)
        print(f"CAS {titre}")
        print("=" * 78)
        print(f"Question: \"{question}\"")
        print(f"\n  {'approach':<26s} | {'result':<16s} | {'cost':<9s} | regime")
        print("  " + "-" * 64)

        # Multi-query, the predefined route
        tool = neuf_outil(frags)
        mq = A.multi_query(question, facets, tool)
        couv_mq, _ = A.coverage(mq["context"], facets)
        ligne("multi-query (predefined)", couv_mq, mq["cost"],
              "a number fixed in advance")

        # Self-RAG (agentique)
        tool = neuf_outil(frags)
        sr = A.self_rag(question, facets, tool, budget=5)
        couv_sr, _ = A.coverage(sr["context"], facets)
        ligne("Self-RAG (agentic)", couv_sr, sr["cost"],
              "the model decides and stops")

        if titre.startswith("SIMPLE"):
            print("\n  Reading: on a 1-facet question, multi-query still launches all")
            print("  its reformulations — waste — while Self-RAG stops at the first")
            print("  turn that suffices.")
        else:
            print("\n  Reading: both cover the 3 facets. Multi-query pays a")
            print("  a FIXED cost; Self-RAG pays on demand and stops as soon as it is")
            print("  covered — adaptive, but at the price of a variable trace.")

    print("\n" + "=" * 78)
    print("WHAT THE COMPARISON REVEALS")
    print("=" * 78)
    print("  Multi-query: predictable (fixed cost and latency), but rigid — it does")
    print("  not adapt to the result, and never judges what it brings back.")
    print("  Self-RAG: adaptive — it judges its answer and relaunches as needed — but")
    print("  unpredictable (variable cost and latency).")
    print("\n  WHAT TO REMEMBER: it is not the brain (rule or LLM) that makes the")
    print("  regime, it is WHO holds the decision to search again: the engineer")
    print("  (predefined) or the model (agentic). Reflexive RAG marks the tipping.")


if __name__ == "__main__":
    main()
