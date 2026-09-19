# -*- coding: utf-8 -*-
"""
Lab 6-1 — From a multi-format document to a document JSON (Claire)

Learning objective
------------------
Take the same content in three source formats (Word, HTML, PDF) and standardise
it into a single pivot format: a JSON dictionary holding the title, the sections
and some basic metadata.

The message to take away:

    The quality of the final information depends intimately on the technical
    nature of the source format. Word and HTML carry an explicit structure; a
    native PDF often loses it, and forces you into heuristics.

Requires python-docx, beautifulsoup4, pypdf. No LLM needed.
Run generate_sample_docs.py first, to produce the files.
"""

import json
from pathlib import Path
from typing import Dict, List

DOCS = Path(__file__).resolve().parent / "sample_docs"


def empty_pivot(source: str) -> Dict:
    """The pivot structure, shared by every format."""
    return {
        "title": "",
        "sections": [],          # a list of {"title": ..., "content": ...}
        "metadata": {"source_format": source},
    }


# ---------------------------------------------------------------------------
# 1. Word (.docx) — an explicit structure, through the heading styles
# ---------------------------------------------------------------------------
def parse_docx(path: Path) -> Dict:
    from docx import Document

    doc = Document(path)
    pivot = empty_pivot("docx")
    current_section = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        style = (para.style.name or "").lower()

        if "title" in style or style == "heading 0":
            pivot["title"] = text
        elif "heading" in style:
            current_section = {"title": text, "content": ""}
            pivot["sections"].append(current_section)
        else:
            if current_section is None:
                # Text before any section: often the metadata line.
                pivot["metadata"].setdefault("header", text)
            else:
                sep = " " if current_section["content"] else ""
                current_section["content"] += sep + text

    return pivot


# ---------------------------------------------------------------------------
# 2. HTML — an explicit structure, through the h1/h2/p tags and <meta>
# ---------------------------------------------------------------------------
def parse_html(path: Path) -> Dict:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    pivot = empty_pivot("html")

    h1 = soup.find("h1")
    if h1:
        pivot["title"] = h1.get_text(strip=True)

    for meta in soup.find_all("meta"):
        name = meta.get("name")
        if name and meta.get("content"):
            pivot["metadata"][name] = meta["content"]

    current_section = None
    for elem in soup.find_all(["h2", "p"]):
        if elem.name == "h2":
            current_section = {"title": elem.get_text(strip=True), "content": ""}
            pivot["sections"].append(current_section)
        elif elem.name == "p" and current_section is not None:
            if "meta" in (elem.get("class") or []):
                continue
            current_section["content"] = elem.get_text(strip=True)

    return pivot


# ---------------------------------------------------------------------------
# 3. A native PDF — no explicit structure: a heuristic on the text
# ---------------------------------------------------------------------------
def parse_pdf(path: Path) -> Dict:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    lines: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        lines.extend(l.strip() for l in text.splitlines() if l.strip())

    pivot = empty_pivot("pdf")
    if not lines:
        return pivot

    # A simple heuristic: the first line is the title, and the sections are
    # guessed from a list of known headings. A native PDF gives NO guarantee of
    # structure at all — which is the whole teaching point.
    #
    # CAREFUL: this list must match the section titles produced by
    # generate_sample_docs.py. If they diverge, the PDF pivot silently comes
    # back with zero sections, and the script still exits cleanly.
    pivot["title"] = lines[0]
    known_headings = {"Purpose", "Number of days", "Eligibility conditions", "Equipment"}

    current_section = None
    for line in lines[1:]:
        if line in known_headings:
            current_section = {"title": line, "content": ""}
            pivot["sections"].append(current_section)
        elif current_section is not None:
            sep = " " if current_section["content"] else ""
            current_section["content"] += sep + line
        else:
            pivot["metadata"].setdefault("header", line)

    return pivot


def summarize(pivot: Dict) -> str:
    n = len(pivot["sections"])
    meta = len(pivot["metadata"])
    return f"title={'yes' if pivot['title'] else 'NO'} | sections={n} | meta keys={meta}"


def main() -> None:
    print("=" * 78)
    print("Lab 6-1 — From a multi-format document to a document JSON (Claire)")
    print("=" * 78)

    if not DOCS.exists():
        print("\nDocuments not found. Run this first: python generate_sample_docs.py")
        return

    targets = [
        ("Word", DOCS / "claire_service_note.docx", parse_docx),
        ("HTML", DOCS / "claire_service_note.html", parse_html),
        ("PDF", DOCS / "claire_service_note.pdf", parse_pdf),
    ]

    pivots = {}
    for name, path, parser in targets:
        print(f"\n--- Source format: {name} ({path.name}) ---")
        if not path.exists():
            print("  file missing, skipped.")
            continue
        pivot = parser(path)
        pivots[name] = pivot
        print("  " + summarize(pivot))
        out = DOCS / f"pivot_{name.lower()}.json"
        out.write_text(json.dumps(pivot, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  JSON written: {out.name}")

    print("\n" + "=" * 78)
    print("A COMPARISON OF FIDELITY")
    print("=" * 78)
    for name, pivot in pivots.items():
        print(f"{name:5s} | {summarize(pivot)}")

    print("\nWHAT TO REMEMBER")
    print("- Word and HTML carry an explicit structure, through styles and tags: easy.")
    print("- A native PDF has no notion of a section: you have to guess by heuristic.")
    print("- The JSON pivot format unifies these sources for the rest of the RAG chain.")


if __name__ == "__main__":
    main()
