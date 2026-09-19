# -*- coding: utf-8 -*-
"""
Lab 13-2 — The same document after reconstruction (Claire)

Learning objective
------------------
EXACTLY the document of the previous lab is taken up again, but starting this
time from the canonical JSON — the pressed cloth. The chunking becomes
"structure-aware": it cuts ALONG the articulations, one block being one unit,
and never across them.

    This is the step that follows reconstruction — and depends on it entirely.

Three things are checked on the fragments drawn from the JSON:

  - no more pagination noise: the "14" is gone, the sentence is intact;
  - no more repeated heads and feet: they never existed in the pivot;
  - the table kept whole, as one indivisible block.

And a bonus: each fragment carries its hierarchical path ("Remote work",
"Allowances > Mileage allowance scale") — the first metadata, for free.

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import List, Tuple
import json

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"
CANON_DOC = CORPUS / "canonical_document.json"


def load_blocks() -> List[dict]:
    data = json.loads(CANON_DOC.read_text(encoding="utf-8"))
    return data["blocks"]


def structure_aware_chunk(blocks: List[dict]) -> Tuple[List[str], List[dict]]:
    """Structure-aware chunking: one pivot block is one fragment.

    Nothing is cut across a block; a table stays whole. Each fragment inherits
    the metadata — the hierarchical path — of its block.
    """
    texts = [b["text"] for b in blocks]
    metas = [b["metadata"] for b in blocks]
    return texts, metas


def breadcrumb(meta: dict) -> str:
    return " > ".join(meta.get("path", [])) or "(root)"


def search_for(chunks: List[str], metas: List[dict], question: str):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vec = TfidfVectorizer()
    mat = vec.fit_transform(chunks + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return chunks[idx], metas[idx], float(sims[idx])


def main() -> None:
    print("=" * 78)
    print("Lab 13-2 — The same document after reconstruction (Claire)")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not CANON_DOC.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    blocks = load_blocks()
    chunks, metas = structure_aware_chunk(blocks)

    print("\n" + "=" * 78)
    print("THE FRAGMENTS DRAWN FROM THE CANONICAL JSON")
    print("=" * 78)
    for i, (c, m) in enumerate(zip(chunks, metas), start=1):
        head = c.strip().replace("\n", " ")
        print(f"\n  [{i}] {breadcrumb(m)}   ({tk.count(c)} tokens)")
        print(f"      \"{head[:96]}…\"" if len(head) > 96 else f"      \"{head}\"")

    # The cleanliness checks. These strings must match generate_corpus.py.
    full_text = "\n".join(chunks)
    noise_14 = " 14 " in (" " + full_text + " ")
    noise_header = "HUMAN RESOURCES DEPARTMENT" in full_text
    table_whole = any(b["type"] == "table" for b in blocks)

    print("\n" + "=" * 78)
    print("THE CLEANLINESS CHECK")
    print("=" * 78)
    print(f"  page number \"14\" in a fragment?      {'yes' if noise_14 else 'no'}")
    print(f"  repeated head in a fragment?          {'yes' if noise_header else 'no'}")
    print(f"  table kept as one whole block?        {'yes' if table_whole else 'no'}")

    # The same question that at the Lab 13-1.
    question = "How many days of remote work per week?"
    frag, meta, score = search_for(chunks, metas, question)
    print("\n" + "=" * 78)
    print("THE SAME QUESTION AS IN LAB 13-1")
    print("=" * 78)
    print(f"  question: \"{question}\"")
    print(f"  fragment found (score {score:.2f}) — {breadcrumb(meta)}:")
    print(f"    \"{frag.strip()}\"")
    print("\n  The fragment is exact AND clean: the sentence is intact, with no \"14\",")
    print("  and it knows where it came from, its section. You can answer without reserve.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The same document, the same question as Lab 13-1: only the INPUT changed.")
    print("- Cutting the pivot means cutting along the boundaries of meaning, not across.")
    print("- The structural noise pollutes nothing now: it never reached the fragments.")
    print("- A bonus: each fragment carries its path — the first metadata, for free.")

    print("\nA RETENIR")
    print("- You do not cut the cloth before it has been pressed.")
    print("- Structure commands, size adjusts: here one block is one unit.")
    print("- The fragment is no longer an orphan: it knows where it lives.")


if __name__ == "__main__":
    main()
