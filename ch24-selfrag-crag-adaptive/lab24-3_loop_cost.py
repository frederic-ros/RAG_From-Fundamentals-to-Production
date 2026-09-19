# -*- coding: utf-8 -*-
"""
Lab 24-3 — The cost of the loop: when should it be relaunched?

Learning objective
------------------
Measure the REAL cost of self-correction. Three architectures are compared on two
kinds of question:

  - classic RAG: one pass, no judgement;
  - Self-RAG: judges its passages, may relaunch or abstain;
  - CRAG: grades, and switches to the web when not confident.

For each, the cost is measured (LLM calls plus searches) alongside the quality of
the answer (grounding and coverage). The chapter's verdict:

    A simple question -> classic RAG wins (the same quality, a minimal cost).
    A hard question   -> Self-RAG or CRAG win (far better quality, a justified cost).

    The loop improves quality, but it is never free.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import cragkit as C

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"
SEUIL = 0.50


def arch_rag(question, rech, frags, k=3):
    cpt = C.Counter()
    cpt.corpus()
    top = [frags[i]["text"] for i, _ in rech.classer(question, k=k)]
    rep = C.generate_answer(question, top, compteur=cpt)
    return rep, top, cpt


def arch_self_rag(question, rech, frags, k=3):
    cpt = C.Counter()
    cpt.corpus()
    top = [frags[i]["text"] for i, _ in rech.classer(question, k=k)]
    rep = C.generate_answer(question, top, compteur=cpt)
    jug = C.tokens_reflexion(question, top, rep, compteur=cpt)
    if jug.confiance < SEUIL:
        # Relaunch: a second, widened search, at an extra cost.
        cpt.corpus()
        top2 = [frags[i]["text"] for i, _ in rech.classer(question, k=k + 2)]
        rep = C.generate_answer(question, top2, compteur=cpt)
        top = top2
    return rep, top, cpt


def arch_crag(question, rech, frags, k=3):
    cpt = C.Counter()
    cpt.corpus()
    top = [frags[i]["text"] for i, _ in rech.classer(question, k=k)]
    verdict, _ = C.grader_crag(question, top, compteur=cpt)
    if verdict == "not_confident":
        web = C.web_search(question, k=1, compteur=cpt)
        top = [w["text"] for w in web]
    rep = C.generate_answer(question, top, compteur=cpt)
    return rep, top, cpt


import re as _re

def qualite(question, reponse, passages, volets):
    """Quality : the answer adresse-t-it truement the question ?

    The decisive criterion: if the question names a distinctive entity (P-99,
    M-18), the answer MUST mention it to be correct. An answer about "P-99"
    built on P-42 text does not contain "P-99" -> low quality, however fluent.
 On combine this test of ancrage with the relevance passages and the couverture 
    any facets.
 """
    if not passages:
        return 0.0
    entites = set(_re.findall(r"\b[a-z]{1,3}-?\d{2,4}\b", question.lower()))
    if entites:
        rep_l = reponse.lower()
        if any(e not in rep_l for e in entites):
            return 0.20  # the entity asked for does not appear: an off-target answer
    rels = [C.isrel(question, p) for p in passages]
    relevance = sum(rels) / len(rels)
    if volets:
        return (relevance + C.couverture(reponse, volets)) / 2
    return relevance


def main() -> None:
    print("=" * 78)
    print("Lab 24-3 — The cost of the loop: when should it be relaunched?")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = C.Search([f["text"] for f in frags])
    print(f"\nMode retrieval : {C.mode_retrieval()}   |   "
          f"Mode jugement : {C.mode_jugement()}")
    print("Cost = LLM calls plus searches (corpus and web). Quality in [0,1].")

    cas = [
        ("SIMPLE — well covered by the corpus",
         "What is the emergency stop procedure for pump P-12?", []),
        ("DIFFICILE — hors corpus (P-99)",
         "What is the emergency stop procedure for pump P-99?", []),
    ]

    archs = [("RAG classique", arch_rag),
             ("Self-RAG", arch_self_rag),
             ("CRAG", arch_crag)]

    for titre, question, volets in cas:
        print("\n" + "=" * 78)
        print(f"CAS {titre}")
        print("=" * 78)
        print(f"Question: \"{question}\"")
        print(f"\n  {'architecture':<16s} | {'cost':>5s} | {'quality':>7s} | cost detail")
        print("  " + "-" * 64)
        for nom, fn in archs:
            rep, ctx, cpt = fn(question, rech, frags)
            q = qualite(question, rep, ctx, volets)
            print(f"  {nom:<16s} | {cpt.total:>5d} | {q:>7.2f} | {cpt.summary()}")
        if titre.startswith("SIMPLE"):
            print("\n  Reading: the same quality everywhere, at very different costs.")
            print("  Self-RAG judges each passage and each statement: it is the most")
            print("  dearly (the chapter speaks of 2 to 3 times the cost). On a question")
            print("  already well covered, paying for that loop returns nothing.")
        else:
            print("\n  Reading: classic RAG answers at minimal cost... but wrongly (the")
            print("  corpus has nothing on the P-99). CRAG pays a little more and switches to the web:")
            print("  a far better quality. The spending is justified here.")

    print("\n" + "=" * 78)
    print("WHAT THE COMPARISON REVEALS")
    print("=" * 78)
    print("  On a simple question the loop returns nothing and costs more:")
    print("  classic RAG wins. On a hard question, the loop (Self-RAG")
    print("  or CRAG) turns a false answer into a correct one: it wins.")
    print("\n  WHAT TO REMEMBER: the loop improves quality but is never free.")
    print("  Hence the next chapter's question: route, so as to pay only when needed.")


if __name__ == "__main__":
    main()
