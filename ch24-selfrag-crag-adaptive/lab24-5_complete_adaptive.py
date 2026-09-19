# -*- coding: utf-8 -*-
"""
Lab 24-5 — Building a complete Adaptive-RAG

Learning objective
------------------
Assemble the chapter's pieces into a single orchestrator. Adaptive-RAG is not a
new architecture: it is the conductor of the previous ones.

    1. ROUTE the question (direct / simple / iterative);
    2. RETRIEVE according to the path (nothing / one pass / a loop);
    3. SELF-EVALUATE the passages (the reflection tokens of Self-RAG);
    4. CORRECT if the confidence is low (the grader and web fallback of CRAG);
    5. GENERATE the final answer.

For each question the execution diagram is produced — the sequence of steps
actually taken — along with the cost and an estimate of quality. You can read
from it that each question follows a DIFFERENT path, which is the whole point of
the orchestrator.

    Adaptive-RAG is not a new building block.
    It is an orchestrator of the previous blocks.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import cragkit as C

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"
SEUIL = 0.50


def adaptive_rag(question, rech, frags, k=3):
    """Orchestrator Adaptive-RAG complet. Returns (answer, steps, compteur)."""
    cpt = C.Counter()
    steps = []

    # 1. ROUTER
    voie, just = C.routeur(question, compteur=cpt)
    steps.append(f"router → {voie} ({just})")

    # 2. Voie DIRECTE : not of search — the reponse vient of the modele lui-meme.
    if voie == "direct":
        steps.append("a direct answer from the model (no search)")
        if C.ollama_disponible():
            cpt.llm()
            rep = C._llm("Answer the question briefly and directly.\n\n"
                         f"Question: {question}\nAnswer:", num_predict=80)
        else:
            rep = ("[direct path] With no local LLM, the direct answer is not "
                   "available: this path rests on the model's own knowledge of "
                   "model (start Ollama). No search was necessary.")
        return rep, steps, cpt, []

    # 2'. TO RETRIEVE (simple = 1 passe ; iterative = profondeur accrue)
    kk = k if voie == "simple" else k + 2
    cpt.corpus()
    top = [frags[i]["text"] for i, _ in rech.classer(question, k=kk)]
    steps.append(f"retrieval corpus (top-{kk})")

    # 3. AUTO-TO EVALUATE (Self-RAG)
    rep = C.generate_answer(question, top, compteur=cpt)
    jug = C.tokens_reflexion(question, top, rep, compteur=cpt)
    steps.append(f"Self-RAG self-evaluation -> confidence {jug.confiance:.2f}")

    # 4. CORRECT (CRAG): the passages are graded systematically. The confidence of
    # Self-RAG alone does not detect "missing content" — a P-12 text looks safe for
    # a P-99 question. The grader tests the presence of the entity asked for.
    verdict, score = C.grader_crag(question, top, compteur=cpt)
    steps.append(f"grader CRAG → {verdict} ({score:.2f})")
    if verdict == "not_confident" or jug.confiance < SEUIL:
        if verdict == "not_confident":
            web = C.web_search(question, k=1, compteur=cpt)
            top = [w["text"] for w in web]
            steps.append(f"repli web → {web[0]['subject']}")
            rep = C.generate_answer(question, top, compteur=cpt)
            steps.append("regeneration on web sources")
        else:
            steps.append("low confidence but a relevant corpus: the cautious answer is kept")

    return rep, steps, cpt, top


def qualite(question, reponse, passages):
    import re
    # Anchoring test: if the question names a distinctive entity, the answer must
    # mentionner for etre correcte (sinon hors-cible).
    entites = set(re.findall(r"\b[a-z]{1,3}-?\d{2,4}\b", question.lower()))
    if entites and any(e not in reponse.lower() for e in entites):
        return 0.20
    if not passages:
        # Voie directe : hors-line, the reponse depend of the modele (often indisponible).
        # Neutralise the score instead of penalising an intentional omission.
        return float("nan") if reponse.startswith("[voie directe]") else C.isuse(question, reponse)
    # Utilite of the reponse + relevance of the meilleur passage retenu.
    use = C.isuse(question, reponse)
    rel = max(C.isrel(question, p) for p in passages)
    return 0.5 * use + 0.5 * rel


def main() -> None:
    print("=" * 78)
    print("Lab 24-5 — Building a complete Adaptive RAG system")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = C.Search([f["text"] for f in frags])
    print(f"\nMode retrieval : {C.mode_retrieval()}   |   "
          f"Mode jugement : {C.mode_jugement()}")

    # A sample covering the three paths, plus one web correction.
    questions = [
        "What is today's date?",                                      # direct
        "What is the emergency stop procedure for pump P-12?",  # simple, confident
        "Analyse the possible causes of overheating in motor M-18 "
        "and their consequences for production.",                    # iterative
        "What is the emergency stop procedure for pump P-99?",  # a web correction
    ]

    recap = []
    for question in questions:
        print("\n" + "=" * 78)
        print(f"QUESTION: \"{question[:60]}{'…' if len(question) > 60 else ''}\"")
        print("=" * 78)
        rep, steps, cpt, passages = adaptive_rag(question, rech, frags)
        print("  Execution diagram:")
        for i, e in enumerate(steps, 1):
            fleche = "   " if i == 1 else "  ↳"
            print(f"  {fleche} {i}. {e}")
        q = qualite(question, rep, passages)
        print(f"  Answer: {rep[:150]}")
        q_aff = "n/a" if q != q else f"{q:.2f}"
        print(f"  Quality: {q_aff}  |  Cost: {cpt.summary()}")
        voie = steps[0].split('→')[1].split('(')[0].strip()
        recap.append((question, voie, cpt.total, q))

    # --- The summary ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("SUMMARY — each question, its path, its cost")
    print("=" * 78)
    print(f"  {'path':<10s} | {'cost':>5s} | {'qual.':>5s} | question")
    print("  " + "-" * 70)
    for question, voie, cout, q in recap:
        q_aff = "n/a " if q != q else f"{q:.2f}"
        print(f"  {voie:<10s} | {cout:>5d} | {q_aff:>5s} | {question[:42]}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  Each question follows a different path through the same orchestrator: the")
    print("  trivial one answers with no search, the standard one makes a pass, the")
    print("  complex one digs deeper, and the unfindable one switches to the web.")
    print("  The cost adapts.")
    print("\n  WHAT TO REMEMBER: Adaptive-RAG orchestrates routing, retrieval,")
    print("  self-evaluation and correction. It is not a new building block — it is")
    print("  their conductor.")


if __name__ == "__main__":
    main()
