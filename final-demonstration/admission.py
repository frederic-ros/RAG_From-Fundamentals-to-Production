# -*- coding: utf-8 -*-
"""
admission.py — the "ready document" gate of the final demonstration.

Before a document enters the index, a mature pipeline asks a question the naive
system never touches: is this document even ADMISSIBLE?

Each document is scored here from 0 to 100 on four objective criteria, and its
fate is then decided. This is the notion of a "ready document" made concrete:
the quality of a retrieval system is settled as much at the intake as at the
search.

The criteria, 25 points each:
  - readability : is the content usable (against an unrecognised scan, an empty
                  file)?
  - integrity   : is the document signed, from a controlled origin (against a
                  forgery, or the web)?
  - freshness   : is it in force (against repealed or expired)?
  - uniqueness  : is it not a duplicate of a more authoritative document?

The decision follows the score plus some hard rules:
  - REJECTED   : unreadable, empty or poisoned -> never enters the index.
  - SUPERSEDED : a duplicate of a more recent or authoritative document.
  - DEGRADED   : admitted but bronze or unsigned -> indexed with a flag, never
                 prioritised, never served alone on a sensitive subject.
  - ADMITTED   : sound, up to date, signed -> fully indexed.

Deterministic, with no API key. Used by every tier from 1b onwards.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
import unicodedata


@dataclass
class AdmissionSheet:
    doc_id: str
    title: str
    score_value: int                 # 0-100
    readability: int           # 0-25
    integrity: int            # 0-25
    freshness: int            # 0-25
    uniqueness: int              # 0-25
    decision: str             # ADMITTED | DEGRADED | SUPERSEDED | REJECTED
    reason: str


# ---------------------------------------------------------------------------
# Readability measures: the proportion of "normal" characters — letters,
# digits, ordinary punctuation, spaces. An unrecognised scan collapses here.
# ---------------------------------------------------------------------------
_PUNCT_OK = set(" .,;:!?'\"()-/%\n\t°")

import re as _re
# A "plausible word": at least three basic Latin letters in a row.
_PLAUSIBLE_WORD = _re.compile(r"[A-Za-zàâäéèêëîïôöùûüçœæ]{3,}")


def _readable_ratio(text: str) -> float:
    """The proportion of "normal" characters. An unrecognised scan collapses."""
    if not text.strip():
        return 0.0
    ok = 0
    for ch in text:
        if ch.isalnum() or ch in _PUNCT_OK:
            ok += 1
        else:
            cat = unicodedata.category(ch)
            if cat.startswith("L") or cat.startswith("M"):
                ok += 1
    return ok / len(text)


def _real_word_ratio(text: str) -> float:
    """Proportion of tokens that resemble real words. This is the most reliable
    signal of failed OCR: almost no plausible word, even when the
    isolated characters pass. Normal text exceeds 0.5; a noise scan falls near
    zero."""
    jetons = text.split()
    if not jetons:
        return 0.0
    reels = sum(1 for j in jetons if _PLAUSIBLE_WORD.search(j))
    return reels / len(jetons)


def _document_text(doc: dict) -> str:
    return " ".join(b.get("text", "") for b in doc["blocks"])


# ---------------------------------------------------------------------------
# Scoring a document.
# ---------------------------------------------------------------------------
def score_document(doc: dict, all_docs: List[dict]) -> AdmissionSheet:
    text = _document_text(doc)
    ratio = _readable_ratio(text)
    word_ratio = _real_word_ratio(text)
    n_words = len(text.split())

    # --- readability (0-25) ---
    # An unrecognised scan keeps isolated "normal" characters but has almost no
    # plausible word: that second signal is what unmasks it.
    if n_words < 3 or ratio < 0.55 or word_ratio < 0.30:
        readable_pts = 0
    elif ratio < 0.80 or word_ratio < 0.60:
        readable_pts = 12
    else:
        readable_pts = 25

    # --- integrity / provenance (0-25) ---
    signed = doc.get("signed", False)
    external = doc.get("origin", "internal") == "external"
    if doc.get("poisoned", False):
        integrity_pts = 0
    elif external and not signed:
        integrity_pts = 5
    elif signed and doc.get("authority") == "gold":
        integrity_pts = 25
    elif signed:
        integrity_pts = 18
    else:
        integrity_pts = 8

    # --- freshness (0-25) ---
    status = doc.get("status", "in force")
    freshness_pts = 25 if status == "in force" else 0

    # --- uniqueness (0-25): a duplicate of a more recent document on the same subject? ---
    uniqueness_pts = 25
    duplicate_of = None
    for other in all_docs:
        if other["id"] == doc["id"]:
            continue
        if _same_subject(doc, other) and _more_authoritative(other, doc):
            uniqueness_pts = 0
            duplicate_of = other["title"]
            break

    score_value = readable_pts + integrity_pts + freshness_pts + uniqueness_pts

    # --- the decision (hard rules first) ---
    if doc.get("poisoned", False):
        decision, reason = "REJECTED", "poisoned content / injected instruction"
    elif readable_pts == 0:
        decision, reason = "REJECTED", "unreadable or empty (not usable)"
    elif duplicate_of is not None:
        decision, reason = "SUPERSEDED", f"duplicate superseded by \"{duplicate_of}\""
    elif status != "in force":
        decision, reason = "SUPERSEDED", "repealed version, replaced by the edition in force"
    elif score_value < 70 or not signed or doc.get("authority") == "bronze":
        decision, reason = "DEGRADED", "admitted with reservation (never prioritised)"
    else:
        decision, reason = "ADMITTED", "sound document, up to date, signed"

    return AdmissionSheet(doc["id"], doc["title"], score_value, readable_pts, integrity_pts, freshness_pts,
                          uniqueness_pts, decision, reason)


def _same_subject(a: dict, b: dict) -> bool:
    """A simple heuristic: the same identifier stem, once the known version
    suffixes (-old, -2021, -2024) are stripped, so hr-remote-work-old maps to
    hr-remote-work. It does not claim to generalise to every ID scheme: in a
    real pipeline, duplicate detection would rest on content similarity, not on
    a naming convention."""
    base_a = a["id"].replace("-old", "").replace("-2021", "").replace("-2024", "")
    base_b = b["id"].replace("-old", "").replace("-2021", "").replace("-2024", "")
    return base_a == base_b and a["id"] != b["id"]


def _more_authoritative(a: dict, b: dict) -> bool:
    """Is a preferable to b? In force beats repealed; then the more recent date."""
    sa = a.get("status") == "in force"
    sb = b.get("status") == "in force"
    if sa != sb:
        return sa
    return a.get("date", "") > b.get("date", "")


# ---------------------------------------------------------------------------
# Applying the gate to the whole corpus.
# ---------------------------------------------------------------------------
def pass_the_gate(documents: List[dict]) -> Dict[str, AdmissionSheet]:
    return {d["id"]: score_document(d, documents) for d in documents}


def admitted_blocks(documents: List[dict]) -> List[dict]:
    """Return the blocks of the documents that were neither rejected nor
    superseded, with a `degraded` flag propagated into the metadata for the
    tiers that follow."""
    sheets = pass_the_gate(documents)
    out = []
    for d in documents:
        f = sheets[d["id"]]
        if f.decision in ("REJECTED", "SUPERSEDED"):
            continue
        degraded = (f.decision == "DEGRADED")
        for b in d["blocks"]:
            if b.get("type") == "empty":
                continue
            bb = dict(b)
            bb["metadata"] = {**b["metadata"], "degraded": degraded,
                              "ready_score": f.score_value}
            out.append(bb)
    return out


if __name__ == "__main__":
    import json
    from pathlib import Path
    path = Path(__file__).parent / "corpus" / "canonical.json"
    if not path.exists():
        raise SystemExit(
            "Corpus not found. Run this first: python generate_corpus.py"
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    sheets = pass_the_gate(data["documents"])
    print(f"{'Document':40} {'Score':>5}  Decision    Reason")
    print("-" * 100)
    for f in sheets.values():
        print(f"{f.title[:40]:40} {f.score_value:>4}  {f.decision:9}  {f.reason}")
