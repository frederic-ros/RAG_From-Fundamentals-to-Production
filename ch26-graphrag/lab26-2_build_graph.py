# -*- coding: utf-8 -*-
"""
Lab 26-2 — From the document to the network of knowledge

Build a graph of knowledge by extracting triples from the corpus, then query it:
neighbours, shortest path, communities.

The teaching point is not the graph itself, it is the EXTRACTION. Its quality is
measured against the ground truth, and that is where the real difficulty of
GraphRAG sits: a graph is only as good as the triples pulled out of the text.

This lab prints precision, recall and F1 of the extraction. Those figures are the
check on the patterns of graphkit._PATTERNS: if a pattern stops matching the
documents, the recall collapses here with no error raised. The French baseline is
1.00 / 0.73 / 0.84.

No API key. Run generate_corpus.py first.
"""

from graphkit import (Graph, load_documents, load_expected_graph,
                      extract_triples, bandeau, _a_networkx)


def main():
    bandeau("Lab 26-2 — Construire automatiquement son premier graphe")
    docs = load_documents()

    # --- Step 1 : extraction triples --------------------------------
    triplets = extract_triples(docs)
    print(f"\n{len(triplets)} triplets extraits :")
    for s, r, o in triplets:
        print(f"   ({s}) --[{r}]--> ({o})")

    # --- Step 2 : construction of the graph ---------------------------------
    graphe = Graph.depuis_triplets(triplets)
    print(f"\nGraph built: {len(graphe.nodes)} nodes, {len(graphe.aretes)} edges.")

    # --- Step 3: the quality of the extraction (the real difficulty) ----------
    attendus = load_expected_graph()
    if attendus:
        m = graphe.evaluate_against(attendus)
        print("\nQuality of the extraction (against the ground truth):")
        print(f"   precision = {m['precision']:.2f}   recall = {m['recall']:.2f}   "
              f"F1 = {m['f1']:.2f}")
        print(f"   ({m['vrais_positifs']} correct triples out of {m['extraits']} extracted, "
              f"{m['attendus']} attendus)")
        print("   -> In real use (Ollama) these figures MOVE: the LLM makes mistakes")
        print("     sometimes of relation. That is the whole point of this lab.")

    # --- Step 4 : interroger the graph -----------------------------------
    print("\nQueries over the graph:")
    print("   voisins(P-42)         =", [v for _, v in graphe.voisins("P-42")])
    path = graphe.path("P-42", "product X")
    print("   path(P-42→produit X)=", " → ".join(path) if path else "introuvable")
    print("   descendants(P-42)     =", graphe.descendants("P-42", profondeur=4))

    # --- Step 5 : visualisation optionnelle ------------------------------
    if _a_networkx():
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import networkx as nx
            g = graphe.to_networkx()
            pos = nx.spring_layout(g, seed=42)
            plt.figure(figsize=(9, 6))
            nx.draw(g, pos, with_labels=True, node_color="#cfe3ff",
                    edge_color="#7aa6d6", node_size=1600, font_size=8)
            nx.draw_networkx_edge_labels(
                g, pos, edge_labels=nx.get_edge_attributes(g, "label"), font_size=7)
            plt.title("Graph de connaissances — chapitre 26")
            plt.tight_layout()
            plt.savefig("graph_ch26.png", dpi=130)
            print("\nVisualisation written: graph_ch26.png")
        except Exception as e:
            print(f"\n(visualisation skipped: {e})")
    else:
        print("\n(networkx absent: visualisation skipped — pip install networkx matplotlib)")

    print("\nTHE MESSAGE: the hard part is not the graph,")
    print("             it is extracting the relations correctly.")


if __name__ == "__main__":
    main()
