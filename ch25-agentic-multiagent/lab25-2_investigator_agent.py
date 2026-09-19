# -*- coding: utf-8 -*-
"""
Lab 25-2 — The investigator agent: following a chain of dependencies

Learning objective
------------------
Some questions cannot be answered in one search, because the answer is a CHAIN.
"Which equipment is impacted if pump P-42 fails?" requires following P-42 to E-7,
and E-7 to L-3 — hop by hop, each hop discovered by the previous one.

The agent decomposes, searches, reads what it finds, and searches again from what
it has just learnt. Its investigation trace is displayed hop by hop.

    An investigator agent does not plan its route in advance.
    It discovers the next step in the answer to the last one.

No API key. Run generate_corpus.py first.
"""

import json
import re
from collections import deque
from pathlib import Path

import agentkit as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"

ENTITE = re.compile(r"\b[ELPM]-\d{1,3}\b")


def enqueter(entite_depart, outil, compteur, budget=6):
    """The investigator agent: decomposes in cascade from an entity, by searching.

    Returns (chain, trace), where the chain is the ordered set of impacted
    entities and the trace is the sequence of reasoning.
 """
    file = deque([entite_depart])
    vus = {entite_depart}
    impacts = []          # (entite, passage justifiant l'impact)
    trace = []

    while file and compteur.recherches < budget:
        courant = file.popleft()
        compteur.rech()
        res = outil.appeler(requete=f"{courant} dependency impact equipment")
        # Keep the most relevant passage that mentions the current entity.
        passage = next((r["text"] for r in res
                        if courant.lower() in r["text"].lower()), res[0]["text"])
        trace.append(f"search(\"{courant}\") -> {passage[:70]}…")

        # Extract the entities named in this passage: its downstream dependencies.
        candidates = [e for e in ENTITE.findall(passage) if e != courant]
        for dep in candidates:
            if dep not in vus:
                vus.add(dep)
                file.append(dep)
                impacts.append((dep, passage))
                trace.append(f"   -> dependency discovered: {dep} "
                             f"(added to the investigation queue)")
    return impacts, trace


def main() -> None:
    print("=" * 78)
    print("Lab 25-2 — The investigator agent: one question, several searches")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = A.Search([f["text"] for f in frags])
    outil = A.search_tool(rech, frags, k=4)

    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Cerveau : {A.mode_cerveau()}")

    question = "Which equipment is impacted if pump P-42 fails?"
    print("\n" + "=" * 78)
    print(f"JULIEN'S QUESTION: \"{question}\"")
    print("=" * 78)

    # --- The comparison: a single search against the investigator agent -------
    print("\n  [SINGLE SEARCH — one turn]")
    cpt_naif = A.Counter()
    cpt_naif.rech()
    res = outil.appeler(requete=question)
    print(f"    → trouve : {res[0]['subject']} ({res[0]['text'][:60]}…)")
    print("    -> but it does NOT follow the chain of dependencies. Incomplete.")

    print("\n  [The INVESTIGATOR agent — decomposes in cascade]")
    cpt = A.Counter()
    impacts, trace = enqueter("P-42", outil, cpt)
    print("    Trace du raisonnement :")
    for ligne in trace:
        print(f"      {ligne}")

    # --- Construction of the answer ----------------------------------------
    entites_impactees = [e for e, _ in impacts]
    passages = list({p for _, p in impacts})
    if A.ollama_disponible():
        cpt.llm()
        contexte = "\n".join(f"- {p}" for p in passages)
        reponse = A._llm(
            "From the chain of dependencies discovered, explain which equipment is "
            "impacted if pump P-42 fails.\n\n"
            f"{contexte}\n\nAnswer:", num_predict=200)
    else:
        if entites_impactees:
            reponse = (f"If pump P-42 fails, the equipment impacted is: "
                       f"{', '.join(entites_impactees)}. The chain: P-42 supplies "
                       f"heat exchanger E-7, on which production line L-3 depends.")
        else:
            reponse = "No dependency identified in the corpus."

    print("\n  THE ANSWER BUILT:")
    print(f"    {reponse[:240]}")
    print(f"\n  Impact chain: P-42 -> {' -> '.join(entites_impactees)}")
    print(f"  Cost: {cpt.summary()}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  A single search finds the P-42 sheet and stops there. The investigator")
    print("  agent spots that P-42 supplies E-7, that E-7 governs L-3, and follows the")
    print("  chain to its end — several searches for one question.")
    print("\n  WHAT TO REMEMBER: the agent DECOMPOSES the problem before answering.")
    print("  That is the planner pattern: turning a question into an investigation.")


if __name__ == "__main__":
    main()
