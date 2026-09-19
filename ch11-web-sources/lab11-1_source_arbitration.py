# -*- coding: utf-8 -*-
"""
Lab 11-1 — Multi-source merging and version arbitration (Sophie)

Learning objective
------------------
Where the ingestion chain of Chapters 8 to 10 arrives: merge sources of different
formats — a local PDF, a web page — into a common set of chunks, and then run a
search across them. But a difficulty specific to live sources appears: when the
web and a local document CONTRADICT each other, which one carries authority?

    Noise is not only visual, a menu in the way. It is also logical: an
    obsolete piece of information. Each fragment is dated, and the freshest
    version prevails.

The scenario: an internal PDF of 2024 says the rate is 4.2%. A web page of 2026,
cleaned in Lab 11-2, says 4.7%. The system must mute the stale fragment.

A NOTE ON THE KEYWORDS. The arbitration keys on a subject word found in the
content ("rate"), and the freshness check looks for the literal string "4.7".
Both must stay in step with the English fixtures of generate_fixtures.py. In the
French edition these were "taux" and "4,7"; left untranslated against an English
corpus they match nothing, no arbitration happens, and the lab quietly reports
the stale PDF as the answer.

No API key. Reuses Lab 11-2 for the web cleaning.
Run generate_fixtures.py first.
"""

import importlib.util
import json
from pathlib import Path
from typing import Dict, List, Tuple

FIX = Path(__file__).resolve().parent / "fixtures"


def _load_lab(file_name: str):
    path = Path(__file__).resolve().parent / file_name
    spec = importlib.util.spec_from_file_location(file_name[:-3].replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pdf_fragment() -> Dict:
    """Load the already-ingested "local PDF" fragment, dated 2024."""
    return json.loads((FIX / "rule_pdf_2024.json").read_text(encoding="utf-8"))


def web_fragment() -> Dict:
    """Clean the 2026 web page through Lab 11-2 and make a dated fragment of it."""
    lab2 = _load_lab("lab11-2_clean_web_page.py")
    pivot = lab2.clean_page("rule_page_v2.html")
    # Extract the sentence carrying the rate.
    sentence = next((s["text"] for s in pivot["sections"]
                     if "applicable rate is" in s["text"]),
                    pivot["text"])
    return {
        "id": "web_rule_2026",
        "content": sentence,
        "metadata": {
            "source_type": "web",
            "title": pivot["title"],
            "date": "2026-06-01",
            "status": "online",
        },
    }


def merge(fragments: List[Dict]) -> List[Dict]:
    """Build the unified corpus: chunks from different formats."""
    corpus = []
    for i, f in enumerate(fragments, 1):
        corpus.append({
            "chunk_id": f"CHUNK_{i:03d}",
            "content": f["content"],
            "metadata": dict(f["metadata"], fragment_id=f["id"]),
        })
    return corpus


def arbitrate_versions(corpus: List[Dict], subject: str) -> Tuple[List[Dict], List[Dict]]:
    """On one subject the most recent version prevails; the others are muted.

    Returns (active, muted).

    The subject word must appear in the content of the fragments. If it does
    not — the classic failure when the corpus is translated and this argument
    is not — then no fragment is concerned, no arbitration happens, and the
    function silently returns the corpus untouched.
    """
    # The fragments speaking of the subject: here, the "rate".
    concerned = [c for c in corpus if subject in c["content"].lower()]
    others = [c for c in corpus if c not in concerned]
    if len(concerned) <= 1:
        return corpus, []
    # The most recent, by the date in the metadata.
    concerned.sort(key=lambda c: c["metadata"].get("date", ""), reverse=True)
    winner = concerned[0]
    stale = concerned[1:]
    for c in stale:
        c["metadata"]["status"] = "obsolete"
        c["metadata"]["muted"] = True
    active = others + [winner]
    return active, stale


def search_for(corpus: List[Dict], question: str) -> Tuple[Dict, float]:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    texts = [c["content"] for c in corpus]
    vec = TfidfVectorizer()
    mat = vec.fit_transform(texts + [question])
    sims = cosine_similarity(mat[-1], mat[:-1])[0]
    idx = int(sims.argmax())
    return corpus[idx], float(sims[idx])


def main() -> None:
    print("=" * 78)
    print("Lab 11-1 — Multi-source merging and version arbitration (Sophie)")
    print("=" * 78)

    if not FIX.exists():
        print("\nFixtures not found. Run this first: python generate_fixtures.py")
        return

    # 1. Gather fragments of different formats.
    pdf = pdf_fragment()
    web = web_fragment()
    print("\n--- Heterogeneous sources merged ---")
    print(f"  Local PDF (2024): \"{pdf['content']}\"")
    print(f"  Web page (2026) : \"{web['content'][:70]}…\"")

    corpus = merge([pdf, web])

    # 2. The cross-source search BEFORE arbitration: the conflict is visible.
    question = "What is the rate applicable to compliance files?"
    print("\n" + "=" * 78)
    print("THE CROSS-SOURCE SEARCH (before arbitration)")
    print("=" * 78)
    print(f"Question: {question}")
    print("The corpus holds TWO contradictory answers:")
    for c in corpus:
        if "rate" in c["content"].lower():
            print(f"  - {c['metadata']['date']} ({c['metadata']['source_type']}): "
                  f"{c['content'][:60]}…")

    # 3. The temporal arbitration.
    active, stale = arbitrate_versions(corpus, subject="rate")

    print("\n" + "=" * 78)
    print("TEMPORAL ARBITRATION: the freshest version prevails")
    print("=" * 78)
    for c in stale:
        print(f"  MUTED: {c['metadata']['date']} ({c['metadata']['source_type']}) "
              f"-> marked obsolete")
    frag, score = search_for(active, question)
    print("\nThe answer kept, from the arbitrated corpus:")
    print(f"  source: {frag['metadata']['source_type']} of {frag['metadata']['date']}")
    print(f"  content: {frag['content'][:80]}…")
    correct = "4.7" in frag["content"]
    print(f"  -> does cite the current rate (4.7%): {'YES' if correct else 'NO'}")

    out = FIX / "arbitrated_corpus.json"
    out.write_text(json.dumps({"active": active, "muted": stale},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out.name}")

    print("\nWHAT TO REMEMBER")
    print("- The cross-source merge brings different formats into one set of chunks.")
    print("- The logical conflict, 2024 against 2026, is invisible until fragments are dated.")
    print("- Temporal arbitration mutes the obsolete: freshness settles it.")


if __name__ == "__main__":
    main()
