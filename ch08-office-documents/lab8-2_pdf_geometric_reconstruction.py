# -*- coding: utf-8 -*-
"""
Lab 8-2 — The recalcitrant PDF: rebuilding the reading order geometrically (Julien)

Learning objective
------------------
Move from extracting a stream of characters to RE-COMPUTING the logic of the
layout. The document is set in two columns, with repeated running heads and
footers: a naive parser interleaves the columns line by line. Here the words are
sorted geometrically by their (x, y) coordinates, so the left column is read in
full and then the right one, and the parasitic elements are filtered out.

No API key. Dependency: pdfplumber.
Run generate_sample_docs.py first.
"""

import json
import re
from pathlib import Path
from typing import Dict, List

DOCS = Path(__file__).resolve().parent / "sample_docs"
PDF = DOCS / "julien_remote_work_agreement.pdf"

NOISE_PATTERNS = [
    re.compile(r"^REMOTE WORK AGREEMENT.*", re.IGNORECASE),
    re.compile(r"^Official document.*", re.IGNORECASE),
    re.compile(r"^Page\s+\d+\s*/\s*\d+\s*$", re.IGNORECASE),
]


def is_noise(ligne: str) -> bool:
    return any(m.match(ligne.strip()) for m in NOISE_PATTERNS)


def naive_extraction(path: Path) -> List[str]:
    import pdfplumber
    with pdfplumber.open(str(path)) as pdf:
        text = pdf.pages[0].extract_text() or ""
    return [l for l in text.splitlines() if l.strip()]


def geometric_extraction(path: Path) -> List[str]:
    """Sort the words by column (x) then by line (y), to restore the order."""
    import pdfplumber
    with pdfplumber.open(str(path)) as pdf:
        page = pdf.pages[0]
        middle = page.width / 2
        words = page.extract_words()

    def rebuild(column) -> List[str]:
        lines_by_y: Dict[int, list] = {}
        for m in column:
            key = round(m["top"] / 5)
            lines_by_y.setdefault(key, []).append(m)
        lines = []
        for key in sorted(lines_by_y):
            line_words = sorted(lines_by_y[key], key=lambda m: m["x0"])
            lines.append(" ".join(m["text"] for m in line_words))
        return lines

    left = [m for m in words if m["x0"] < middle]
    right = [m for m in words if m["x0"] >= middle]
    return rebuild(left) + rebuild(right)


def clean(lines: List[str]) -> List[str]:
    return [l for l in lines if not is_noise(l)]


def group_into_sections(lines: List[str]) -> Dict:
    """Cut the clean lines into sections on "Article N - ..."."""
    pivot = {"title": "Remote work agreement (official PDF)",
             "sections": [],
             "metadata": {"source_format": "pdf", "status": "approved",
                          "date": "2025-03-15"}}
    pattern = re.compile(r"^Article\s+\d+\s*-\s*(.*)", re.IGNORECASE)
    current = None
    for line in lines:
        if pattern.match(line):
            current = {"title": line.rstrip("."), "text": ""}
            pivot["sections"].append(current)
        elif current is not None:
            sep = " " if current["text"] else ""
            current["text"] += sep + line
    return pivot


def main() -> None:
    print("=" * 78)
    print("Lab 8-2 — The recalcitrant PDF: geometric reconstruction (Julien)")
    print("=" * 78)

    if not PDF.exists():
        print("\nDocument not found. Run this first: python generate_sample_docs.py")
        return

    print("\n--- BEFORE: the naive extraction, columns interleaved ---")
    for line in naive_extraction(PDF)[:6]:
        print(f"  {line}")
    print("  ...")

    print("\n--- AFTER: the geometric sort, plus noise filtering ---")
    geo = geometric_extraction(PDF)
    cleaned = clean(geo)
    for line in cleaned:
        print(f"  {line}")

    pivot = group_into_sections(cleaned)

    # Check the order of the articles.
    text = " ".join(cleaned)
    positions = [text.find(f"Article {i}") for i in range(1, 5)]
    order_ok = all(positions[i] < positions[i + 1] for i in range(3)) and -1 not in positions

    print("\n" + "=" * 78)
    print("THE RESULT")
    print("=" * 78)
    print(f"Noise lines removed: {len(geo) - len(cleaned)}")
    print(f"Sections (articles) rebuilt: {len(pivot['sections'])}")
    print(f"Reading order Article 1->4 respected: {'YES' if order_ok else 'NO'}")

    out_path = DOCS / "pivot_pdf.json"
    out_path.write_text(json.dumps(pivot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON written: {out_path.name}")

    # --- From the pivot to the chunks ---
    from chunking import chunk_pivot, preview
    chunks = chunk_pivot(pivot, prefix="CHUNK_PDF")
    print(f"\n--- Chunks produits : {len(chunks)} ---")
    preview(chunks)
    chunks_path = DOCS / "chunks_pdf.json"
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Chunks written: {chunks_path.name}")

    print("\nWHAT TO REMEMBER")
    print("- A PDF has no reading order: it has (x, y) positions to be interpreted.")
    print("- Reading line by line interleaves the columns; sorting by geometry separates them.")
    print("- The official PDF says \"three days\": hold on to that for Lab 8-5.")


if __name__ == "__main__":
    main()
