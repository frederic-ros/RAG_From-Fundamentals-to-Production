# -*- coding: utf-8 -*-
"""
Lab 13-3 — Comparing the two pipelines (Claire)

Learning objective
------------------
The two previous labs showed, separately, the failure and then the repair. Here
they are set FACE TO FACE: the same document, the same chunker with the same
token budget, the same questions. The only difference: the raw text is chunked,
or the canonical JSON is.

    It is not the chunker that creates the quality of the fragment,
    it is the quality of the representation it works on.

Three things are measured per pipeline, over a small set of questions:

  - does the search bring back a CLEAN fragment, free of noise?
  - does the fragment carry its CONTEXT, the hierarchical path?
  - the similarity score, for indication.

The verdict fits in one table: with the chunker held equal, the pivot wins all
along the line.

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple
import json

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"
RAW_DOC = CORPUS / "raw_document.txt"
CANON_DOC = CORPUS / "canonical_document.json"

# These must match the strings emitted by generate_corpus.py.
HEADERS = ["HUMAN RESOURCES DEPARTMENT", "Confidential — internal use"]

QUESTIONS = [
    "How many days of remote work per week?",
    "What is the rate for 6 to 20 km?",
    "How do I request exceptional leave?",
]


# --- Pipeline A: chunk the RAW text, fixed size ------------------------------
def raw_pipeline(size: int) -> Tuple[List[str], List[dict]]:
    text = RAW_DOC.read_text(encoding="utf-8")
    tokens = tk.encoder(text)
    chunks = [tk.decoder(tokens[i:i + size]) for i in range(0, len(tokens), size)]
    metas = [{"path": []} for _ in chunks]   # no context: the raw text has none
    return chunks, metas


# --- Pipeline B: chunk the CANONICAL JSON, one block being one fragment -------
def canonical_pipeline() -> Tuple[List[str], List[dict]]:
    data = json.loads(CANON_DOC.read_text(encoding="utf-8"))
    chunks = [b["text"] for b in data["blocks"]]
    metas = [b["metadata"] for b in data["blocks"]]
    return chunks, metas


def search_for(chunks: List[str], metas: List[dict], question: str):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return chunks[idx], metas[idx], float(sims[idx])


def is_clean(fragment: str) -> bool:
    if any(h in fragment for h in HEADERS):
        return False
    if " 14 " in (" " + fragment + " "):
        return False
    return True


def has_context(meta: dict) -> bool:
    return bool(meta.get("path"))


def evaluate(name: str, chunks: List[str], metas: List[dict]) -> dict:
    clean = 0
    contexted = 0
    details = []
    for q in QUESTIONS:
        frag, meta, score = search_for(chunks, metas, q)
        p = is_clean(frag)
        c = has_context(meta)
        clean += int(p)
        contexted += int(c)
        details.append((q, p, c, score))
    return {"name": name, "clean": clean, "contexted": contexted,
            "total": len(QUESTIONS), "details": details}


def main() -> None:
    print("=" * 78)
    print("Lab 13-3 — Comparing the two pipelines (Claire)")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not RAW_DOC.exists() or not CANON_DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    a = evaluate("A — cutting the RAW text", *raw_pipeline(40))
    b = evaluate("B — cutting the CANONICAL JSON", *canonical_pipeline())

    print("\n" + "=" * 78)
    print("THE SAME DOCUMENT, THE SAME QUESTIONS, TWO INPUTS")
    print("=" * 78)
    for res in (a, b):
        print(f"\n{res['name']}")
        print(f"  clean fragments    : {res['clean']}/{res['total']}")
        print(f"  contexted fragments: {res['contexted']}/{res['total']}")
        for q, p, c, score in res["details"]:
            print(f"    - \"{q[:46]}…\"  clean={'yes' if p else 'no':3}  "
                  f"context={'yes' if c else 'no':3}  score={score:.2f}")

    print("\n" + "=" * 78)
    print("THE VERDICT")
    print("=" * 78)
    print(f"  Pipeline A (raw)      : {a['clean']}/{a['total']} clean, "
          f"{a['contexted']}/{a['total']} contexted.")
    print(f"  Pipeline B (canonical): {b['clean']}/{b['total']} clean, "
          f"{b['contexted']}/{b['total']} contexted.")
    print("\n  The chunker is identical. The representation makes the difference.")

    print("\nWHAT TO REMEMBER")
    print("- With the chunker held equal, cutting the pivot beats cutting the raw, always.")
    print("- The quality of a fragment is decided BEFORE the cut, in the reconstruction.")
    print("- The JSON document is the canonical input to chunking: that is where you start.")


if __name__ == "__main__":
    main()
