# -*- coding: utf-8 -*-
"""
Lab 9-5 — The arena of structures: a comparative benchmark

Learning objective
------------------
Develop an engineering instinct: choose the right representation according to
the nature of the question. Three approaches are compared over one table, with a
set of questions labelled either "search" (semantic) or "calculation":

  A. Raw       : the table flattened, plus a TF-IDF search.
  B. Verbalised: rows turned into sentences, plus a TF-IDF search.
  C. Table-RAG : the question translated into SQL (reusing Lab 9-4).

The success rate and the time are measured, by approach and by kind of question.
The aim is not to name an absolute winner, but to show that each approach wins
on the kind of question that suits it.

No API key. Dependencies: pandas, scikit-learn. Reuses Lab 9-4 for the SQL.
Run generate_sample_data.py first.
"""

import importlib.util
import time
from pathlib import Path
from typing import Callable, Dict, List

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
XLSX = DATA / "Maintenance_Batteries.xlsx"

# Reuse the SQL Table-RAG of Lab 9-4.
_lab94 = Path(__file__).resolve().parent / "lab9-4_table_rag_sql.py"
_spec = importlib.util.spec_from_file_location("lab94", _lab94)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)


# ---------------------------------------------------------------------------
# The evaluation set: the question, its kind, and how the answer is checked
# ---------------------------------------------------------------------------
# Kind "search": a semantic question about one entity.
# Kind "calculation": a question of aggregation or filtering.
QUESTIONS = [
    # (question, kind, words expected in the answer)
    ("What is the recommended action for BAT005?", "search", ["shutdown", "replacement"]),
    ("Which workshop holds BAT003?", "search", ["assembly"]),
    ("What is the status of BAT002?", "search", ["replace"]),
    ("What is the voltage of BAT001?", "search", ["12.6"]),
    ("Which site hosts BAT007?", "search", ["southbank"]),
    ("How many batteries are to replace?", "calculation", ["2"]),
    ("What is the average voltage?", "calculation", ["11.8"]),
    ("What is the maximum temperature?", "calculation", ["45"]),
    ("How many batteries per site?", "calculation", ["southbank", "3"]),
    ("Which equipment has a voltage under 11.5?", "calculation", ["bat002", "bat005"]),
]


def check(answer: str, expected: List[str]) -> bool:
    r = answer.lower()
    return all(a.lower() in r for a in expected)


# ---------------------------------------------------------------------------
# Approach A — raw
# ---------------------------------------------------------------------------
def build_raw(df: pd.DataFrame) -> List[str]:
    """A realistic flattening: the header isolated, the values in misaligned chunks.

    As in Lab 9-1, the cut does not coincide with the rows, so no fragment holds
    a complete row: the relation is degraded.
    """
    header = " ".join(df.columns)
    values = [str(v) for _, row in df.iterrows() for v in row.values]
    fragments = [header]
    size = 5  # misaligned against the 8 columns
    for i in range(0, len(values), size):
        fragments.append(" ".join(values[i:i + size]))
    return fragments


# ---------------------------------------------------------------------------
# Approach B — verbalised
# ---------------------------------------------------------------------------
def build_verbalized(df: pd.DataFrame) -> List[str]:
    cols = list(df.columns)
    key = cols[0]
    sentences = []
    for _, row in df.iterrows():
        details = ", ".join(f"{c} = {row[c]}" for c in cols[1:])
        sentences.append(f"For {key} {row[key]}: {details}.")
    return sentences


def search_tfidf(fragments: List[str], question: str) -> str:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(fragments + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    return fragments[int(sims.argmax())]


def measure(name: str, answer_fn: Callable[[str], str]) -> Dict:
    """Measure the success rate by kind of question, and the total time."""
    results = {"search": [0, 0], "calculation": [0, 0]}  # [hits, total]
    t0 = time.perf_counter()
    for question, kind, expected in QUESTIONS:
        answer = answer_fn(question)
        results[kind][1] += 1
        if check(answer, expected):
            results[kind][0] += 1
    elapsed = time.perf_counter() - t0
    return {"name": name, "results": results, "ms": elapsed * 1000}


def main() -> None:
    print("=" * 78)
    print("Lab 9-5 — The arena of structures: a comparative benchmark")
    print("=" * 78)

    if not XLSX.exists():
        print("\nFile not found. Run this first: python generate_sample_data.py")
        return

    df = pd.read_excel(XLSX, sheet_name="Batteries")

    # Prepare the three approaches.
    raw = build_raw(df)
    verbalised = build_verbalized(df)
    conn = _mod.load_sqlite()
    columns = [r[1] for r in conn.execute(f"PRAGMA table_info({_mod.TABLE})").fetchall()]

    def ans_raw(q: str) -> str:
        return search_tfidf(raw, q)

    def ans_verbalised(q: str) -> str:
        return search_tfidf(verbalised, q)

    def ans_sql(q: str) -> str:
        result, _ = _mod.answer(conn, q, "offline", columns)
        return result

    measurements = [
        measure("A. Raw", ans_raw),
        measure("B. Verbalised", ans_verbalised),
        measure("C. Table-RAG (SQL)", ans_sql),
    ]

    print(f"\nA set of {len(QUESTIONS)} questions "
          f"({sum(1 for _,t,_ in QUESTIONS if t=='search')} search, "
          f"{sum(1 for _,t,_ in QUESTIONS if t=='calculation')} calculation).")

    print("\n" + "=" * 78)
    print("RESULTS")
    print("=" * 78)
    print(f"{'Approach':20s} | {'search':>10s} | {'calculation':>12s} | {'time':>9s}")
    print("-" * 78)
    for m in measurements:
        r = m["results"]
        srch = f"{r['search'][0]}/{r['search'][1]}"
        calc = f"{r['calculation'][0]}/{r['calculation'][1]}"
        print(f"{m['name']:20s} | {srch:>10s} | {calc:>12s} | {m['ms']:>7.1f}ms")

    print("\n" + "=" * 78)
    print("HOW TO READ THIS")
    print("=" * 78)
    print("- On SEARCH questions, about an entity, verbalisation dominates: it places")
    print("  each row on the map of meaning.")
    print("- On CALCULATION questions, totals and filters, only Table-RAG answers right:")
    print("  semantic approximation cannot count.")
    print("- Raw loses on almost everything: the worst representation, bar tiny cases.")

    print("\nWHAT TO REMEMBER")
    print("- There is no single winner: the right approach depends on the kind of question.")
    print("- A good architect routes: search to verbalised RAG, calculation to a structured query.")
    print("- To measure is to decide: the benchmark replaces intuition with figures.")

    conn.close()


if __name__ == "__main__":
    main()
