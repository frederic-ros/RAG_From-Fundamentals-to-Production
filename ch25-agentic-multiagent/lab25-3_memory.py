# -*- coding: utf-8 -*-
"""
Lab 25-3 — Memory: short term and long term

Learning objective
------------------
Without memory, every question starts from nothing. This lab shows two distinct
memories at work:

  - SHORT-TERM memory holds the thread of the conversation, so that an elliptical
    question ("And for the P-42?") recovers its subject from the previous turn.
    It compresses itself when the conversation grows long;
  - LONG-TERM memory persists what the agent has LEARNT across sessions:
    preferences, established facts. It survives the end of the conversation.

    Short-term memory is the thread of the conversation.
    Long-term memory is the experience of the agent.

THE ELLIPTICAL QUESTIONS ARE THE POINT. Turns 2 and 5 of the conversation lose
their subject without memory. This lab prints, turn by turn, whether the referent
was resolved — which makes it the verification lab for the ellipsis markers of
agentkit.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentkit as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"
CONV = Path(__file__).resolve().parent / "corpus" / "conversation.json"
MEMOIRE_LT = Path(__file__).resolve().parent / "corpus" / "memoire_long_terme.json"


def without_memory(questions, outil):
    """Each question handled in isolation: no thread is kept."""
    print("  [WITHOUT short-term memory] — each question starts from nothing")
    for q in questions:
        ag = A.AgentRAG(outil=outil, memoire=A.ShortTermMemory())  # memory neuve
        r = ag.repondre(q)
        resolu = [t for t in r["trace"] if "referent" in t]
        note = "  (reference NOT resolved)" if not resolu and "and for" in q.lower() \
            or "pareil" in q.lower() and not resolu else ""
        print(f"    Q: {q}")
        print(f"    R: {r['reponse'][:80]}{note}")


def with_memory(questions, outil):
    """A continuous conversation: short-term memory keeps the thread and resolves the references."""
    print("  [WITH short-term memory] — the thread is kept")
    ag = A.AgentRAG(outil=outil, memoire=A.ShortTermMemory(seuil_compression=3))
    for q in questions:
        r = ag.repondre(q)
        resolu = [t for t in r["trace"] if "referent" in t]
        note = f"  ({resolu[0]})" if resolu else ""
        print(f"    Q: {q}")
        print(f"    R: {r['reponse'][:80]}{note}")
    print("\n    The state of the memory at the end of the conversation:")
    if ag.memoire.summary:
        print(f"      Compressed summary: {ag.memoire.summary}")
    print(f"      Known referents: {ag.memoire.referents()}")
    return ag


def main() -> None:
    print("=" * 78)
    print("Lab 25-3 — Short-term and long-term memory: the agent that remembers")
    print("=" * 78)

    if not CORPUS.exists() or not CONV.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = A.Search([f["text"] for f in frags])
    outil = A.search_tool(rech, frags, k=3)
    questions = json.loads(CONV.read_text(encoding="utf-8"))["turns"]

    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Cerveau : {A.mode_cerveau()}")

    # ===================================================================
    # PARTIE 1 — Memory court terme : with vs without
    # ===================================================================
    print("\n" + "=" * 78)
    print("PART 1 — SHORT-TERM MEMORY: with against without")
    print("=" * 78)
    print("Claire's conversation (implicit references, \"and for the P-42?\")\n")
    without_memory(questions, outil)
    print()
    with_memory(questions, outil)

    # ===================================================================
    # PARTIE 2 — Memory long terme : persistance between sessions
    # ===================================================================
    print("\n" + "=" * 78)
    print("PART 2 — LONG-TERM MEMORY: persistence across sessions")
    print("=" * 78)

    lt = A.LongTermMemory(str(MEMOIRE_LT))
    deja = lt.tout()

    if deja:
        print("  SESSION 2 (a restart detected) — the agent recovers its memories:")
        for cle, item in deja.items():
            print(f"    - {cle} = {item['valeur']}  [{item['categorie']}]")
        print(f"\n    Display preference recovered: "
              f"{lt.preferences().get('format_reponse', '(none)')}")
        print("    -> The agent did NOT have to ask again: the memory survived session 1.")
        print("\n  (To replay session 1, delete "
              f"{MEMOIRE_LT.name} puis relancez.)")
    else:
        print("  SESSION 1 (the first run) — the agent establishes durable facts:")
        lt.memoriser("format_reponse", "tableau", "preference")
        lt.memoriser("P-42_reference", "HX-420", "fait")
        lt.memoriser("P-42_cools", "heat exchanger E-7 and line L-3", "fact")
        for cle, item in lt.tout().items():
            print(f"    - memorised: {cle} = {item['valeur']}  [{item['categorie']}]")
        print(f"\n    These memories are written to: {MEMOIRE_LT.name}")
        print("    -> RUN THE LAB AGAIN: session 2 will recover them without asking.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  Without short-term memory, \"and for the P-42?\" loses its referent: the")
    print("  agent does not know what is being talked about. With it, the agent follows")
    print("  on naturally, and compresses the old turns so as not to saturate.")
    print("  Long-term memory makes preferences and facts survive from one session")
    print("  to the next.")
    print("\n  WHAT TO REMEMBER: memory is not a cache. It is the representation of the")
    print("  agent's experience — the library (the corpus) and the notebook (the")
    print("  memory) coexist; neither substitutes for the other.")


if __name__ == "__main__":
    main()
