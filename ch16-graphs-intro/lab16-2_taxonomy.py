# -*- coding: utf-8 -*-
"""
Lab 16-2 — Building your first taxonomy (Sophie)

Learning objective
------------------
Before the graph, a simpler structure that you already know without knowing it:
the TAXONOMY. A tree of categories, from the general to the particular, like the
shelves of a library or the classification of living things.

    A taxonomy ORGANISES.
    A graph LINKS.

This lab builds a taxonomy in pure Python — plain nested dictionaries — displays
it, and lets you search it by category. You see what a taxonomy can do, situate a
document within an organisation of knowledge, and, by its absence, what it CANNOT
do: it expresses only ONE relation, "belongs to" / "is a kind of". The real
dependencies — supersedes, depends on, supplies — escape it. That lack is what
will call for the graph in Lab 16-3.

No API key, no external dependency.
"""

from __future__ import annotations

from typing import Dict, List


# ---------------------------------------------------------------------------
# The taxonomy, as a tree of nested dictionaries.
# The leaves (lists) are the documents; the nodes (dicts) are the categories.
# ---------------------------------------------------------------------------
TAXONOMY: Dict = {
    "Safety": {
        "Electrical": ["BS 7671 wiring regulations", "Electrical lockout"],
        "Machinery": ["Machinery Directive", "Guarding of moving parts"],
    },
    "Environment": {
        "Water": ["Aqueous discharge order"],
        "Waste": ["Sorting of industrial waste"],
    },
    "Quality": {
        "Food industry": ["HACCP", "Batch traceability"],
    },
}


def show_tree(tree: Dict, depth: int = 0) -> None:
    """Print the taxonomy with indentation: a textual visualisation."""
    indent = "    " * depth
    for key, value in tree.items():
        if isinstance(value, dict):
            print(f"{indent}{key}")
            show_tree(value, depth + 1)
        else:  # a leaf: a list of documents
            print(f"{indent}{key}")
            for doc in value:
                print(f"{indent}    - {doc}")


def full_path(tree: Dict, prefix: str = "") -> List[str]:
    """Return every path: theme -> sub-theme -> document."""
    paths: List[str] = []
    for key, value in tree.items():
        here = f"{prefix} -> {key}" if prefix else key
        if isinstance(value, dict):
            paths.extend(full_path(value, here))
        else:
            for doc in value:
                paths.append(f"{here} -> {doc}")
    return paths


def documents_under(tree: Dict, category: str) -> List[str]:
    """Search by category: every document beneath `category`.

    This is the one "query" a taxonomy can honour natively: walk down a branch
    and collect its leaves.
    """
    def collect(node) -> List[str]:
        docs: List[str] = []
        if isinstance(node, dict):
            for v in node.values():
                docs.extend(collect(v))
        else:
            docs.extend(node)
        return docs

    def find(node, target: str):
        if isinstance(node, dict):
            for key, value in node.items():
                if key == target:
                    return value
                found = find(value, target)
                if found is not None:
                    return found
        return None

    subtree = find(tree, category)
    return collect(subtree) if subtree is not None else []


def main() -> None:
    print("#" * 78)
    print("# Lab 16-2 — Building your first taxonomy (Sophie)")
    print("#" * 78)

    print("\n" + "=" * 78)
    print("STEP 1 — The tree of categories")
    print("=" * 78)
    show_tree(TAXONOMY)

    print("\n" + "=" * 78)
    print("STEP 2 — Every document has a place: a path from general to particular")
    print("=" * 78)
    for path in full_path(TAXONOMY):
        print(f"  {path}")

    print("\n" + "=" * 78)
    print("STEP 3 — Searching by category")
    print("=" * 78)
    for category in ("Electrical", "Safety", "Food industry"):
        docs = documents_under(TAXONOMY, category)
        print(f"\n  \"Show me every document under {category}\"")
        for doc in docs:
            print(f"    - {doc}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- A taxonomy SITUATES a document: it says WHAT it comes under.")
    print("- It expresses only ONE relation: \"belongs to\" / \"is a kind of\".")
    print("- It says NOTHING about the links between documents: not \"supersedes\",")
    print("  not \"depends on\", not \"supplies\". Those crossing relations escape it.")
    print("\n  Try this: \"Which equipment depends on the supplier Mecafluid?\"")
    print("  The taxonomy CANNOT answer — this is not a question of filing, but of")
    print("  RELATION. That is the subject of Lab 16-3.")
    print("\nWHAT TO REMEMBER")
    print("  A taxonomy organises. A graph links.")


if __name__ == "__main__":
    main()
