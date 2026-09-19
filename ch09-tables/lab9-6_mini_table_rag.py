# -*- coding: utf-8 -*-
"""
Lab 9-6 — Mini Table-RAG: the synthesis (routing search against calculation)

Learning objective
------------------
Assemble the whole chapter into a small system that ROUTES each question to the
right approach: search questions — semantic, about an entity — to verbalisation
plus vector search, and calculation questions — totals, filters, aggregations —
to a structured SQL query. This is the mark of maturity of the chapter:

    A good architect does not push everything through the map of meaning.
    Search questions go to the RAG, calculation questions go to the SQL.

The router is deliberately simple and deterministic, driven by calculation
keywords. It reuses the verbalisation of Lab 9-3 and the SQL Table-RAG of
Lab 9-4.

No API key. Dependencies: pandas, scikit-learn. Reuses Lab 9-4.
Run generate_sample_data.py first.
"""

import importlib.util
from pathlib import Path
from typing import List

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
XLSX = DATA / "Maintenance_Batteries.xlsx"

# Reuse the SQL Table-RAG of Lab 9-4.
_lab94 = Path(__file__).resolve().parent / "lab9-4_table_rag_sql.py"
_spec = importlib.util.spec_from_file_location("lab94", _lab94)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# The keywords that signal a CALCULATION question, to be routed to the SQL.
CALCULATION_WORDS = ["how many", "count", "average", "mean", "total", "sum",
                     "cumulative", "maximum", "minimum", "max", "min",
                     "highest", "lowest", "per site", "by site", "under",
                     "below", "above", "greater than", "less than",
                     "number of"]


def router(question: str) -> str:
    """Decide: 'calculation' (SQL) or 'search' (vector)."""
    q = question.lower()
    return "calculation" if any(w in q for w in CALCULATION_WORDS) else "search"


def build_verbalized(df: pd.DataFrame) -> List[str]:
    cols = list(df.columns)
    key = cols[0]
    sentences = []
    for _, row in df.iterrows():
        details = ", ".join(f"{c} = {row[c]}" for c in cols[1:])
        sentences.append(f"For {key} {row[key]}: {details}.")
    return sentences


def vector_search(fragments: List[str], question: str) -> str:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(fragments + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    return fragments[int(sims.argmax())]


def main() -> None:
    print("=" * 78)
    print("Lab 9-6 — Mini Table-RAG: the synthesis (routing search against calculation)")
    print("=" * 78)

    if not XLSX.exists():
        print("\nFile not found. Run this first: python generate_sample_data.py")
        return

    df = pd.read_excel(XLSX, sheet_name="Batteries")
    verbalised = build_verbalized(df)
    conn = _mod.load_sqlite()
    columns = [r[1] for r in conn.execute(f"PRAGMA table_info({_mod.TABLE})").fetchall()]

    questions = [
        "What is the recommended action for BAT005?",     # search
        "Which workshop holds BAT003?",                   # search
        "How many batteries are to replace?",             # calculation
        "What is the average voltage?",                   # calculation
        "Which equipment has a voltage under 11.5?",      # calculation
        "What is the status of BAT002?",                  # search
    ]

    print("\n" + "=" * 78)
    print("THE ROUTER IN ACTION")
    print("=" * 78)
    for question in questions:
        route = router(question)
        if route == "calculation":
            result, sql = _mod.answer(conn, question, "offline", columns)
            detail = f"SQL: {sql}"
        else:
            result = vector_search(verbalised, question)
            detail = "the vector route (verbalisation)"
        print(f"\nQ: {question}")
        print(f"   routed to: {route.upper()}  ({detail})")
        print(f"   ->  {result[:90]}")

    print("\n" + "=" * 78)
    print("WHAT THE MINI TABLE-RAG DOES")
    print("=" * 78)
    print("- It reads the question and decides whether it is a matter of meaning or of calculation.")
    print("- Entity questions go through verbalisation: the relation is recovered.")
    print("- Calculation questions go through the SQL: the answer is exact.")
    print("- The two routes coexist, and the router chooses between them.")

    print("\nWHAT TO REMEMBER")
    print("- The synthesis of the chapter: do not vectorise everything, route by the question.")
    print("- A cell holds a value; a table holds a relation. Preserve it by verbalising, or")
    print("  query it with SQL — but never flatten it.")
    print("- This is architectural maturity: the right representation at the right moment.")

    conn.close()


if __name__ == "__main__":
    main()
