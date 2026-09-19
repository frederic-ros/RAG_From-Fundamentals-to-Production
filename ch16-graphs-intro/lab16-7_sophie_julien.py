# -*- coding: utf-8 -*-
"""
Lab 16-7 — Sophie against Julien: organise or link? (the synthesis)

Learning objective
------------------
Compare two business needs, in order to choose the right structure of
representation:

  - SOPHIE (regulatory): "File the standards by domain."
    -> a need for ORGANISATION. A taxonomy is enough.

  - JULIEN (maintenance): "Find every piece of equipment impacted by the failure
    of one component."
    -> a need for RELATION. The graph is indispensable.

    Not all knowledge calls for the same structure.
    A taxonomy files; a graph links.

This lab replays both situations in miniature, on the structures built in the
earlier labs, and justifies the choice in each case. It closes the progression of
the chapter: recognising, faced with a need, whether it belongs to the tree or to
the network.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import corpus

# A small regulatory taxonomy, condensed from Lab 16-2.
SOPHIE_TAXONOMY = {
    "Safety": {"Electrical": ["BS 7671 wiring regulations"],
               "Machinery": ["Machinery Directive"]},
    "Environment": {"Water": ["Aqueous discharge order"]},
}

DEPENDENCIES = {"uses", "depends on", "powered by", "supplied by"}


def sophie_case() -> None:
    print("=" * 78)
    print("SOPHIE\'S CASE — \"File the standards by domain\"")
    print("=" * 78)
    print("The need: ORGANISE. One relation is enough: \"belongs to\".\n")
    for domain, sub in SOPHIE_TAXONOMY.items():
        print(f"  {domain}")
        for subdomain, docs in sub.items():
            print(f"      {subdomain}")
            for d in docs:
                print(f"          - {d}")
    print("\n  Verdict: TAXONOMY. The hierarchy answers the need in full.")
    print("  A graph here would be pure expense: no crossing relation is in play.")


def julien_case(g) -> None:
    print("\n" + "=" * 78)
    print("JULIEN\'S CASE — \"Which equipment is impacted if Mecafluid stops?\"")
    print("=" * 78)
    print("The need: LINK. Multiple, varied relations, to be chained.\n")
    impacted = g.impacted_by("Mecafluid", relations=DEPENDENCIES)
    for node, depth in impacted:
        print(f"    {'   ' * (depth - 1)}\\_ {node} ({g.types.get(node,'?')}, hop {depth})")
    print("\n  Verdict: GRAPH. A taxonomy COULD NOT answer this:")
    print("  a dependency is not a filing question, it is a link to be traversed.")


def decision_table() -> None:
    print("\n" + "=" * 78)
    print("THE DECISION RULE")
    print("=" * 78)
    rows = [
        ("The need...", "Taxonomy", "Graph"),
        ("files from general to particular", "YES", "-"),
        ("has one relation only (belongs to)", "YES", "-"),
        ("follows dependencies or successions", "-", "YES"),
        ("chains several facts (multi-hop)", "-", "YES"),
        ("mixes varied, named relations", "-", "YES"),
    ]
    for need, taxo, graph in rows:
        print(f"  {need:<40} {taxo:^10} {graph:^8}")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    g = corpus.load_graph()

    print("#" * 78)
    print("# Lab 16-7 — Sophie against Julien: organise or link?")
    print("#" * 78 + "\n")

    sophie_case()
    julien_case(g)
    decision_table()

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The right tool depends on the NATURE of the relations in play, not on fashion.")
    print("- One relation only, \"is a kind of\" -> a taxonomy.")
    print("- Varied relations to be chained -> a graph.")
    print("- And often the two live together: the graph TYPES its nodes via a taxonomy.")
    print("\nWHAT TO REMEMBER")
    print("  There is no universal structure: a taxonomy organises, a graph links.")
    print("  Choosing means reading the nature of the need.")


if __name__ == "__main__":
    main()
