# -*- coding: utf-8 -*-
"""
Lab 7-3 — Code your own automated AI-ready score "linter" (Sophie)

Learning objective
------------------
How do you spot a document that is hostile to machines? By automating the grid
of the chapter's five principles:

  1. Genuinely hierarchical headings
  2. Normalised tables (nothing flattened)
  3. Metadata present
  4. One document, one truth
  5. Acronyms spelled out

For each principle not respected, the linter raises an actionable alert. It
scores a document out of 5, and can be run across a whole corpus.

No external dependency, no API key.
Run generate_sample_docs.py first.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

DOCS = Path(__file__).resolve().parent / "sample_docs"

# Acronyms treated as "known", defined elsewhere in the organisation. Any other
# unexplained abbreviation in the text raises an alert.
COMMON_ACRONYMS = {"HR", "PDF", "CE", "ISO", "IT", "URL", "API"}

# The sign of a flattened table: a long run of numbers with no structure.
NUMBER_RUN = re.compile(r"(?:\b\d+(?:[.,]\d+)?\b[ ,;]*){4,}")

# An acronym: 2 or more consecutive capitals, possibly with digits.
ACRONYM_PATTERN = re.compile(r"\b[A-Z][A-Z0-9]{1,}\b")

# An acronym definition: a parenthesis right after an expression, "... (RAMS)".
DEFINED_PATTERN = re.compile(r"\(([A-Z][A-Z0-9]{1,})\)")


def full_text(pivot: Dict) -> str:
    parts = [pivot.get("title", "")]
    for s in pivot.get("sections", []):
        parts.append(s.get("title", ""))
        parts.append(s.get("content", ""))
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Criterion 1 — Genuinely hierarchical headings
# ---------------------------------------------------------------------------
def criterion_headings(pivot: Dict) -> Tuple[bool, str]:
    sections = pivot.get("sections", [])
    with_title = [s for s in sections if s.get("title", "").strip()]
    if len(sections) >= 2 and len(with_title) == len(sections):
        return True, ""
    if len(sections) <= 1:
        return False, "no hierarchy: the document is one undifferentiated block"
    return False, "some sections have no heading: the hierarchy is incomplete"


# ---------------------------------------------------------------------------
# Criterion 2 — Normalised tables (nothing flattened)
# ---------------------------------------------------------------------------
def criterion_tables(pivot: Dict) -> Tuple[bool, str]:
    for s in pivot.get("sections", []):
        content = s.get("content", "")
        m = NUMBER_RUN.search(content)
        if m:
            excerpt = m.group(0).strip()[:40]
            return False, f"a suspicious run of numbers (a flattened table?): \"{excerpt}…\""
    return True, ""


# ---------------------------------------------------------------------------
# Criterion 3 — Metadata present
# ---------------------------------------------------------------------------
def metadata_criterion(pivot: Dict) -> Tuple[bool, str]:
    meta = pivot.get("metadata", {})
    essential = {"date", "author", "version"}
    present = essential & set(meta)
    if present == essential:
        return True, ""
    missing = essential - present
    return False, f"metadata missing: {', '.join(sorted(missing))}"


# ---------------------------------------------------------------------------
# Criterion 4 — One document, one truth (no obvious contradiction)
# ---------------------------------------------------------------------------
def criterion_single_truth(pivot: Dict) -> Tuple[bool, str]:
    text = full_text(pivot)
    # The heuristic: a contradiction only exists when TWO different values of
    # "max pressure" appear WITHOUT a distinct model separating them. If the
    # same sentence sets two values against each other ("12.5 bar ... 14 bar
    # peak tolerated"), that is a contradiction. Two distinct models, MX-200 at
    # 12.5 and MX-201 at 16, are not.
    sentences = re.split(r"[.;]", text)
    for sentence in sentences:
        values = re.findall(r"max(?:imum)?\s+pressure\s*:?\s*(\d+(?:[.,]\d+)?)",
                            sentence, flags=re.IGNORECASE)
        if len(set(values)) > 1:
            return False, ("two contradictory truths for \"max pressure\" in the "
                           "same passage: " + ", ".join(sorted(set(values))) + " bar")
    # The "peak tolerated" case: a peak value exceeding the stated maximum.
    if re.search(r"peak tolerated", text, re.IGNORECASE):
        return False, "a \"peak tolerated\" value contradicting the stated max pressure"
    # Several service-note references open a risk of contradiction.
    refs = re.findall(r"\bNS-\d{4}-\d{2}\b", text)
    if len(set(refs)) > 1:
        return False, "several service notes cited: a risk of contradictory versions"
    return True, ""


# ---------------------------------------------------------------------------
# Criterion 5 — Acronyms spelled out
# ---------------------------------------------------------------------------
def criterion_acronyms(pivot: Dict) -> Tuple[bool, str]:
    text = full_text(pivot)
    defined = set(DEFINED_PATTERN.findall(text)) | COMMON_ACRONYMS
    # Model reference prefixes ("MX-200") are not acronyms.
    model_prefixes = set(re.findall(r"\b([A-Z]{2,})-\d", text))
    candidates = set(ACRONYM_PATTERN.findall(text))
    undefined = {
        a for a in candidates
        if a not in defined
        and a not in model_prefixes
        and not re.search(r"\d", a)
        and len(a) <= 6
    }
    if not undefined:
        return True, ""
    return False, "acronyms not spelled out: " + ", ".join(sorted(undefined))


CRITERIA = [
    ("Hierarchical headings", criterion_headings),
    ("Normalised tables", criterion_tables),
    ("Metadata present", metadata_criterion),
    ("One document, one truth", criterion_single_truth),
    ("Acronyms spelled out", criterion_acronyms),
]


def score_document(pivot: Dict) -> Tuple[int, List[str]]:
    """Return the score (0 to 5) and the list of alerts."""
    score = 0
    alerts: List[str] = []
    for name, function in CRITERIA:
        ok, message = function(pivot)
        if ok:
            score += 1
        else:
            alerts.append(f"{name}: {message}")
    return score, alerts


def verdict(score: int) -> str:
    if score == 5:
        return "An AI-ready document."
    if score >= 3:
        return "Improvable: there are easy gains still to take."
    return "Hostile to machines: rework it before indexing."


def audit(name: str, pivot: Dict) -> int:
    score, alerts = score_document(pivot)
    print(f"\n{'=' * 78}")
    print(f"DOCUMENT: {name}  —  title \"{pivot.get('title', '')[:50]}\"")
    print("=" * 78)
    print(f"AI-ready score: {score} / 5  ->  {verdict(score)}")
    if alerts:
        print("Alerts:")
        for a in alerts:
            print(f"  ! {a}")
    else:
        print("No alert: every principle is respected.")
    return score


def main() -> None:
    print("=" * 78)
    print("Lab 7-3 — An AI-ready score linter (Sophie)")
    print("=" * 78)

    if not (DOCS / "julien_hostile_sheet.json").exists():
        print("\nDocuments not found. Run this first: python generate_sample_docs.py")
        return

    # 1) Hostile against AI-ready: the same document, two versions.
    hostile = json.loads((DOCS / "julien_hostile_sheet.json").read_text(encoding="utf-8"))
    ai_ready = json.loads((DOCS / "julien_ai_ready_sheet.json").read_text(encoding="utf-8"))
    s_hostile = audit("julien_hostile_sheet", hostile)
    s_ready = audit("julien_ai_ready_sheet", ai_ready)

    # 2) Reuse a pivot from Chapter 6, if it is reachable.
    pivot_ch6 = Path(__file__).resolve().parents[1] / "ch06-ingestion" / "sample_docs" / "pivot_word.json"
    if pivot_ch6.exists():
        ch6 = json.loads(pivot_ch6.read_text(encoding="utf-8"))
        audit("ch06/pivot_word (Claire's note)", ch6)

    # 3) The audit at scale: Sophie's corpus.
    print("\n" + "=" * 78)
    print("CORPUS AUDIT (Sophie)")
    print("=" * 78)
    corpus = json.loads((DOCS / "sophie_corpus.json").read_text(encoding="utf-8"))
    results = []
    for doc in corpus:
        score, _ = score_document(doc["pivot"])
        results.append((doc["name"], score))
    for name, score in sorted(results, key=lambda x: x[1]):
        state = "rework" if score < 3 else ("improvable" if score < 5 else "AI-ready")
        print(f"  {score}/5  {name:28s}  {state}")

    print("\n" + "=" * 78)
    print("WHAT TO REMEMBER")
    print("=" * 78)
    print(f"- The hostile version scores {s_hostile}/5, the AI-ready one {s_ready}/5:")
    print("  the same content, two radically different levels of usability.")
    print("- The linter makes document quality visible and actionable at scale.")
    print("- Detecting the hostile means checking the chapter's five principles mechanically.")


if __name__ == "__main__":
    main()
