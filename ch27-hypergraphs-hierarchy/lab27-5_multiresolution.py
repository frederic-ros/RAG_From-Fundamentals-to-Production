# -*- coding: utf-8 -*-
"""
Lab 27-5 — Designing a multi-resolution engine
"Which level for which question?" (the synthesis lab)

The aim: integrate the four representations of the chapter (vector, graph,
hypergraph, hierarchy) behind a single router, then evaluate that router over the
50 annotated questions of the corpus.

This is the chapter's thesis made runnable: we no longer look for THE right
structure, we route towards the right LEVEL of granularity. The router turns a
set of specialists into a coherent team.

THIS IS THE VERIFICATION LAB FOR THE ROUTER WORD LISTS in multikit. If a list
stops matching the questions, its column collapses into "vector", the default,
with no error raised. The French baseline is 41/50, and the confusion matrix
shows where the remaining errors sit.

No API key. Run generate_corpus.py first.
"""

from collections import defaultdict

from multikit import (Search, Hypergraph, DocTree, HierarchicalIndex,
                      GraphTree, Counter, load_procedures,
                      load_inspections, load_turbine_md, load_questions,
                      load_cost, routeur_multiresolution, cout_de, bandeau)


def main():
    bandeau("Lab 27-5 — The multi-resolution engine: the router")
    procs, themes_gt = load_procedures()
    rapports = load_inspections()
    arbre = DocTree(load_turbine_md())
    questions = load_questions()
    cout = load_cost()

    # --- prepare the four engines --------------------------------------------
    # NOTE: the four engines are built here to show that they
    # really do coexist (the same data as Labs 27-1 to 27-4). But THIS lab
    # measures ONLY the routing accuracy — the label chosen against the label
    # expected. It does not query those engines question by question; see Labs
    # 27-1 to 27-4 for each engine actually running.
    engines = {"vector": Search(procs + rapports)}
    hypergraphe = Hypergraph()
    for theme, membres in themes_gt.items():
        hypergraphe.add(theme, membres)
    engines["hypergraph"] = hypergraphe
    engines["hierarchy"] = HierarchicalIndex.depuis_arbre(arbre)
    engines["graph"] = GraphTree(arbre)
    print(f"\n{len(engines)} engines available. {len(questions)} questions to route "
          f"(accuracy of the ROUTING, not of the retrieval).\n")

    # --- to route and to evaluate -----------------------------------------------
    bons = 0
    confusion: dict[tuple[str, str], int] = defaultdict(int)
    cout_par_moteur: dict[str, Counter] = defaultdict(Counter)
    compte: dict[str, int] = defaultdict(int)

    print(f"{'#':>3}  {'expected':12} {'routed to':12} {'ok':>3}  question")
    print("─" * 92)
    for i, item in enumerate(questions, 1):
        q, attendu = item["q"], item["engine"]
        choisi = routeur_multiresolution(q)
        ok = (choisi == attendu)
        bons += int(ok)
        confusion[(attendu, choisi)] += 1
        compte[choisi] += 1

        c, lat = cout_de(choisi, cout)
        cout_par_moteur[choisi].ajoute(cout=c, latence=lat)

        if i <= 12 or not ok:   # show the start plus every error
            print(f"{i:>3}  {attendu:12} {choisi:12} {'OK' if ok else '!!':>3}  {q[:46]}")
    print("   …")

    # --- bilan -----------------------------------------------------------
    n = len(questions)
    print("─" * 92)
    print(f"\nRouting accuracy: {bons}/{n} = {bons / n:.0%}")

    print("\nConfusion matrix (rows = expected, columns = routed):")
    moteurs = ["vector", "graph", "hypergraph", "hierarchy", "mixed"]
    entete = "            " + "".join(f"{m[:6]:>9}" for m in moteurs)
    print(entete)
    for attendu in moteurs:
        ligne = f"  {attendu:10}"
        for choisi in moteurs:
            ligne += f"{confusion.get((attendu, choisi), 0):>9}"
        print(ligne)

    print("\nCost and latency per engine:")
    print(f"  {'engine':14}{'#':>4}{'total cost':>12}{'total latency':>15}")
    for m in moteurs:
        c = cout_par_moteur[m]
        print(f"  {m:14}{compte[m]:>4}{c.cout:>11.1f}{c.latence_ms:>12.0f}ms")

    print("\nTHE MESSAGE: the problem is not only WHAT to search for, it is HOW.")
    print("             The router turns specialists into a coherent team.")


if __name__ == "__main__":
    main()
