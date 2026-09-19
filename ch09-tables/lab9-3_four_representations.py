# -*- coding: utf-8 -*-
"""
Lab 9-3 — Four ways to represent a table (the technical heart)

Learning objective
------------------
Choose, among four strategies, the representation suited to a business table.
The chapter ranks them from the worst to the finest:

  1. Raw table: flattened into text. Wrong as soon as the header detaches.
  2. Row -> sentence: each row verbalised, re-injecting the headers. The
     relation destroyed by flattening is rebuilt. In most cases this is the
     best approach.
  3. Chunk per row: one row is one fragment, headers in the metadata. Useful
     when each row is a rich, filterable entity.
  4. Chunk per column: grouped by column, for crossing questions — "the
     distribution of ...", "the list of ...".

All four are applied to one table, then a small retrieval test (TF-IDF) shows
that the representation chosen changes the answer, according to the kind of
question asked.

No API key. Dependencies: pandas, scikit-learn.
Run generate_sample_data.py first, and ideally Lab 9-2.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"


# ---------------------------------------------------------------------------
# The four representations
# ---------------------------------------------------------------------------
def repr_raw(df: pd.DataFrame) -> List[str]:
    """Approach 1 — the table flattened into text, a single fragment."""
    header = " ".join(df.columns)
    body = " ".join(str(v) for _, row in df.iterrows() for v in row.values)
    return [header + " " + body]


def repr_row_sentence(df: pd.DataFrame) -> List[str]:
    """Approach 2 — each row verbalised into a self-contained sentence."""
    cols = list(df.columns)
    key = cols[0]  # the first column identifies the entity
    sentences = []
    for _, row in df.iterrows():
        subject = f"{key} {row[key]}"
        details = ", ".join(f"{c} = {row[c]}" for c in cols[1:])
        sentences.append(f"For {subject}: {details}.")
    return sentences


def repr_chunk_row(df: pd.DataFrame) -> List[Dict]:
    """Approach 3 — one row is one fragment, headers in the metadata."""
    cols = list(df.columns)
    chunks = []
    for _, row in df.iterrows():
        chunks.append({
            "content": " ".join(f"{c}: {row[c]}" for c in cols),
            "metadata": {c: _val(row[c]) for c in cols},
        })
    return chunks


def repr_chunk_column(df: pd.DataFrame) -> List[Dict]:
    """Approach 4 — one fragment per column, for crossing analysis."""
    chunks = []
    for c in df.columns:
        values = [str(v) for v in df[c].tolist()]
        # The column name is repeated, to anchor the meaning of the whole width.
        content = (f"Column {c}. List of the values of {c}: "
                   + ", ".join(values) + ".")
        chunks.append({
            "content": content,
            "metadata": {"column": c, "n_values": len(values)},
        })
    return chunks


def _val(v):
    if pd.isna(v):
        return None
    return v.item() if hasattr(v, "item") else v


# ---------------------------------------------------------------------------
# A small retrieval test (TF-IDF) over a list of text fragments
# ---------------------------------------------------------------------------
def search(fragments: List[str], question: str) -> Tuple[str, float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(fragments + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return fragments[idx], float(sims[idx])


def main() -> None:
    print("=" * 78)
    print("Lab 9-3 — Four ways to represent a table")
    print("=" * 78)

    hr = DATA / "hr_leave.csv"
    if not hr.exists():
        print("\nData not found. Run this first: python generate_sample_data.py")
        return

    df = pd.read_csv(hr)
    print(f"\nClaire's HR table: {len(df)} members of staff.")

    # The four representations.
    raw = repr_raw(df)
    sentences = repr_row_sentence(df)
    row_chunks = repr_chunk_row(df)
    column_chunks = repr_chunk_column(df)

    print("\n--- Approach 1: the raw table, 1 fragment ---")
    print(f"  \"{raw[0][:90]}…\"")

    print("\n--- Approach 2: row -> sentence ---")
    for p in sentences[:2]:
        print(f"  {p}")
    print("  ...")

    print("\n--- Approach 3: chunk per row (content plus metadata) ---")
    print(f"  content : {row_chunks[0]['content']}")
    print(f"  metadata: {row_chunks[0]['metadata']}")

    print("\n--- Approach 4: chunk per column ---")
    for c in column_chunks[:2]:
        print(f"  {c['content'][:80]}…")
    print("  ...")

    # --- The test: an ENTITY question against a CROSSING question ---
    print("\n" + "=" * 78)
    print("THE RETRIEVAL TEST: the representation changes the answer")
    print("=" * 78)

    q_entity = "How many days of leave does Alice have?"
    q_crossing = "List of the Staff column."

    print(f"\nAn ENTITY question: \"{q_entity}\"")
    frag_raw, s1 = search(raw, q_entity)
    frag_sentence, s2 = search(sentences, q_entity)
    print(f"  raw           -> \"{frag_raw[:60]}…\" (score {s1:.2f})")
    print(f"  row->sentence -> \"{frag_sentence[:60]}…\" (score {s2:.2f})")
    sentence_ok = "Alice" in frag_sentence and "25" in frag_sentence
    print(f"  => verbalisation isolates the right row: {'YES' if sentence_ok else 'no'}")

    print(f"\nA CROSSING question: \"{q_crossing}\"")
    column_texts = [c["content"] for c in column_chunks]
    frag_col, s3 = search(column_texts, q_crossing)
    print(f"  column chunk  -> \"{frag_col[:60]}…\" (score {s3:.2f})")
    # The right chunk is the one listing the staff, so it holds the first names.
    col_ok = "Alice" in frag_col and "Bruno" in frag_col
    print(f"  => the column chunk brings back the whole list: {'YES' if col_ok else 'no'}")

    print("\n" + "=" * 78)
    print("THE FOUR APPROACHES, SIDE BY SIDE")
    print("=" * 78)
    print(f"{'Approach':18s} | {'Strength':28s} | when to use it")
    print("-" * 78)
    rows = [
        ("Raw table", "Immediate", "small tables only"),
        ("Row->sentence", "Findable, natural", "the general case"),
        ("Chunk per row", "Filterable, structured", "rich row-entities"),
        ("Chunk per column", "Crossing analysis", "questions about one quantity"),
    ]
    for approach, strength, usage in rows:
        print(f"{approach:18s} | {strength:28s} | {usage}")

    print("\nWHAT TO REMEMBER")
    print("- There is no one good representation, but one per kind of question.")
    print("- Verbalisation, row to sentence, is the best default choice.")
    print("- The column chunk shines on crossing questions, where the others fail.")


if __name__ == "__main__":
    main()
