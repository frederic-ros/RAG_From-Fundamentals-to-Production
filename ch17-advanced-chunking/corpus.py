# -*- coding: utf-8 -*-
"""
corpus.py — shared loading of the Chapter 17 corpus.

Run this first: python generate_corpus.py
"""

from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent / "corpus"


def corpus_ready() -> bool:
    return (BASE / "motor_M18_manual.md").exists()


def load(name: str) -> str:
    """Return the content of a corpus document, by file name."""
    return (BASE / name).read_text(encoding="utf-8")
