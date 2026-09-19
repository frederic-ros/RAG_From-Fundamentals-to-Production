# -*- coding: utf-8 -*-
"""
Lab 9-4 — Table-RAG: when RAG is no longer the right answer (Claire)

Learning objective
------------------
Recognise the frontier. Questions of CALCULATION — totals, filters,
aggregations — are not a matter of semantic resemblance but of a structured
query. Rather than vectorising the table, it is loaded into an in-memory SQL
database (SQLite) and the question is translated into SQL. The answer is then
EXACT, not approximate.

    Not all data should become embeddings.
    Some should stay structured, and be queried as such.

Two modes for the question-to-SQL translation, chosen automatically:

  1. OFFLINE (the default): a rule-based, deterministic translator. Nothing to
     install.
  2. LOCAL (Ollama): a local LLM generates the SQL. Activated if Ollama answers.

To force a mode: set LAB_MODE to offline or local.

No API key. Dependencies: pandas (sqlite3 is in the standard library).
Run generate_sample_data.py first.
"""

import json
import os
import re
import sqlite3
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
XLSX = DATA / "Maintenance_Batteries.xlsx"

OLLAMA_TAGS = "http://localhost:11434/api/tags"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_LLM", "llama3.2")

TABLE = "batteries"


# ---------------------------------------------------------------------------
# Loading the table into an in-memory SQL database
# ---------------------------------------------------------------------------
def load_sqlite() -> sqlite3.Connection:
    df = pd.read_excel(XLSX, sheet_name="Batteries")
    conn = sqlite3.connect(":memory:")
    df.to_sql(TABLE, conn, index=False, if_exists="replace")
    return conn


# ---------------------------------------------------------------------------
# Question to SQL, OFFLINE mode: deterministic rules
# ---------------------------------------------------------------------------
def question_to_sql_offline(question: str) -> Optional[str]:
    q = question.lower()

    # A count, with a condition on the status.
    if ("how many" in q or "count" in q) and "replace" in q:
        return f"SELECT COUNT(*) FROM {TABLE} WHERE Status = 'To replace';"
    if ("how many" in q or "count" in q) and "critical" in q:
        return f"SELECT COUNT(*) FROM {TABLE} WHERE Status = 'Critical';"
    # An average of the voltage.
    if ("average" in q or "mean" in q) and "voltage" in q:
        return f"SELECT ROUND(AVG(Voltage_V), 2) FROM {TABLE};"
    # The maximum temperature.
    if ("max" in q or "highest" in q or "maximum" in q) and "temp" in q:
        return f"SELECT MAX(Temperature_C) FROM {TABLE};"
    # The list of equipment to replace.
    if ("which" in q or "list" in q) and "replace" in q:
        return f"SELECT Equipment FROM {TABLE} WHERE Status = 'To replace';"
    # A count per site.
    if "per site" in q or "by site" in q or ("how many" in q and "site" in q):
        return f"SELECT Site, COUNT(*) FROM {TABLE} GROUP BY Site;"
    # Equipment whose voltage is below a threshold.
    m = re.search(r"voltage.*(?:under|below|less than)\s*(\d+(?:[.,]\d+)?)", q)
    if m:
        threshold = m.group(1).replace(",", ".")
        return f"SELECT Equipment, Voltage_V FROM {TABLE} WHERE Voltage_V < {threshold};"
    return None


# ---------------------------------------------------------------------------
# Question to SQL, LOCAL mode (Ollama)
# ---------------------------------------------------------------------------
def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def question_to_sql_local(question: str, columns) -> Optional[str]:
    schema = ", ".join(columns)
    prompt = (
        "Translate the question into ONE SQLite SQL query, with no explanation. "
        f"The table \"{TABLE}\" has the columns: {schema}. "
        "Answer with the SQL query alone, ending in a semicolon.\n"
        f"Question: {question}"
    )
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = json.loads(r.read().decode("utf-8")).get("response", "")
        m = re.search(r"(SELECT .+?;)", text, re.IGNORECASE | re.DOTALL)
        return m.group(1) if m else None
    except Exception:
        return None


def choose_mode() -> str:
    force = os.environ.get("LAB_MODE", "").lower()
    if force in {"offline", "local"}:
        return force
    return "local" if ollama_available() else "offline"


def is_sql_safe(sql: str) -> bool:
    """The guard rail: only simple SELECTs are executed."""
    s = sql.strip().lower()
    forbidden = ("insert", "update", "delete", "drop", "alter", "attach", ";--")
    return s.startswith("select") and not any(word in s for word in forbidden)


def answer(conn: sqlite3.Connection, question: str, mode: str, columns) -> Tuple[str, str]:
    sql = (question_to_sql_local(question, columns) if mode == "local"
           else question_to_sql_offline(question))
    if sql is None:
        sql = question_to_sql_offline(question)  # the fallback
    if sql is None:
        return "(no query generated)", ""
    if not is_sql_safe(sql):
        return "(query rejected by the guard rail)", sql
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        return str(rows), sql
    except Exception as e:
        return f"(SQL error: {e})", sql


def main() -> None:
    print("=" * 78)
    print("Lab 9-4 — Table-RAG: when RAG is no longer the right answer (Claire)")
    print("=" * 78)

    if not XLSX.exists():
        print("\nFile not found. Run this first: python generate_sample_data.py")
        return

    conn = load_sqlite()
    columns = [r[1] for r in conn.execute(f"PRAGMA table_info({TABLE})").fetchall()]
    mode = choose_mode()
    print(f"\nQuestion-to-SQL translation mode: {mode}")
    print(f"Table \"{TABLE}\" loaded in memory ({', '.join(columns)}).")

    questions = [
        "How many batteries are to replace?",
        "What is the average voltage?",
        "What is the maximum temperature?",
        "How many batteries per site?",
        "Which equipment has a voltage under 11.5?",
    ]

    print("\n" + "=" * 78)
    print("EXACT ANSWERS FROM A STRUCTURED QUERY")
    print("=" * 78)
    for question in questions:
        result, sql = answer(conn, question, mode, columns)
        print(f"\nQ: {question}")
        print(f"   SQL: {sql}")
        print(f"   ->  {result}")

    # A comparison with what a vector RAG cannot do.
    print("\n" + "=" * 78)
    print("WHY NOT VECTOR RAG?")
    print("=" * 78)
    print("The question \"how many batteries are to replace?\" is a CALCULATION: it needs")
    print("rows counted, not a resembling passage found. A vector RAG would bring back")
    print("nearby fragments, but would not know how to add them up. The structured query")
    print("answers exactly, quickly, and in a way that can be checked.")

    print("\nWHAT TO REMEMBER")
    print("- Calculation questions — totals, filters, aggregations — call for SQL, not embeddings.")
    print("- The LLM does not calculate: it translates the question into a query. The database calculates.")
    print("- A guard rail allows only SELECTs: arbitrary SQL is never executed.")

    conn.close()


if __name__ == "__main__":
    main()
