# -*- coding: utf-8 -*-
"""
Lab 9-1 — The demonstration of the disaster: linear flattening (Julien)

Learning objective
------------------
See for yourself, in practice, the destruction of relational information that a
naive parser causes. Julien's maintenance table is flattened into continuous
text, indexed in a vector store, and then asked a crossed question — a row
against a column. The system fails: the embedding has mixed the rows and the
columns together.

    A cell holds a value. A table holds a relation.
    Flattening the table destroys the relation.

Three search engines to choose from, detected automatically, to show that the
failure comes not from the engine but from the representation:

  1. in-house : TF-IDF plus a cosine (zero dependency);
  2. faiss    : if faiss-cpu is installed;
  3. chroma   : if chromadb is installed (embeddings supplied, no download).

No API key. Run generate_sample_data.py first.
"""

import importlib.util
from pathlib import Path
from typing import List, Tuple

import pandas as pd

DATA = Path(__file__).resolve().parent / "data"
XLSX = DATA / "Maintenance_Batteries.xlsx"


# ---------------------------------------------------------------------------
# Level 1 — flattening the table linearly into continuous text
# ---------------------------------------------------------------------------
def flatten_table(df: pd.DataFrame) -> List[str]:
    """Flatten the table "by the mile", the way a raw text extractor would.

    This faithfully simulates a naive parser: the header is extracted ONCE, at
    the top of the document, and then all the values follow one another without
    repeating the column. The chunking is blind to the structure — its size does
    not coincide with the rows, so a value ends up separated from its header and
    sometimes from its equipment. That is exactly what destroys the row-by-column
    relation.
    """
    header = " ".join(df.columns)
    values = []
    for _, row in df.iterrows():
        values.extend(str(v) for v in row.values)

    # The header forms its own fragment, like an isolated title line.
    fragments = [header]
    # A deliberately misaligned cut: 5 does not divide the number of columns.
    size = 5
    for i in range(0, len(values), size):
        fragments.append(" ".join(values[i:i + size]))
    return fragments


# ---------------------------------------------------------------------------
# Vector search: three engines
# ---------------------------------------------------------------------------
def _tfidf(corpus: List[str], question: str):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer()
    mat = vec.fit_transform(corpus + [question])
    return mat[:-1], mat[-1]


def homemade_search(corpus: List[str], question: str) -> Tuple[int, float]:
    from sklearn.metrics.pairwise import cosine_similarity
    docs, q = _tfidf(corpus, question)
    sims = cosine_similarity(q, docs)[0]
    idx = int(sims.argmax())
    return idx, float(sims[idx])


def search_faiss(corpus: List[str], question: str) -> Tuple[int, float]:
    import faiss
    docs, q = _tfidf(corpus, question)
    docs = docs.toarray().astype("float32")
    q = q.toarray().astype("float32")
    faiss.normalize_L2(docs)
    faiss.normalize_L2(q)
    index = faiss.IndexFlatIP(docs.shape[1])
    index.add(docs)
    scores, idx = index.search(q, 1)
    return int(idx[0][0]), float(scores[0][0])


def search_chroma(corpus: List[str], question: str) -> Tuple[int, float]:
    import chromadb
    docs, q = _tfidf(corpus, question)
    docs = docs.toarray().tolist()
    q = q.toarray()[0].tolist()
    client = chromadb.Client()
    name = "lab91_" + str(abs(hash(" ".join(corpus))) % 100000)
    try:
        client.delete_collection(name)
    except Exception:
        pass
    col = client.create_collection(name, metadata={"hnsw:space": "cosine"})
    col.add(ids=[f"c{i}" for i in range(len(corpus))], embeddings=docs, documents=corpus)
    res = col.query(query_embeddings=[q], n_results=1)
    doc = res["documents"][0][0]
    return corpus.index(doc), 1.0 - res["distances"][0][0]


def available_engines():
    engines = [("in-house", homemade_search)]
    if importlib.util.find_spec("faiss") is not None:
        engines.append(("faiss", search_faiss))
    if importlib.util.find_spec("chromadb") is not None:
        engines.append(("chroma", search_chroma))
    return engines


def main() -> None:
    print("=" * 78)
    print("Lab 9-1 — The demonstration of the disaster: linear flattening (Julien)")
    print("=" * 78)

    if not XLSX.exists():
        print("\nFile not found. Run this first: python generate_sample_data.py")
        return

    df = pd.read_excel(XLSX, sheet_name="Batteries")
    print(f"\nJulien's table: {len(df)} pieces of equipment, {len(df.columns)} columns.")
    print("Columns:", ", ".join(df.columns))

    fragments = flatten_table(df)
    print(f"\nAfter flattening \"by the mile\": {len(fragments)} blind fragments.")
    print("A sample fragment:")
    print(f"  \"{fragments[1]}\"")

    # The crossed question: tie a column value back to its equipment.
    question = "Which equipment runs at a voltage of 11.4 volts?"
    # The truth: Voltage_V = 11.4 -> BAT002.
    true_equipment = "BAT002"
    true_value = "11.4"
    target_row = df[df["Equipment"] == true_equipment].iloc[0]
    print(f"\nThe crossed question: \"{question}\"")
    print(f"Expected answer (row x column): {true_equipment}, at {true_value} V")

    print("\n" + "=" * 78)
    print("THE RESULT OF VECTOR SEARCH OVER THE FLATTENED TABLE")
    print("=" * 78)
    print(f"{'Engine':10s} | does the fragment tie 11.4 V to the right equipment?")
    print("-" * 78)

    for name, function in available_engines():
        idx, score = function(fragments, question)
        fragment = fragments[idx]
        # To answer, the fragment must hold BOTH the equipment and its value, AND
        # make it possible to know that 11.4 is a VOLTAGE — the header present.
        has_equipment = true_equipment in fragment
        has_value = true_value in fragment
        has_voltage_header = "Voltage_V" in fragment
        ties = has_equipment and has_value and has_voltage_header
        verdict = "YES" if ties else "NO — the relation is lost"
        print(f"{name:10s} | {verdict}")
        print(f"           fragment: \"{fragment[:62]}…\"")

    print("\n" + "=" * 78)
    print("ANATOMY OF THE FAILURE")
    print("=" * 78)
    print(f"The real target row is: {dict(target_row)}")
    print("After flattening, the header \"Voltage_V\" sits alone at the top of the")
    print("document, far from the values. The fragment holding \"11.4\" no longer says")
    print("that this is a VOLTAGE, nor always which equipment it belongs to: the")
    print("row-by-column relation has been destroyed by the naive parsing.")

    print("\nWHAT TO REMEMBER")
    print("- Flattening a table turns it into a run of values with no relations.")
    print("- No vector store recovers a relation that the flattening has destroyed.")
    print("- The failure comes from the REPRESENTATION, not the engine: the next labs fix it.")


if __name__ == "__main__":
    main()
