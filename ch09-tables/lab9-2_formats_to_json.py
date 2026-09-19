# -*- coding: utf-8 -*-
"""
Lab 9-2 — From pure data formats to the JSON document (Excel, CSV)

Learning objective
------------------
Carry pure data formats — Excel and CSV here — over to the JSON document,
distinguishing the FILE (the technical container) from the STRUCTURE of
knowledge it carries. An Excel workbook is not continuous text: it is a book of
sheets, of typed columns and of rows. That structure is preserved.

One pivot is produced per source, carrying in its metadata the provenance (file,
sheet), the columns and their types. This is the base reused by all the labs
that follow.

No API key. Dependencies: pandas, openpyxl.
Run generate_sample_data.py first.
"""

import json
from pathlib import Path
from typing import Dict, List

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"


def column_type(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "decimal"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    return "text"


def df_to_pivot(df: pd.DataFrame, source: str, sheet: str) -> Dict:
    """Turn a DataFrame into a structured document pivot."""
    columns = [{"name": c, "type": column_type(df[c])} for c in df.columns]
    rows = []
    for i, row in df.iterrows():
        # Each row stays a key/value object: the relation is preserved.
        rows.append({"index": int(i), "values": {c: _val(row[c]) for c in df.columns}})
    return {
        "type": "table",
        "source_file": source,
        "sheet": sheet,
        "n_rows": len(df),
        "columns": columns,
        "rows": rows,
    }


def _val(v):
    """Normalise numpy and pandas values into native JSON types."""
    if pd.isna(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def load_excel(path: Path) -> List[Dict]:
    """An Excel workbook may hold SEVERAL sheets: one structure per sheet."""
    pivots = []
    sheets = pd.read_excel(path, sheet_name=None)  # a dict {sheet: df}
    for sheet_name, df in sheets.items():
        pivots.append(df_to_pivot(df, path.name, sheet_name))
    return pivots


def load_csv(path: Path) -> Dict:
    df = pd.read_csv(path)
    return df_to_pivot(df, path.name, sheet="(csv)")


def summarize(pivot: Dict) -> None:
    print(f"  source={pivot['source_file']} | sheet={pivot['sheet']} "
          f"| {pivot['n_rows']} rows | {len(pivot['columns'])} columns")
    types = ", ".join(f"{c['name']}:{c['type']}" for c in pivot["columns"])
    print(f"    typed columns: {types}")


def main() -> None:
    print("=" * 78)
    print("Lab 9-2 — From pure data formats to the JSON document (Excel, CSV)")
    print("=" * 78)

    if not DATA.exists():
        print("\nData not found. Run this first: python generate_sample_data.py")
        return

    all_pivots = []

    # 1. Julien's multi-sheet Excel workbook.
    xlsx = DATA / "Maintenance_Batteries.xlsx"
    if xlsx.exists():
        print("\n--- Excel (Julien): one structure per sheet ---")
        for pivot in load_excel(xlsx):
            summarize(pivot)
            all_pivots.append(pivot)

    # 2. The CSVs of Sophie (budget) and Claire (HR).
    for name in ("road_budget.csv", "hr_leave.csv"):
        path = DATA / name
        if path.exists():
            print(f"\n--- CSV ({name}) ---")
            pivot = load_csv(path)
            summarize(pivot)
            all_pivots.append(pivot)

    # Write the pivots.
    out = DATA / "table_pivots.json"
    out.write_text(json.dumps(all_pivots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nPivots written: {out.name} ({len(all_pivots)} tables)")

    print("\n" + "=" * 78)
    print("FILE AGAINST STRUCTURE")
    print("=" * 78)
    print("- The FILE is the container: .xlsx, .csv. It varies with the tool.")
    print("- The STRUCTURE is the knowledge: typed columns, related rows. That is")
    print("  what the pivot preserves, not the original format.")
    print("- Each row stays a key/value object: the relation is never flattened.")

    print("\nWHAT TO REMEMBER")
    print("- An Excel workbook is not text: it is a book of structured sheets.")
    print("- Keep the columns, their types, and the provenance: file and sheet.")
    print("- This pivot is the base of the four representations (Lab 9-3) and Table-RAG (Lab 9-4).")


if __name__ == "__main__":
    main()
