# -*- coding: utf-8 -*-
"""
tree.py — document-tree utilities, shared by the labs of Chapter 14.

A document is not a pile of fragments: it is a TREE. This module loads the tree
JSON produced by generate_corpus.py and provides what the labs need:

  - the LEAVES (the small, precise child fragments that get indexed);
  - for each leaf, its hierarchical PATH (the breadcrumb);
  - for each leaf, its PARENT (the large context fragment that gets restored).

No dependency, no API key.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
import json


@dataclass
class Leaf:
    """A child fragment: the precise text plus its address in the tree.

    Two parents are distinguished:
      - parent_id / parent_title: the IMMEDIATE parent, the subsection that
        directly contains the paragraph;
      - context_id / context_title: the CONTEXT parent, the enclosing section,
        the one restored by parent-child retrieval so as to give the model the
        rule AND its exception together.
    """
    id: str
    text: str
    path: List[str]              # e.g. ["HR agreement", "Remote work", "General rule"]
    parent_id: str               # immediate parent
    parent_title: str
    context_id: str              # context parent (enclosing section)
    context_title: str

    @property
    def breadcrumb(self) -> str:
        return " > ".join(self.path)


@dataclass
class Parent:
    """A parent fragment: the complete context of a section."""
    id: str
    title: str
    path: List[str]
    text: str                    # concatenation of every descendant paragraph

    @property
    def breadcrumb(self) -> str:
        return " > ".join(self.path)


@dataclass
class Tree:
    root: dict
    leaves: List[Leaf] = field(default_factory=list)
    parents: dict = field(default_factory=dict)   # id -> Parent

    def parent_of(self, leaf: Leaf) -> Parent:
        """Immediate parent (subsection) of a leaf."""
        return self.parents[leaf.parent_id]

    def context_of(self, leaf: Leaf) -> Parent:
        """Context parent (enclosing section) — the one that gets restored."""
        return self.parents[leaf.context_id]


def load(json_path: Path) -> Tree:
    """Load a tree JSON and extract its leaves and parents."""
    root = json.loads(Path(json_path).read_text(encoding="utf-8"))
    tree = Tree(root=root)
    _walk(root, [], None, tree)
    return tree


def _descendant_text(node: dict) -> str:
    """Concatenate every paragraph of a node and of its descendants."""
    pieces: List[str] = list(node.get("paragraphs", []))
    for child in node.get("children", []):
        t = _descendant_text(child)
        if t:
            pieces.append(t)
    return " ".join(pieces).strip()


def _walk(node: dict, path: List[str], parent: Optional[dict],
          tree: Tree, section: Optional[dict] = None):
    current_path = path + [node["title"]]

    # Remember the enclosing SECTION: it is the context parent that parent-child
    # retrieval will restore. If the current node is a section, it becomes the
    # reference section for its descendants.
    if node.get("type") == "section":
        section = node
    section_ref = section if section is not None else node

    # Any node carrying paragraphs can serve as a PARENT (a context).
    tree.parents[node["id"]] = Parent(
        id=node["id"],
        title=node["title"],
        path=list(current_path),
        text=_descendant_text(node),
    )

    # The paragraphs of THIS node become leaves, attached both to their
    # immediate parent (the node itself) and to their context section.
    for i, para in enumerate(node.get("paragraphs", [])):
        tree.leaves.append(
            Leaf(
                id=f"{node['id']}-p{i}",
                text=para,
                path=list(current_path),
                parent_id=node["id"],
                parent_title=node["title"],
                context_id=section_ref["id"],
                context_title=section_ref["title"],
            )
        )

    for child in node.get("children", []):
        _walk(child, current_path, node, tree, section)


if __name__ == "__main__":
    demo = Path(__file__).resolve().parent / "corpus" / "remote_work_agreement.json"
    if demo.exists():
        t = load(demo)
        print(f"Leaves: {len(t.leaves)}")
        for leaf in t.leaves:
            print(f"  - {leaf.breadcrumb}")
            print(f"      immediate parent : {leaf.parent_title}")
            print(f"      restored context : {t.context_of(leaf).title}")
    else:
        print("Run this first: python generate_corpus.py")
