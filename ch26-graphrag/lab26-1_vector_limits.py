# -*- coding: utf-8 -*-
"""
Lab 26-1 — "Why does my RAG not find the answer?"

The aim: show concretely that a vector RAG answers factual questions perfectly —
one hop, the answer inside a single document — but fails as soon as the question
requires FOLLOWING a chain of relations.

Two questions are put side by side, with the top-k of the vector retrieval shown
for each, and the observation that the complete chain appears in NO single
document. The graph, in the labs that follow, will rebuild it.

No API key. Run generate_corpus.py first.
"""

from graphkit import Search, Graph, load_documents, extract_triples, bandeau


def main():
    bandeau("Lab 26-1 — When the vector is no longer enough")
    docs = load_documents()
    search = Search(docs)

    print("\nCorpus :", len(docs), "documents.")
    print("No document holds the complete chain P-42 -> E-7 -> L-3 -> product X.\n")

    # --- Question 1 : factuelle (the vector suffit) ------------------------
    q1 = "What is the nominal pressure of P-42?"
    print("─" * 72)
    print("QUESTION FACTUELLE :", q1)
    top1 = search.cherche(q1, k=3)
    for d in top1:
        print(f"  [{d['score']:.2f}] {d['id']} : {d['content'][:70]}…")
    print("  -> The answer (3 bar) is INSIDE the top-ranked document. Success.")

    # --- Question 2 : relationnelle (the vector fails) -------------------
    q2 = "What does the line fed by P-42 manufacture?"
    print("─" * 72)
    print("QUESTION RELATIONNELLE :", q2)
    top2 = search.cherche(q2, k=3)
    for d in top2:
        print(f"  [{d['score']:.2f}] {d['id']} : {d['content'][:70]}…")
    # The vector refinds documents proches words, but aucun not relie
    # P-42 at the produit X : it faudrait suivre trois relations.
    contient_reponse = any("produit X" in d["content"] and "P-42" in d["content"]
                           for d in top2)
    print(f"  -> Does any single document hold both P-42 and 'product X'? "
          f"{'yes' if contient_reponse else 'NO'}")
    print("  -> The vector cannot FOLLOW P-42 -> E-7 -> L-3 -> product X.")

    # --- What the graph will be able to do (a preview) ------------------------
    print("─" * 72)
    print("A PREVIEW — what the graph will rebuild (Lab 26-2 onwards):")
    graphe = Graph.depuis_triplets(extract_triples(docs))
    path = graphe.path("P-42", "product X")
    if path:
        print("   path(P-42 → produit X) =", " → ".join(path))
        print("   The answer emerges from the TRAVERSAL, not from a single document.")
    else:
        print("   (path not found — check the extraction)")

    print("─" * 72)
    print("THE MESSAGE: embeddings find DOCUMENTS;")
    print("             graphs find RELATIONS.")


if __name__ == "__main__":
    main()
