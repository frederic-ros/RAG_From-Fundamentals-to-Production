# -*- coding: utf-8 -*-
"""
Lab 10-5 — Building a mini Vision-RAG (the synthesis)

Learning objective
------------------
Carry out the synthesis of the chapter: a complete pipeline that answers a
question from information taken out of VISUAL documents. The chain is the
familiar one of the book — only the first step changes. A vision model
interprets the images, and then everything becomes a JSON document again, then
fragments, then embeddings, then a search.

    page-image -> vision -> JSON document -> fragments -> embeddings -> answer

The descriptions of the plan and of the chart (Lab 10-4) are indexed, and
questions are answered whose answer was NEVER written down: "what is the sensor
wired to?", "was there a temperature peak?".

Hybrid mode: an "in-house" vector search (TF-IDF, no dependency) by default; the
visual descriptions come from offline mode or from Ollama (Labs 10-2 and 10-3).
No API key. Run generate_sample_docs.py first.
"""

import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple

DOCS = Path(__file__).resolve().parent / "sample_docs"


def _load_module(file_name: str):
    path = Path(__file__).resolve().parent / file_name
    spec = importlib.util.spec_from_file_location(file_name.replace("-", "_")[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. Build the fragments from the multimodal JSON document
# ---------------------------------------------------------------------------
def build_fragments() -> List[Dict]:
    lab4 = _load_module("lab10-4_document_to_json.py")
    doc = lab4.build_documentary_json()

    fragments = []
    for s in doc["sections"]:
        fragments.append({"content": f"{s['title']}. {s['text']}",
                          "source": s["source"], "type": "text"})
    for f in doc["figures"]:
        # Each described figure becomes an indexable fragment.
        content = f"{f['title']}. {f['description']}"
        fragments.append({"content": content, "source": f["source"], "type": f["type"]})
    return fragments


# ---------------------------------------------------------------------------
# 2. The in-house vector search (TF-IDF plus a cosine)
# ---------------------------------------------------------------------------
def search_for(fragments: List[Dict], question: str) -> Tuple[Dict, float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    corpus = [f["content"] for f in fragments]
    vec = TfidfVectorizer()
    mat = vec.fit_transform(corpus + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return fragments[idx], float(sims[idx])


def main() -> None:
    print("=" * 78)
    print("Lab 10-5 — Building a mini Vision-RAG (the synthesis)")
    print("=" * 78)

    if not DOCS.exists():
        print("\nImages not found. Run this first: python generate_sample_docs.py")
        return

    fragments = build_fragments()
    print(f"\nFragments indexed: {len(fragments)}")
    for f in fragments:
        print(f"  - [{f['type']}] {f['content'][:64]}… ({f['source']})")

    questions = [
        "What is the temperature sensor wired to?",
        "Was there a temperature peak during the day?",
        "What voltage was measured on the line 4 battery?",
    ]

    print("\n" + "=" * 78)
    print("THE VISION-RAG ANSWERS")
    print("=" * 78)
    for question in questions:
        frag, score = search_for(fragments, question)
        print(f"\nQ: {question}")
        print(f"   source found: {frag['source']} (type {frag['type']}, score {score:.2f})")
        print(f"   excerpt: {frag['content'][:100]}…")

    print("\n" + "=" * 78)
    print("WHAT THE MINI VISION-RAG DOES")
    print("=" * 78)
    print("- It answers from documents that were never text.")
    print("- The sensor question finds its answer in the description of the plan.")
    print("- The peak question finds its answer in the description of the chart.")
    print("- The chain is the same as everywhere: only the first step, vision, changes.")

    print("\nWHAT TO REMEMBER")
    print("- Vision-RAG is where the ingestion part arrives: no format now resists")
    print("  entry into the system.")
    print("- The vision model does not add a parallel chain: it feeds the same one.")
    print("- Once described, an image is searched like any other text.")


if __name__ == "__main__":
    main()
