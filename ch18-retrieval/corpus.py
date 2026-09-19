# -*- coding: utf-8 -*-
"""
corpus.py — the shared loading of the corpus and queries of Chapter 18.

Every lab reads the same data the same way: the documents on one side, the
labelled queries on the other.

Run generate_corpus.py first.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

BASE = Path(__file__).resolve().parent / "corpus"


def corpus_ready() -> bool:
    return (BASE / "documents.tsv").exists() and (BASE / "queries.tsv").exists()


def _read_tsv(path: Path) -> List[Tuple[str, ...]]:
    lignes = []
    for ligne in path.read_text(encoding="utf-8").splitlines():
        if not ligne.strip() or ligne.startswith("#"):
            continue
        lignes.append(tuple(ligne.split("\t")))
    return lignes


def load_documents() -> Tuple[List[str], List[str]]:
    """Returns (ids, textes) in the ordre of the file."""
    ids, textes = [], []
    for ident, texte in _read_tsv(BASE / "documents.tsv"):
        ids.append(ident)
        textes.append(texte)
    return ids, textes


def load_queries() -> List[Tuple[str, str, str]]:
    """Renvoie [(query, id_pertinent, type), ...]."""
    return [(r, i, t) for r, i, t in _read_tsv(BASE / "queries.tsv")]
