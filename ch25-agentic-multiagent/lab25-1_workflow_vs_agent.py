# -*- coding: utf-8 -*-
"""
Lab 25-1 — Workflow against agent: where does the decision sit?

Learning objective
------------------
The chapter's distinction is not technological, it is about the LOCATION OF THE
DECISION. A workflow fixes the sequence of steps in advance; an agent decides its
own actions.

Three questions are passed through both, two of them worth searching for and one
trivial:

  - the WORKFLOW searches every time, including for the trivial question;
  - the AGENT judges first, and skips the search when it is useless.

    The difference is not the technology. It is where the decision sits.

The cost of each is counted, so the saving is visible.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentkit as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def workflow(question, outil, compteur):
    """A FIXED pipeline: always searches, then generates. No decision at run time."""
    compteur.rech()
    res = outil.appeler(requete=question)
    passages = [r["text"] for r in res[:2]]
    rep = A.generate(question, passages, compteur=compteur)
    return rep, "search -> generate (always)"


def agent(question, ag, compteur):
    """The agent: DECIDES at run time whether to search or answer directly."""
    r = ag.repondre(question, compteur)
    path = " ; ".join(r["trace"])
    return r["reponse"], path


def main() -> None:
    print("=" * 78)
    print("Lab 25-1 — From workflow to agent: who takes the decision?")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = A.Search([f["text"] for f in frags])
    outil = A.search_tool(rech, frags, k=3)

    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Agent brain: {A.mode_cerveau()}")

    questions = [
        "What is the emergency stop procedure for pump P-12?",   # useful
        "Hello, what is today's date?",                          # trivial
        "What is the supplement for night maintenance work?",    # useful
    ]

    cout_wf = A.Counter()
    cout_ag = A.Counter()
    ag = A.AgentRAG(outil=outil)

    for question in questions:
        print("\n" + "=" * 78)
        print(f"QUESTION: \"{question}\"")
        print("=" * 78)

        rep_wf, chemin_wf = workflow(question, outil, cout_wf)
        print("  [WORKFLOW — pipeline fixe]")
        print(f"    decision: taken IN ADVANCE by the engineer -> {chemin_wf}")
        print(f"    answer  : {rep_wf[:90]}")

        rep_ag, chemin_ag = agent(question, ag, cout_ag)
        print("  [AGENT — decides at run time]")
        print(f"    decision: taken BY THE SYSTEM -> {chemin_ag}")
        print(f"    answer  : {rep_ag[:90]}")

    print("\n" + "=" * 78)
    print("WHERE IS THE DECISION? — cost compared")
    print("=" * 78)
    print(f"  Workflow (always searches): {cout_wf.summary()}")
    print(f"  Agent (searches if needed)  : {cout_ag.summary()}")
    print("\n  On the trivial question the workflow searched for nothing; the agent")
    print("  decided to answer directly. The same tool, the same corpus — only the")
    print("  location of the decision changes.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  The workflow runs a fixed sequence: the decision was taken once, by the")
    print("  designer. The agent decides at each turn, according to the question.")
    print("\n  WHAT TO REMEMBER: workflow or agent, it is not a matter of technology.")
    print("  It is a matter of WHERE THE DECISION SITS — fixed upstream, or taken at")
    print("  run time by the system itself.")


if __name__ == "__main__":
    main()
