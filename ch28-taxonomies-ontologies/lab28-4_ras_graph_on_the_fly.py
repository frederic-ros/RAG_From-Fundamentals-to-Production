# -*- coding: utf-8 -*-
"""
Lab 28-4 — RAS: Retrieval-And-Structuring (a graph on the fly)
"No global index: only what the question touches is structured"

The aim: rather than structuring the WHOLE graph in advance — expensive, and out
of date as soon as a document changes — a targeted retrieval is run first, and a
small semantic graph is built ON THE FLY over those fragments alone. Ideal for
fast-moving corpora, reports that change every day.

For "what does pump P-42 depend on?", RAS reads only 3 fragments, extracts a mini
graph of a few edges, and answers — without ever having indexed the 25 reports
as a graph.

No API key. Run generate_corpus.py first.
"""

from businesskit import (Ontology, build_ras, load_fragments, bandeau)


QUESTIONS = [
    "What does pump P-42 depend on, and what risks does it carry?",
    "Which intervention procedure on a pump, and which technician is responsible?",
]


def main():
    bandeau("Lab 28-4 — RAS: Retrieval-And-Structuring (a graph on the fly)")
    onto = Ontology.load()
    frags = load_fragments()
    K = 4

    print(f"\nComplete corpus: {len(frags)} reports.")
    print("The RAS strategy: the global graph is NOT indexed. For each question the")
    print(f"{K} closest fragments are retrieved, and only those are then")
    print("those fragments alone into a mini-graph constrained by the ontology.\n")

    for q in QUESTIONS:
        print("═" * 74)
        print(f"QUESTION : {q}")
        graphe = build_ras(frags, q, ontologie=onto, k=K)

        print(f"\n  Mini-graph built on the fly: "
              f"{len(graphe.nodes)} instances, {len(graphe)} edges "
              f"(over the {K} fragments read, not {len(frags)}).")
        if graphe.aretes:
            print("  Edges:")
            for s, l, o in graphe.aretes:
                print(f"     {s} --{l}--> {o}")
        else:
            print("  (no typed relation extracted from these fragments)")

        # exemple of interrogation of the mini-graph
        cible = "pompe p 42"
        if cible in graphe.nodes:
            risques = graphe.voisins(cible, "carries_risk_of")
            circuits = graphe.voisins(cible, "fed_by")
            print(f"\n  Querying the mini-graph on \"{cible}\":")
            print(f"     fed by: {circuits or '-'}")
            print(f"     risques       : {risques or '—'}")
        print()

    print("═" * 74)
    print("THE MESSAGE: classic GraphRAG indexes the WHOLE graph in advance —")
    print("precise but costly and quickly stale. RAS reverses the order: retrieve")
    print("retrieve first, structure second, and only what is useful. On a")
    print("corpus that changes every day, you pay for the structuring only on")
    print("the fragments actually consulted.")
    print("\nTHE LIMIT: RAS sees only the local neighbourhood of the question. A")
    print("global question (\"map every dependency\") remains the territory of the")
    print("pre-indexed graph. The two approaches complete each other.")


if __name__ == "__main__":
    main()
