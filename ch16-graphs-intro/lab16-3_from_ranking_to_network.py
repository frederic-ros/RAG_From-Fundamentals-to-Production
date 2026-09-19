# -*- coding: utf-8 -*-
"""
Lab 16-3 — From filing to network: when a taxonomy is no longer enough (Julien)

Learning objective
------------------
Start from the idea of a taxonomy (Lab 16-2), and then ADD crossing relations to
it, to model Julien's domain of industrial maintenance. What follows is the move
from the tree to the network: the GRAPH.

    Where a taxonomy has only one relation ("is a kind of"), a graph admits as
    many as the business actually has: depends on, supplies, supersedes,
    powers, uses.

This lab shows:

  1. the taxonomy alone (the TYPES of the nodes: Pump, Motor, Supplier...);
  2. the addition of crossing relations, the triples, which form the graph;
  3. a question the taxonomy CANNOT honour, but which the graph resolves by
     traversal: "Which equipment depends on Mecafluid?".

You can then see why the graph ENCOMPASSES the taxonomy: each node keeps a type
(taxonomy), and the named edges (graph) link those nodes to each other.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import corpus


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    g = corpus.load_graph()

    print("#" * 78)
    print("# Lab 16-3 — From filing to network (Julien)")
    print("#" * 78)

    # --- 1. The taxonomy: each entity has a TYPE ------------------------------
    print("\n" + "=" * 78)
    print("STEP 1 — The taxonomy: filing the entities by type")
    print("=" * 78)
    by_type: dict = {}
    for node in g.nodes():
        by_type.setdefault(g.types[node], []).append(node)
    for type_, nodes in sorted(by_type.items()):
        print(f"  {type_:<13}: {', '.join(nodes)}")
    print("\n  Useful for filing — but one relation only: \"is a kind of\".")
    print("  There is no way to read from it that a pump DEPENDS on a motor.")

    # --- 2. The graph: add the crossing relations -----------------------------
    print("\n" + "=" * 78)
    print("STEP 2 — The graph: linking the entities by named relations")
    print("=" * 78)
    print("The same entities, but joined by NAMED edges (triples):\n")
    # The succession relations are hidden here, to focus on the dependencies.
    physical = {"uses", "depends on", "powered by", "supplied by", "adjusts"}
    for subject, relation, obj in g.triples():
        if relation in physical:
            t_s = g.types.get(subject, "?")
            t_o = g.types.get(obj, "?")
            print(f"  {subject:<10}({t_s:<11}) --[{relation:<13}]--> {obj:<10}({t_o})")

    # --- 3. The question only the relation resolves ---------------------------
    print("\n" + "=" * 78)
    print("STEP 3 — The question the taxonomy cannot honour")
    print("=" * 78)
    question = "Which equipment depends, directly or not, on Mecafluid?"
    print(f"  \"{question}\"\n")

    print("  With a TAXONOMY: all you can do is list the \"Supplier\" entries and the")
    print("  \"Equipment\" entries separately. No link brings them together. Failure.\n")

    print("  With the GRAPH: the incoming relations are walked back from Mecafluid.")
    dep = {"uses", "depends on", "powered by", "supplied by"}
    impacted = g.impacted_by("Mecafluid", relations=dep)
    for node, depth in impacted:
        arrow = "  " * depth
        print(f"    {arrow}\\_ {node}  ({g.types.get(node,'?')}, {depth} hop(s) away)")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The graph appears as soon as the relations become MULTIPLE and VARIED.")
    print("- It ENCOMPASSES the taxonomy: each node keeps a type, the edges link them.")
    print("- A question of DEPENDENCY is not a question of FILING: it requires")
    print("  following links, not walking down a tree.")
    print("\nWHAT TO REMEMBER")
    print("  A taxonomy files the nodes; a graph links them. One fits inside the other.")


if __name__ == "__main__":
    main()
