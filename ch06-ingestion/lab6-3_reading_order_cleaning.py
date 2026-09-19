# -*- coding: utf-8 -*-
"""
Lab 6-3 — Reading order and noise cleaning (Sophie)

Learning objective
------------------
Two defects of PDF extraction are corrected here, on a real two-column
procurement document:

  1. THE NOISE: repeated running heads and page footers — the contract
     reference, the confidentiality notice, the page number. They are detected
     and removed.

  2. THE READING ORDER: a naive parser reads line by line ACROSS both columns,
     interleaving the articles. They are un-interleaved by horizontal position
     (bounding boxes), so the left column is read in full before the right one.

The lab shows both approaches:

  - a geometric heuristic, using word positions, which is the recommended one;
  - a fallback using regular expressions, for the noise cleaning alone.

A note on the noise patterns: they match the exact wording of the running head
and footer produced by generate_sample_docs.py. If you change that wording,
update these patterns too, or the noise will silently survive the cleaning —
the script will still run, and the second lesson will quietly disappear.

Requires pdfplumber. Run generate_sample_docs.py first.
"""

import re
from pathlib import Path
from typing import List

DOCS = Path(__file__).resolve().parent / "sample_docs"
PDF = DOCS / "sophie_contract_2columns.pdf"

# Patterns of the repeated noise, specific to public procurement documents.
NOISE_PATTERNS = [
    re.compile(r"^PUBLIC CONTRACT No\..*", re.IGNORECASE),
    re.compile(r"^Confidential document.*", re.IGNORECASE),
    re.compile(r"^Page\s+\d+\s*/\s*\d+\s*$", re.IGNORECASE),
]


def is_noise(line: str) -> bool:
    return any(pattern.match(line.strip()) for pattern in NOISE_PATTERNS)


# ---------------------------------------------------------------------------
# The naive approach: text extraction line by line (the problem)
# ---------------------------------------------------------------------------
def naive_extraction(path: Path) -> List[str]:
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return [l for l in text.splitlines() if l.strip()]


# ---------------------------------------------------------------------------
# The geometric approach: un-interleaving by column (the solution)
# ---------------------------------------------------------------------------
def extract_by_columns(path: Path) -> List[str]:
    """Rebuild the reading order by separating the words into columns.

    The principle: every extracted word has a horizontal position (x0). The
    page is split into two columns at the midpoint, the words are grouped into
    lines by their rounded vertical coordinate, and the left column is then read
    in full before the right one.
    """
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        page = pdf.pages[0]
        middle = page.width / 2
        words = page.extract_words()

    left = [w for w in words if w["x0"] < middle]
    right = [w for w in words if w["x0"] >= middle]

    def rebuild(column) -> List[str]:
        # Group the words into lines by their rounded vertical coordinate.
        lines_by_y = {}
        for w in column:
            key = round(w["top"] / 5)   # a tolerance of 5 points
            lines_by_y.setdefault(key, []).append(w)
        lines = []
        for key in sorted(lines_by_y):
            line_words = sorted(lines_by_y[key], key=lambda w: w["x0"])
            lines.append(" ".join(w["text"] for w in line_words))
        return lines

    return rebuild(left) + rebuild(right)


def clean(lines: List[str]) -> List[str]:
    """Strip the repeated noise."""
    return [l for l in lines if not is_noise(l)]


def main() -> None:
    print("=" * 78)
    print("Lab 6-3 — Reading order and noise cleaning (Sophie)")
    print("=" * 78)

    if not PDF.exists():
        print("\nDocument not found. Run this first: python generate_sample_docs.py")
        return

    # --- The problem: naive extraction ---
    print("\n--- BEFORE: naive line-by-line extraction (the columns interleave) ---")
    naive = naive_extraction(PDF)
    for line in naive[:8]:
        print(f"  {line}")
    print("  ...")
    print("\nObservation: \"Article 1\" and \"Article 3\" are mixed on the same line.")

    # --- The solution: un-interleaving plus cleaning ---
    print("\n--- AFTER: un-interleaved by column, and the noise stripped ---")
    by_columns = extract_by_columns(PDF)
    cleaned = clean(by_columns)
    for line in cleaned:
        print(f"  {line}")

    # --- The summary ---
    noise_removed = len(by_columns) - len(cleaned)
    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print(f"Lines before cleaning      : {len(by_columns)}")
    print(f"Noise lines removed        : {noise_removed}")
    print(f"Final lines ready for chunking: {len(cleaned)}")

    # Check the order: Articles 1, 2, 3, 4 must appear in sequence.
    text = " ".join(cleaned)
    positions = [text.find(f"Article {i}") for i in range(1, 5)]
    order_ok = all(positions[i] < positions[i + 1] for i in range(3)) and -1 not in positions
    print(f"Reading order of articles 1->4 respected: {'YES' if order_ok else 'NO'}")

    print("\nWHAT TO REMEMBER")
    print("- Repeated noise, running heads and footers, is detected by pattern and stripped.")
    print("- On two columns, reading line by line interleaves the text: you have to")
    print("  un-interleave by horizontal position before any chunking.")
    print("- Restoring the logical reading order is an indispensable preprocessing step.")


if __name__ == "__main__":
    main()
