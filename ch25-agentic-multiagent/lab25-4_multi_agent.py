# -*- coding: utf-8 -*-
"""
Lab 25-4 — Multi-agent: the Council of Guardians

Learning objective
------------------
Rather than inflating a single agent until it knows everything, expertise is
DISTRIBUTED across specialists, each with its own corpus: Julien (maintenance),
Claire (HR), Sophie (architecture). Four roles orchestrate them:

    PLANNER    — decomposes and chooses which specialists to mobilise;
    EXECUTOR   — collects their contributions;
    CRITIC     — re-reads, and rejects the contributions that are not reliable;
    SUPERVISOR — synthesises, within a budget, and can interrupt.

Three cases are shown: a single-domain question, a crossing question that
mobilises several, and a case where a mobilised agent has nothing reliable to
say — which is where the Critic earns its place.

    Without a Supervisor and a Critic, a multi-agent system is not reliable.
    It is an amplifier of risk.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentkit as A

FRAG = Path(__file__).resolve().parent / "corpus" / "fragments.json"
DOM = Path(__file__).resolve().parent / "corpus" / "domains.json"


def build_council(frags, domaines):
    """Create the three specialist agents, each with its own restricted corpus."""
    specialistes = []
    for cle, info in domaines.items():
        sous_corpus = [frags[i] for i in info["fragments"]]
        rech = A.Search([f["text"] for f in sous_corpus])
        outil = A.search_tool(rech, sous_corpus, k=2)
        specialistes.append(A.SpecialistAgent(
            nom=info["agent"], domaine=cle, outil=outil,
            mots_cles=info["keywords"]))
    return specialistes


def show(question, orch):
    print("\n" + "=" * 78)
    print(f"QUESTION: \"{question}\"")
    print("=" * 78)
    r = orch.process(question)
    print("  The council deliberates :")
    for ligne in r["trace"]:
        role = ligne.split(":")[0]
        print(f"    [{role:<10s}] {ligne.split(':', 1)[1].strip()}")
    print(f"\n  THE COLLECTIVE ANSWER :\n    {r['reponse'][:260]}")
    print(f"\n  Contributions kept : "
          f"{[c['agent'] for c in r['retenues']]}")
    if r["rejetees"]:
        print(f"  Contributions rejected by the Critic : "
              f"{[c['agent'] for c in r['rejetees']]}")
    print(f"  Cost: {r['cout'].summary()}")
    return r


def main() -> None:
    print("=" * 78)
    print("Lab 25-4 — Multi-agent: the Council of Guardians")
    print("=" * 78)

    if not FRAG.exists() or not DOM.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    frags = json.loads(FRAG.read_text(encoding="utf-8"))["fragments"]
    domaines = json.loads(DOM.read_text(encoding="utf-8"))
    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Cerveau : {A.mode_cerveau()}")

    specialistes = build_council(frags, domaines)
    orch = A.Orchestrator(specialistes, budget=6)
    print("The council, constituted:")
    for s in specialistes:
        print(f"  - Agent {s.nom:<7s} — domain {s.domaine}")

    # --- Case 1: a single-domain question (one relevant specialist) -----------
    show("What is the emergency stop procedure for pump P-42?", orch)

    # --- Cas 2 : question transverse (several expertises) -----------------
    show("For night maintenance work on motor M-18, what bonus applies and who "
         "must supervise a multi-agent system?", orch)

    # --- Case 3: the Critic at work (a mobilised agent has nothing reliable) ---
    # "motor failure" mobilises Julien, but the question is about a BONUS: the
    # maintenance corpus holds nothing relevant, so the Critic rejects his
    # contribution, while Claire (HR) answers correctly.
    #
    # This case only works if the question hits BOTH domains' keywords. Left in
    # French against the English keyword lists it mobilised Julien alone, and the
    # Critic had no correct contribution to contrast with.
    #
    # THE WORDING IS CALIBRATED. Julien must be mobilised (his keyword "motor" is
    # present) but score BELOW the reliability threshold of 0.18, so the Critic
    # rejects him; Claire must land on the night-bonus fragment well above it.
    # A first English wording put Julien at 0.21, just over the line: his
    # off-topic contribution about pump P-42 was kept, and the Critic had nothing
    # to reject. Check the scores printed by this lab if you reword it.
    show("If a motor fails at night, what salary supplement and compensatory "
         "rest apply?", orch)

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  The Planner mobilises only the relevant specialists; the Executor")
    print("  collects their contributions; the Critic discards those that are not")
    print("  reliable (an agent with no information on the subject); the Supervisor")
    print("  synthesises within the budget. No agent called another directly.")
    print("\n  KEY MESSAGE: a multi-agent system DISTRIBUTES expertise instead of overloading one")
    print("  a single agent. And without a Supervisor and a Critic, you do not have a")
    print("  agentic foundation, it merely amplifies risk.")


if __name__ == "__main__":
    main()
