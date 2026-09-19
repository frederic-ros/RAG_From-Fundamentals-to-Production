# -*- coding: utf-8 -*-
"""
Lab 8-1 — Extraction Word : of the style natif to the arborescence JSON (Claire)

Learning objective
--------------------
Query, in code, the structure DECLARED by a Word document — its heading styles
of title Heading 1, Heading 2, ...) for the couler in the JSON documentaire pivot,
while preserving the parent/child hierarchy of the sections. The opposite of
extracting "by the mile", which flattens everything.

No dependency beyond python-docx. No API key.
Lancer first generate_sample_docs.py.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

DOCS = Path(__file__).resolve().parent / "sample_docs"
DOCX = DOCS / "claire_remote_work_agreement.docx"


def title_level(style_name: str) -> Optional[int]:
    """Returns the level of title (0 for the title of the document, 1, 2, ...)."""
    s = (style_name or "").lower()
    if s in {"title", "heading 0"}:
        return 0
    m = re.match(r"heading (\d+)", s)
    if m:
        return int(m.group(1))
    return None


def extract_tree(path: Path) -> Dict:
    """Construit a JSON documentaire with hierarchy parent/enfant.

 Each section porte son level, son title, son text propre and ses
 under-sections. On reconstruit the tree from the SUITE styles.
 """
    from docx import Document

    doc = Document(path)
    pivot = {"title": "", "sections": [], "metadata": {"source_format": "docx"}}

    # Pile sections ouvertes, by level (for rattacher at the bon parent).
    pile: List[Dict] = []

    def add_section(level: int, title: str) -> Dict:
        section = {"level": level, "title": title, "text": "", "subsections": []}
        # Pop until a parent of strictly lower level is found.
        while pile and pile[-1]["level"] >= level:
            pile.pop()
        if pile:
            pile[-1]["subsections"].append(section)
        else:
            pivot["sections"].append(section)
        pile.append(section)
        return section

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        level = title_level(para.style.name)

        if level == 0:
            pivot["title"] = text
        elif level is not None:
            add_section(level, text)
        else:
            # A body paragraph: attached to the current section.
            if pile:
                sep = " " if pile[-1]["text"] else ""
                pile[-1]["text"] += sep + text
            else:
                pivot["metadata"].setdefault("entete", text)

    return pivot


def compter(sections: List[Dict]) -> int:
    total = 0
    for s in sections:
        total += 1 + compter(s.get("subsections", []))
    return total


def show_tree(sections: List[Dict], indent: int = 0) -> None:
    for s in sections:
        prefix = "  " * indent + ("└ " if indent else "")
        excerpt = s["text"][:50] + ("…" if len(s["text"]) > 50 else "")
        print(f"{prefix}[H{s['level']}] {s['title']}  —  {excerpt}")
        show_tree(s.get("subsections", []), indent + 1)


def main() -> None:
    print("=" * 78)
    print("Lab 8-1 — Word extraction: from the native style to a JSON tree (Claire)")
    print("=" * 78)

    if not DOCX.exists():
        print("\nDocument introuvable. Lancez d'abord : python generate_sample_docs.py")
        return

    pivot = extract_tree(DOCX)

    print(f"\nTitre du document : {pivot['title']}")
    print(f"Sections de premier level : {len(pivot['sections'])}")
    print(f"Sections au total (toutes profondeurs) : {compter(pivot['sections'])}")

    print("\n--- Arborescence reconstruite ---")
    show_tree(pivot["sections"])

    out_path = DOCS / "pivot_word.json"
    out_path.write_text(json.dumps(pivot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out_path.name}")

    # --- From the pivot to the chunks (the "and then to chunks" of the chapter) ---
    from chunking import chunk_pivot, preview
    chunks = chunk_pivot(pivot, prefix="CHUNK_WORD")
    print(f"\n--- Chunks produits : {len(chunks)} ---")
    preview(chunks)
    chunks_path = DOCS / "chunks_word.json"
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Chunks written: {chunks_path.name}")

    print("\nA RETENIR")
    print("- Word heading styles carry a hierarchy: you have to READ it, not ignore it.")
    print("- Extracting \"by the mile\" destroys the parent/child tree.")
    print("- Each chunk inherits its section path, a breadcrumb trail, and its provenance.")


if __name__ == "__main__":
    main()
