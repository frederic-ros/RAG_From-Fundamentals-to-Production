# -*- coding: utf-8 -*-
"""
Lab 26-3 — "Search around, or summarise the whole graph?"

The aim: compare two ways of querying a graph — the LOCAL search (the
neighbourhood of an entity) and the GLOBAL search (community summaries) — and
show that the type of question dictates the strategy.

  - A LOCAL question: "Which equipment depends on P-42?"
    -> a neighbourhood traversal, few nodes, precise.
  - A GLOBAL question: "What are the main critical points of the network?"
    -> community summaries, an overall view.

For each strategy the lab prints the nodes visited, the answer, and the cost in
nodes traversed. Each strategy is good for ITS kind of question, and mediocre for
the other.

No API key. Run generate_corpus.py first.
"""

from graphkit import (Graph, load_documents, extract_triples,
                      local_search, global_search, bandeau)


def main():
    bandeau("Lab 26-3 — Local Graph Search vs Global Graph Search")
    docs = load_documents()
    graphe = Graph.depuis_triplets(extract_triples(docs))
    print(f"\nGraph: {len(graphe.nodes)} nodes, {len(graphe.aretes)} edges.")

    # --- Question LOCALE ---------------------------------------------------
    print("\n" + "─" * 72)
    print("A LOCAL QUESTION: \"Which equipment depends on P-42?\"")
    loc = local_search(graphe, ["P-42"], profondeur=3)
    print("  The local strategy ->")
    print("    nodes visited:", loc["n_noeuds"], "->", loc["nodes"])
    print("    faits directs :", loc["faits"])
    dependances = graphe.descendants("P-42", profondeur=3)
    print("    ANSWER: depending on P-42 ->", dependances)
    print("    Precise and inexpensive for a targeted question.")

    # What would GLOBAL retrieval return for the same question? Its view is too broad.
    glob_sur_locale = global_search(graphe)
    print("  The global strategy on the same question ->")
    print("    traverses", glob_sur_locale["n_noeuds"], "nodes (every community)")
    print("    Needlessly wide: the answer is a simple neighbourhood.")

    # --- Question GLOBALE --------------------------------------------------
    print("\n" + "─" * 72)
    print("A GLOBAL QUESTION: \"What are the main critical points of the network?\"")
    glob = global_search(graphe)
    print("  The global strategy ->")
    for c in glob["communautes"]:
        print(f"    {c['communaute']} (taille {c['taille']}) — pivot : {c['pivot']}")
        print(f"        membres : {c['membres']}")
    pivot_principal = glob["communautes"][0]["pivot"] if glob["communautes"] else "?"
    print(f"    ANSWER: the most connected community turns around "
          f"\"{pivot_principal}\"")
    print("    Captures an overall view that no isolated neighbourhood gives.")

    # What would LOCAL retrieval return for this global question? Its view is too narrow.
    loc_sur_globale = local_search(graphe, ["P-42"], profondeur=1)
    print("  The local strategy on the same question ->")
    print("    sees only", loc_sur_globale["n_noeuds"], "nodes around P-42")
    print("    Short-sighted: misses the other critical points (production zone, L-5).")

    # --- The comparison ------------------------------------------------------
    print("\n" + "─" * 72)
    print(f"{'':22}{'nodes visited':>16}{'good for':>22}")
    print(f"{'Local search':22}{loc['n_noeuds']:>16}{'targeted questions':>22}")
    print(f"{'Global search':22}{glob['n_noeuds']:>16}{'aggregation':>22}")
    print("\nTHE MESSAGE: not every question uses the graph the same way.")


if __name__ == "__main__":
    main()
