# -*- coding: utf-8 -*-
"""
Lab 26-5 — "Which engine for which question?" (the synthesis lab)

Build a router that chooses between the four strategies, and evaluate it over the
25 annotated questions of the corpus.

This is the chapter's thesis made runnable: real GraphRAG is not "a graph", it is
a system able to choose the right engine according to the NATURE of the question.
The graph HARMS simple factual questions; the router avoids that overhead where
it serves nothing.

For each question the lab prints the strategy the router chose against the
expected type, then the routing accuracy and the aggregated cost per strategy.

THIS IS THE VERIFICATION LAB FOR THE ROUTER WORD LISTS in graphkit. If a list
stops matching the questions, the accuracy drops here with no error raised. The
French baseline is 22/25.

No API key. Run generate_corpus.py first.
"""

from collections import defaultdict

from graphkit import (Search, Graph, Counter, load_documents,
                      load_questions, extract_triples, routeur_complexite,
                      local_search, global_search, vector_cypher,
                      bandeau, _entites_presentes)


# The mapping from expected question type to ideal strategy. The router is
# "correct" when its strategy is consistent with that type.
TYPE_VERS_STRATEGIE = {
    "factual": {"vectoriel"},
    "relational": {"local", "vectorcypher"},
    "supplier": {"vectorcypher"},
    "aggregation": {"global"},
}


def repondre(question: str, strategie: str, search: Search,
             graphe: Graph) -> tuple[str, Counter]:
    """Apply the chosen strategy and return (short_context, cost)."""
    c = Counter()
    if strategie == "vectoriel":
        docs = search.cherche(question, k=2)
        c.ajoute(docs=len(docs))
        return (docs[0]["content"][:60] if docs else ""), c
    if strategie == "global":
        g = global_search(graphe)
        c.ajoute(nodes=g["n_noeuds"])
        pivot = g["communautes"][0]["pivot"] if g["communautes"] else "?"
        return f"communities; pivot={pivot}", c
    if strategie == "local":
        docs = search.cherche(question, k=1)
        ent = _entites_presentes(docs[0]["content"]) if docs else []
        loc = local_search(graphe, ent[:1] or ["P-42"], profondeur=2)
        c.ajoute(docs=1, nodes=loc["n_noeuds"])
        return f"voisinage={loc['nodes'][:5]}", c
    # vectorcypher
    vc = vector_cypher(question, search, graphe, profondeur=3, k=2)
    c.ajoute(docs=vc["n_docs"], nodes=vc["n_noeuds"])
    return f"sous-graphe={vc['sous_graphe'][:3]}", c


def main():
    bandeau("Lab 26-5 — Hybrid GraphRAG: an intelligent router (the synthesis)")
    docs = load_documents()
    questions = load_questions()
    search = Search(docs)
    graphe = Graph.depuis_triplets(extract_triples(docs))
    print(f"\n{len(questions)} questions, a graph of {len(graphe.nodes)} nodes.\n")

    bons = 0
    cout_par_strategie: dict[str, Counter] = defaultdict(Counter)
    compte_strategie: dict[str, int] = defaultdict(int)

    print(f"{'#':>3}  {'expected':13} {'routed to':13} {'ok':>3}  question")
    print("─" * 88)
    for i, item in enumerate(questions, 1):
        q, type_attendu = item["q"], item["type"]
        strategie = routeur_complexite(q)
        ok = strategie in TYPE_VERS_STRATEGIE.get(type_attendu, set())
        bons += int(ok)
        compte_strategie[strategie] += 1

        _, cout = repondre(q, strategie, search, graphe)
        agg = cout_par_strategie[strategie]
        agg.ajoute(docs=cout.documents_lus, nodes=cout.noeuds_visites,
                   recherches=cout.recherches_vectorielles)

        marque = "OK" if ok else "!!"
        print(f"{i:>3}  {type_attendu:13} {strategie:13} {marque:>3}  {q[:42]}")

    # --- Routing summary --------------------------------------------------
    n = len(questions)
    print("─" * 88)
    print(f"\nRouting accuracy: {bons}/{n} = {bons / n:.0%}")

    print("\nSplit and cost per strategy:")
    print(f"  {'strategy':14}{'#':>4}{'docs read':>10}{'nodes':>8}")
    for strat in ("vectoriel", "local", "global", "vectorcypher"):
        c = cout_par_strategie[strat]
        print(f"  {strat:14}{compte_strategie[strat]:>4}"
              f"{c.documents_lus:>10}{c.noeuds_visites:>8}")

    # --- The lesson in figures: the router spares the graph -------------------
    factuelles = sum(1 for it in questions if it["type"] == "factual")
    routees_vectoriel = compte_strategie["vectoriel"]
    print(f"\n{factuelles} factual questions in the corpus; "
          f"{routees_vectoriel} questions routed to the vector alone.")
    print("-> That many questions AVOID the overhead of the graph, which would")
    print("   degrade them: GraphRAG-Bench reports -13% on simple factual questions.")

    print("\nTHE MESSAGE: real GraphRAG is not \"a graph\". It is a system")
    print("             a hybrid that picks the right engine for the nature of the question.")


if __name__ == "__main__":
    main()
