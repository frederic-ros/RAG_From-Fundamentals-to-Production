# -*- coding: utf-8 -*-
"""
corpus.py — the shared loading of the corpus and the graph of Chapter 16.

A small utility module, so that every lab reads the same data the same way: the
text documents on one side, the graph of triples on the other. Its very structure
recalls the duality of the chapter:

    load_documents() -> what a SIMILARITY search sees
    load_graph()     -> what a KNOWLEDGE GRAPH sees

Run generate_corpus.py first.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

from graph import Graph

BASE = Path(__file__).resolve().parent / "corpus"
DOCS = BASE / "documents"


def corpus_ready() -> bool:
    """True if the corpus has been generated."""
    return DOCS.exists() and (BASE / "triples.tsv").exists()


def load_documents() -> Dict[str, str]:
    """Return {file_name: content} for every text document."""
    docs: Dict[str, str] = {}
    for f in sorted(DOCS.glob("*.txt")):
        docs[f.name] = f.read_text(encoding="utf-8")
    return docs


def _read_tsv(path: Path) -> List[Tuple[str, ...]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        rows.append(tuple(line.split("\t")))
    return rows


def load_types() -> Dict[str, str]:
    """Return {node: type} from corpus/types.tsv."""
    types: Dict[str, str] = {}
    path = BASE / "types.tsv"
    if path.exists():
        for node, type_ in _read_tsv(path):
            types[node] = type_
    return types


def load_graph() -> Graph:
    """Build the Graph from the triples, and apply the node types."""
    g = Graph()
    types = load_types()
    for node, type_ in types.items():
        g.add_node(node, type_)
    for subject, relation, obj in _read_tsv(BASE / "triples.tsv"):
        g.add_relation(subject, relation, obj)
    # Reapply the types, in case a node appeared only in the triples.
    for node, type_ in types.items():
        g.types[node] = type_
    return g
