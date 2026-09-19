# -*- coding: utf-8 -*-
"""
Lab 6-2 — The trap of the flattened table: Level 1 against Level 3 (Julien)

Learning objective
------------------
Experience the loss of structural information from a table, depending on the
parser:

    Level 1 (raw)        : linear text extraction. Rows and columns are
                           flattened; the figures lose their heading.
    Level 3 (structural) : the table is extracted as a grid (pdfplumber).
                           Each cell keeps its row and its column.

It then shows why a naive search fails at Level 1: the question "maximum
pressure of the MX-200" does not find the value, because the row/column link has
disappeared.

Level 3 here is pdfplumber, which is light and needs no API key. To go further,
tools such as Docling or LlamaParse produce structured Markdown or JSON
directly; see the note at the end of the file.

A note on the lookup: the parameter searched for, "pressure", must appear in the
column heading produced by generate_sample_docs.py. If the heading is reworded,
Level 3 will report "column not found" while the script still exits cleanly.

Requires pypdf and pdfplumber. Run generate_sample_docs.py first.
"""

from pathlib import Path
from typing import Dict, List, Optional

DOCS = Path(__file__).resolve().parent / "sample_docs"
PDF = DOCS / "julien_table_report.pdf"


# ---------------------------------------------------------------------------
# Level 1 — raw text extraction
# ---------------------------------------------------------------------------
def extract_level1(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


# ---------------------------------------------------------------------------
# Level 3 — structural extraction of the table
# ---------------------------------------------------------------------------
def extract_level3(path: Path) -> Optional[List[List[str]]]:
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                # Clean the cells (None -> "").
                return [[(c or "").strip() for c in row] for row in table]
    return None


def table_to_markdown(table: List[List[str]]) -> str:
    if not table:
        return "(no table)"
    header = table[0]
    lines = ["| " + " | ".join(header) + " |",
             "| " + " | ".join("---" for _ in header) + " |"]
    for row in table[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def table_to_records(table: List[List[str]]) -> List[Dict[str, str]]:
    """Turn the grid into records: one row becomes one dict {column: value}."""
    if not table or len(table) < 2:
        return []
    header = table[0]
    return [dict(zip(header, row)) for row in table[1:]]


# ---------------------------------------------------------------------------
# Demonstration: looking up a value at the crossing of a row and a column
# ---------------------------------------------------------------------------
def lookup_level1(raw_text: str, model: str, parameter: str) -> str:
    """Try to find a value in the flattened text.

    This simulates a naive search: look for the parameter near the model in the
    linear text. Since the row/column structure is lost, the association is
    fragile, and in practice impossible.
    """
    # In the raw text the column headings and the rows are separated: there is
    # no way to know which value belongs to which (row, column) pair.
    return ("undetermined — the flattened text no longer ties the value to its "
            "column heading or to its model row")


def lookup_level3(records: List[Dict[str, str]], model: str,
                  parameter: str) -> str:
    """Find a value by crossing the row (model) with the column (parameter)."""
    model_row = None
    for record in records:
        # The first column identifies the model.
        model_key = list(record.keys())[0]
        if record[model_key] == model:
            for key, val in record.items():
                if parameter.lower() in key.lower():
                    return val
            model_row = record
    if model_row is not None:
        return "column not found"
    return "model not found"


def main() -> None:
    print("=" * 78)
    print("Lab 6-2 — The trap of the flattened table: Level 1 against Level 3 (Julien)")
    print("=" * 78)

    if not PDF.exists():
        print("\nDocument not found. Run this first: python generate_sample_docs.py")
        return

    # --- Level 1 ---
    print("\n--- LEVEL 1: raw text extraction ---")
    raw = extract_level1(PDF)
    print(raw.strip()[:500])

    # --- Level 3 ---
    print("\n--- LEVEL 3: structural extraction (pdfplumber) ---")
    table = extract_level3(PDF)
    if not table:
        print("No table detected.")
        return
    print(table_to_markdown(table))

    records = table_to_records(table)

    # --- The lookup demonstration ---
    print("\n" + "=" * 78)
    print("DEMONSTRATION: \"What is the maximum pressure of the MX-200?\"")
    print("=" * 78)

    v1 = lookup_level1(raw, "MX-200", "pressure")
    v3 = lookup_level3(records, "MX-200", "pressure")

    print(f"Level 1 (raw text)   : {v1}")
    print(f"Level 3 (structural) : {v3} bar")

    print("\nWHAT TO REMEMBER")
    print("- Flattening the text destroys the row-by-column link of a table.")
    print("- The same figure becomes unusable: you no longer know what it refers to.")
    print("- A structural parser preserves the grid: the value stays queryable.")

    print("\nNOTE — going further than pdfplumber")
    print("Advanced structure parsers such as Docling or LlamaParse produce Markdown")
    print("or JSON directly, handle merged cells and tables spanning several pages.")
    print("The teaching principle stays the same: preserve the structure rather than")
    print("flattening the text.")


if __name__ == "__main__":
    main()
