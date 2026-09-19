# -*- coding: utf-8 -*-
"""
Lab 27-1 — "A relation is not always a pair"

A graph joins entities two by two. But some documents concern the same subject
without being linked pairwise. A hyperedge captures that.

Three procedures (cybersecurity, maintenance, process safety) take part in the
theme "business continuity" without sharing a single entity. A flat graph either
sees nothing or invents artificial edges; the hypergraph gathers them into one
hyperedge.

On a thematic query, only the hypergraph answers correctly.

No API key. Run generate_corpus.py first.
"""

from itertools import combinations

from multikit import (Hypergraph, load_procedures, bandeau)


def main():
    bandeau("Lab 27-1 — Where the flat graph fails: the thematic blind spot")
    procs, themes_gt = load_procedures()
    par_id = {p["id"]: p for p in procs}

    # === Representation 1 : graph plat (edges binaires) =================
    # On relie deux procedures si elles partagent a entity. Or the procedures
    # of a same theme NOT partagent NOT of entities -> aucune edge not the relie.
    aretes = []
    for a, b in combinations(procs, 2):
        communes = set(a["entities"]) & set(b["entities"])
        if communes:
            aretes.append((a["id"], b["id"], communes))
    print("\nTHE FLAT GRAPH (an edge means shared entities):")
    if aretes:
        for a, b, c in aretes:
            print(f"   {a} —— {b}  (via {c})")
    else:
        print("   NO edge: the procedures share no entity two by two.")
    print("   -> The flat graph cannot group by theme: the theme does not exist")
    print("     not as an object, only as an absent co-occurrence.")

    # === Representation 2 : hypergraph thematic =======================
    hg = Hypergraph()
    for theme, membres in themes_gt.items():
        hg.add(theme, membres)
    print("\nTHE HYPERGRAPH (a hyperedge means a theme):")
    for theme, membres in hg.hyperaretes.items():
        titres = [par_id[m]["title"] for m in membres]
        print(f"   ⬡ {theme} → {membres}")
        for t in titres:
            print(f"        · {t}")

    # === The deux queries ===============================================
    print("\n" + "─" * 74)
    print("A RELATIONAL QUERY: \"Do P-SEC-002 and P-SUR-002 share a theme?\"")
    rel = "Regulatory compliance"
    print("   flat graph: no direct edge -> cannot conclude")
    print(f"   hypergraph: {rel} → {hg.documents_du_theme(rel)} ✅")

    print("\nA THEMATIC QUERY: \"Which procedures participate in business continuity?\"")
    theme = "Business continuity"
    membres = hg.documents_du_theme(theme)
    print("   flat graph: no edge expresses this theme -> failure")
    print(f"   hypergraph: {theme} → {membres} ✅")
    couverture = len(set(membres) & set(themes_gt[theme])) / len(themes_gt[theme])
    print(f"   coverage against the ground truth: {couverture:.0%}")

    print("\n" + "─" * 74)
    print("THE MESSAGE: a graph represents RELATIONS between entities;")
    print("             a hypergraph represents CONCEPTS that group entities.")


if __name__ == "__main__":
    main()
