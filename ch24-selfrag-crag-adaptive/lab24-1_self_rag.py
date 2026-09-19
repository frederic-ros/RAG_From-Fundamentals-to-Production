# -*- coding: utf-8 -*-
"""
Lab 24-1 — Self-RAG: learning to say "I am not sure"

Learning objective
------------------
Show how a system can evaluate FOR ITSELF the quality of what it has retrieved,
instead of answering confidently from mediocre fragments. The "reflection
tokens" of Self-RAG are implemented as explicit judgements:

    ISREL — is the passage RELEVANT to the question?
    ISSUP — is the statement produced SUPPORTED by the passage?
    ISUSE — is the answer USEFUL (does it really answer)?

A CONFIDENCE score is aggregated from them, and two behaviours are compared on a
rare failure that the corpus covers badly:

  - classic RAG: answers anyway -> a false but assured answer;
  - Self-RAG: doubts (low confidence) -> a cautious answer, or a request for a
    further search.

    The problem is not only to retrieve.
    The problem is to know whether what was retrieved deserves trust.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import cragkit as C

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"
SEUIL_CONFIANCE = 0.50


def rag_classique(question, rech, frags, k=3):
    """Classic RAG: retrieve the top-k and answer, without judging itself."""
    top = [frags[i]["text"] for i, _ in rech.classer(question, k=k)]
    return C.generate_answer(question, top), top


def self_rag(question, rech, frags, k=3):
    """Self-RAG: retrieve, JUDGE with reflection tokens, then own the answer or doubt."""
    top = [frags[i]["text"] for i, _ in rech.classer(question, k=k)]
    reponse = C.generate_answer(question, top)
    jug = C.tokens_reflexion(question, top, reponse)
    if jug.confiance < SEUIL_CONFIANCE:
        prudente = ("I am not certain: the documents available do not clearly cover "
                    "this question (confidence "
                    f"{jug.confiance:.2f}). A further search is recommended, "
                    "rather than an affirmative answer.")
        return prudente, top, jug, "prudent"
    return reponse, top, jug, "owned"


def main() -> None:
    print("=" * 78)
    print("Lab 24-1 — Self-RAG: learning to say \"I am not sure\"")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = C.Search([f["text"] for f in frags])

    print(f"\nMode retrieval : {C.mode_retrieval()}   |   "
          f"Mode jugement : {C.mode_jugement()}")
    if C.mode_jugement() == "regle":
        print("Reflection tokens = a deterministic proxy. For a real LLM-as-judge:")
        print("  OLLAMA_MODEL=llama3.2 python lab24-1_self_rag.py")

    # Deux questions : a bien couverte, a mal couverte (panne rare).
    cas = [
        ("A question WELL covered (the P-12 procedure)",
         "What is the emergency stop procedure for pump P-12?"),
        ("A question BADLY covered (a rare failure, corrosive lubricant)",
         "Which exact lubricant should be used for the bearings of pump P-42 "
         "en environnement corrosif ?"),
    ]

    for titre, question in cas:
        print("\n" + "=" * 78)
        print(titre)
        print("=" * 78)
        print(f"Question: \"{question}\"")

        # --- RAG classique ---
        rep_rag, ctx = rag_classique(question, rech, frags)
        print("\n  [Classic RAG] answers without judging itself:")
        print(f"    → {rep_rag[:150]}")

        # --- Self-RAG ---
        rep_sr, ctx, jug, mode = self_rag(question, rech, frags)
        print("\n  [Self-RAG] judges its passages (reflection tokens):")
        print(f"    ISREL (relevance passages) : {jug.isrel:.2f}")
        print(f"    ISSUP (answer supported)    : {jug.issup:.2f}")
        print(f"    ISUSE (answer useful)       : {jug.isuse:.2f}")
        print(f"    -> AGGREGATED CONFIDENCE    : {jug.confiance:.2f} "
              f"(threshold {SEUIL_CONFIANCE:.2f})")
        print(f"    Decision: {mode.upper()}")
        print(f"    → {rep_sr[:170]}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  On the well-covered question, Self-RAG owns its answer: confidence is high.")
    print("  On the rare failure, classic RAG answers confidently from")
    print("  off-topic fragments; Self-RAG measures a low confidence and")
    print("  prefers the cautious admission to the hallucination.")
    print("\n  WHAT TO REMEMBER: retrieving is not enough — you have to judge whether")
    print("  what was retrieved deserves trust. That is the self-evaluation of Self-RAG.")


if __name__ == "__main__":
    main()
