# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 13.

The chapter rests on a single discipline: you never chunk the raw file, you chunk
what you have RECONSTRUCTED from it. To demonstrate that, the SAME document is
needed in two forms, and that is exactly what this script produces:

    corpus/raw_document.txt
        The text "as extracted, straight through" from a PDF: repeated running
        heads and footers, lone page numbers — one of which lands in the MIDDLE
        of a sentence ("two days 14 per week") — headings glued to the text, and
        a table FLATTENED into a run of words and numbers. This is the creased
        cloth: cut into it, and you cut across the grain.

    corpus/canonical_document.json
        The reconstructed JSON document, in the pivot format: a clean hierarchy
        of headings, typed paragraphs, the table kept as ONE indivisible
        Markdown block, the pagination noise removed, and — decisive for what
        follows — the hierarchical path attached to each block in its metadata.
        This is the pressed cloth, ready to be cut.

The running thread: Claire (the HR note on remote work, consistent with
Chapter 12: two days maximum) and the allowances scale (the table).

A NOTE ON THE PAGE NUMBER. The string "14" inserted mid-sentence in build_raw is
the whole point of Lab 13-1: a naive splitter cuts there and produces a fragment
that reads "two days 14". Do not tidy it away.

Deterministic. No API key. Run before the labs: python generate_corpus.py
"""

from pathlib import Path
import json

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# The documentary "truth": the clean, structured document. The two artefacts —
# the noisy raw text and the canonical JSON — are derived from it AFTERWARDS.
# ---------------------------------------------------------------------------
DOCUMENT = {
    "title": "HR note — Organisation of work",
    "sections": [
        {
            "title": "Remote work",
            "paragraphs": [
                "Remote work is authorised up to a limit of two days per week, "
                "in agreement with the line manager.",
                "The request is made through the HR portal at least one week in "
                "advance.",
            ],
            "subsections": [
                {
                    "title": "Exceptional leave",
                    "paragraphs": [
                        "One day of exceptional leave is granted for moving "
                        "house, on production of evidence.",
                    ],
                }
            ],
        },
        {
            "title": "Allowances",
            "paragraphs": [
                "The sustainable travel allowance amounts to four hundred euros "
                "a year, subject to eligibility.",
            ],
            "tables": [
                {
                    "title": "Mileage allowance scale",
                    "columns": ["Distance", "Rate"],
                    "rows": [
                        ["0 to 5 km", "0.25 EUR/km"],
                        ["6 to 20 km", "0.30 EUR/km"],
                        ["over 20 km", "0.35 EUR/km"],
                    ],
                }
            ],
        },
    ],
}


# ---------------------------------------------------------------------------
# 1) THE RAW DOCUMENT — flattened text plus the structural noise of a "straight
#    through" extraction.
# ---------------------------------------------------------------------------
def build_raw(doc: dict) -> str:
    header = "HUMAN RESOURCES DEPARTMENT"
    footer = "Confidential — internal use"
    lines: list[str] = []
    page = [1]

    def page_break():
        lines.append(footer)
        lines.append(str(page[0]))   # a lone page number
        page[0] += 1
        lines.append(header)

    lines.append(header)
    lines.append(doc["title"])       # the title drowned in the flow

    for sec in doc["sections"]:
        lines.append(sec["title"])   # the heading glued to the text, no hierarchy
        for p in sec.get("paragraphs", []):
            lines.append(p)
        for ss in sec.get("subsections", []):
            lines.append(ss["title"])
            for p in ss.get("paragraphs", []):
                lines.append(p)
        for tab in sec.get("tables", []):
            # The table FLATTENED: cells concatenated, the structure lost.
            lines.append(tab["title"])
            lines.append("  ".join(tab["columns"]))
            for row in tab["rows"]:
                lines.append("  ".join(row))
        page_break()

    text = "\n".join(lines)

    # The coup de grace: a page number landing IN THE MIDDLE of a sentence, the
    # remnant of a badly extracted page foot. Lab 13-1 depends on this.
    text = text.replace(
        "up to a limit of two days per week",
        "up to a limit of two days 14 per week",
    )
    return text


# ---------------------------------------------------------------------------
# 2) THE CANONICAL JSON — the pivot format: typed blocks plus a hierarchical path.
# ---------------------------------------------------------------------------
def build_canonical(doc: dict) -> dict:
    blocks: list[dict] = []

    def emit(text: str, kind: str, path: list[str]):
        blocks.append({
            "type": kind,
            "text": text,
            "metadata": {
                "document": doc["title"],
                "path": list(path),
                "section": path[-1] if path else None,
            },
        })

    def walk(section: dict, parents: list[str]):
        path = parents + [section["title"]]
        for p in section.get("paragraphs", []):
            emit(p, "paragraph", path)
        for tab in section.get("tables", []):
            emit(_table_markdown(tab), "table", path + [tab["title"]])
        for ss in section.get("subsections", []):
            walk(ss, path)

    for sec in doc["sections"]:
        walk(sec, [])

    return {"document": doc["title"], "blocks": blocks}


def _table_markdown(tab: dict) -> str:
    cols = tab["columns"]
    out = [f"**{tab['title']}**",
           "| " + " | ".join(cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in tab["rows"]:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def main() -> None:
    print("Generating the Chapter 13 test corpus:")

    raw = build_raw(DOCUMENT)
    canon = build_canonical(DOCUMENT)

    (CORPUS / "raw_document.txt").write_text(raw, encoding="utf-8")
    (CORPUS / "canonical_document.json").write_text(
        json.dumps(canon, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  + raw_document.txt         ({len(raw)} characters, flattened plus noise)")
    print(f"  + canonical_document.json  ({len(canon['blocks'])} structured blocks)")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
