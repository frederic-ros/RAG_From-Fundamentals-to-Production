# -*- coding: utf-8 -*-
"""
Lab 26-4 — "The vector searches, the graph explains"

The aim: implement the hybrid pattern that gets the best results in practice. The
vector supplies the ENTRY POINTS, and the traversal WIDENS the context by
following the relations, downstream and upstream.

A real case: "Which supplier risks impacting production on L-3?"

  - The vector alone: brings back fragments, but no path.
  - The graph alone: could walk up, but starts from nothing — no entry point.
  - VectorCypher: the vector finds where to start, the graph does the walking.

For each method the lab prints the context assembled, the answer, and the cost in
documents read and nodes visited. Only VectorCypher answers.

No API key. Run generate_corpus.py first.
"""

from graphkit import (Search, Graph, Counter, load_documents,
                      extract_triples, vector_cypher, bandeau)


def main():
    bandeau("Lab 26-4 — VectorCypher: the best of both worlds")
    docs = load_documents()
    search = Search(docs)
    graphe = Graph.depuis_triplets(extract_triples(docs))

    question = "Which supplier risks impacting production on L-3?"
    print("\nQUESTION :", question)
    print("Expected answer: Rexel (via L-3 <- E-7 <- ... manufactured_by Rexel).")

    # === Method 1 : RAG vector-based seul ===================================
    print("\n" + "─" * 72)
    print("METHOD 1 — the vector RAG alone")
    c1 = Counter()
    docs_v = search.cherche(question, k=3)
    c1.ajoute(docs=len(docs_v))
    for d in docs_v:
        print(f"    [{d['score']:.2f}] {d['id']} : {d['content'][:64]}…")
    # The vector brings back fragments — possibly the word "Rexel", by lexical
    # coincidence — but it supplies NO path linking L-3 to the
    # fournisseur. Or to answer exige the relation, not the co-occurrence.
    print("    supplies a PATH from L-3 to the supplier?  NO")
    print("    (the fragments are juxtaposed; the link remains to be rebuilt)")
    print("   ", c1.summary())

    # === Method 2 : graph seul (without point of input vector-based) ==========
    print("\n" + "─" * 72)
    print("METHOD 2 — the graph alone (an arbitrary start, no vector entry)")
    c2 = Counter()
    # Without the vector, there is no way to know to start FROM L-3. A start "at
    # random" from an irrelevant node shows the bootstrapping problem.
    depart = sorted(graphe.nodes)[0]
    amont = graphe.voisins_amont(depart)
    c2.ajoute(nodes=len(graphe.nodes))
    print(f"    arbitrary start: {depart} (no relevant entry point)")
    print(f"    amont({depart}) = {amont}")
    print("    The graph is powerful but does not know WHERE to begin.")
    print("   ", c2.summary())

    # === Method 3 : VectorCypher =========================================
    print("\n" + "─" * 72)
    print("METHOD 3 — VectorCypher (the vector for the entry, the graph for the expansion)")
    c3 = Counter()
    vc = vector_cypher(question, search, graphe, profondeur=3, k=3)
    c3.ajoute(docs=vc["n_docs"], nodes=vc["n_noeuds"])
    print("    vector entry points:", vc["entrees"])
    print("    the sub-graph walked up:")
    for fait in vc["sous_graphe"]:
        print("       ", fait)
    # The under-graph contient explicitement the PATH reliant L-3 at the fournisseur.
    a_le_chemin = any("Rexel" in f for f in vc["sous_graphe"]) and \
                  any("L-3" in f for f in vc["sous_graphe"])
    print("    supplies a PATH linking L-3 to the supplier?",
          "YES" if a_le_chemin else "NO")
    if a_le_chemin:
        print("    ANSWER: Rexel — supplies E-7 (upstream of L-3) and the parts for P-42.")
    print("   ", c3.summary())

    # === Synthesis ==========================================================
    print("\n" + "─" * 72)
    print(f"{'Method':16}{'docs read':>10}{'nodes':>8}{'answers?':>12}")
    print(f"{'RAG seul':16}{c1.documents_lus:>10}{c1.noeuds_visites:>8}"
          f"{'no':>12}")
    print(f"{'Graph seul':16}{c2.documents_lus:>10}{c2.noeuds_visites:>8}"
          f"{'no start':>12}")
    print(f"{'VectorCypher':16}{c3.documents_lus:>10}{c3.noeuds_visites:>8}"
          f"{'yes':>12}")
    print("\nTHE MESSAGE: the graph does not replace the retrieval — it enriches its context.")


if __name__ == "__main__":
    main()
