# -*- coding: utf-8 -*-
"""
corpus.py — loading the Chapter 15 corpus, shared by the labs.

Exposes a small Document structure (text plus metadata) and a filtering helper,
so that the labs can concentrate on the lesson rather than on the plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Callable
import json

CORPUS = Path(__file__).resolve().parent / "corpus"
DOCS = CORPUS / "documents.json"


@dataclass
class Document:
    id: str
    text: str
    metadata: dict

    def meta(self, key: str, default=None):
        return self.metadata.get(key, default)


def load() -> List[Document]:
    if not DOCS.exists():
        raise FileNotFoundError(
            "Corpus not found. Run this first: python generate_corpus.py"
        )
    data = json.loads(DOCS.read_text(encoding="utf-8"))
    return [Document(d["id"], d["text"], d["metadata"]) for d in data["documents"]]


def filter_docs(docs: List[Document], predicate: Callable[[Document], bool]) -> List[Document]:
    """Return the documents satisfying the predicate. A filter is an exclusion."""
    return [d for d in docs if predicate(d)]


if __name__ == "__main__":
    docs = load()
    print(f"{len(docs)} documents loaded:")
    for d in docs:
        print(f"  - {d.id:30} status={d.meta('status'):12} source={d.meta('source')}")
