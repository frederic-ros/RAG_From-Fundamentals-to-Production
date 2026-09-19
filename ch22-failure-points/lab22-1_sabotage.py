# -*- coding: utf-8 -*-
"""
Lab 22-1 — The seven points of failure, by controlled sabotage

Learning objective
------------------
Rather than READING the list of failures, they are PROVOKED — one at a time — on
a minimal pipeline, and the symptom of each is observed. You start from a
healthy corpus, then pull ONE sabotage lever at a time, changing nothing else.

  You never really understand a failure until you have triggered it yourself.

The thesis of the chapter then appears plainly: FOUR of the seven "historical"
failures are RETRIEVAL failures, visible WITHOUT any LLM (missing content,
shattered chunking, a miss at ranking, and — on the representation side — the
confusion of meaning). The others belong to generation or to the absence of a
loop.

Without Ollama the generation is extractive and deterministic: enough to see the
symptom. With Ollama (OLLAMA_MODEL), a real LLM writes the answer, and the
symptom then reads as it would in production.

No API key. Run this first: python generate_corpus.py
"""

import json
from pathlib import Path

import ragdiag as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def _top(search, frags, question, k=5, **kw):
    order = search.rank(question, **kw)
    return order[:k]


def main() -> None:
    print("=" * 78)
    print("Lab 22-1 — The seven points of failure, by controlled sabotage")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus introuvable. Lancez d'abord : python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    near_dups = data["near_duplicates"]
    by_id = {f["id"]: f for f in frags}

    print(f"\nMode retrieval : {R.mode_retrieval()}   |   "
          f"Generation mode: {R.generation_mode()}")
    print("(Without Ollama the generation is extractive and deterministic.)")

    # =====================================================================
    # FAILURE 1 — Missing content (BEFORE the question) — pure retrieval
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 1 — MISSING CONTENT  [before the question | retrieval]")
    print("=" * 78)
    q = "What are the remote work entitlements of apprentices?"
    good = 4
    healthy = [f["text"] for f in frags]
    R_healthy = R.Search(healthy)
    rank_healthy = R.rank_of([i for i, _ in R_healthy.rank(q)], good)
    print(f"Question: \"{q}\"")
    print(f"  Corpus healthy  : good document #{good} au rank_value {rank_healthy}.")

    sabotaged, note = R.sabotage_missing_content(frags, good)
    texts_s = [f["text"] for f in sabotaged]
    R_s = R.Search(texts_s)
    top = R_s.rank(q)[:3]
    print(f"  SABOTAGE     : {note}")
    print("  Top 3 after sabotage:")
    for rank_value, (i, s) in enumerate(top, 1):
        print(f"    {rank_value}. [{s:.3f}] {sabotaged[i]['subject']}")
    answer = R.generate_answer(q, [sabotaged[i]["text"] for i, _ in top])
    print(f"  Answer generated: {answer[:160]}")
    print("  SYMPTOM: the good fragment is no longer a candidate (a recall failure).")
    print("  The system answers from an off-topic neighbour, without flagging it.")
    print("  LINK: ingestion.  WHEN: before.  VISIBLE WITHOUT AN LLM: yes.")

    # =====================================================================
    # FAILURE 2 — Shattered chunking (BEFORE the question) — pure retrieval
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 2 — SHATTERED CHUNKING  [before the question | retrieval]")
    print("=" * 78)
    # On prend a document complet (stop P-42) and on the hache in miettes.
    doc = by_id[1]["text"]
    morceaux = R.sabotage_shattered_chunking(doc, size=7)
    print(f"Original document ({len(doc.split())} words) shredded into "
          f"{len(morceaux)} fragments de 7 words :")
    for m in morceaux[:3]:
        print(f"    | {m} …")
    q2 = "What is the complete emergency stop procedure for the P-42 pump, "\
         "from the mushroom-head button to the lock-out?"
    # Index = the miettes + the reste of the corpus (without the doc entier).
    others = [f["text"] for f in frags if f["id"] != 1]
    R_h = R.Search(morceaux + others)
    top = R_h.rank(q2)[:3]
    print("  Top-3 fragments: each looks relevant, none is complete.")
    for rank_value, (i, s) in enumerate(top, 1):
        src = (morceaux + others)[i]
        print(f"    {rank_value}. [{s:.3f}] {src[:55]}…")
    print("  SYMPTOM: the answer exists, but scattered; only one piece comes back.")
    print("  LINK: chunking.  WHEN: before.  VISIBLE WITHOUT AN LLM: yes.")

    # =====================================================================
    # FAILURE 3 — Misleading representation (BEFORE the question)
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 3 — MISLEADING REPRESENTATION  [before the question | retrieval]")
    print("=" * 78)
    print("  The embedding brings together texts that are thematically close but")
    print("  opposite in meaning. In TF-IDF mode, surface overlap illustrates it:")
    q3 = "emergency stop P-42"
    R_full = R.Search([f["text"] for f in frags])
    top = R_full.rank(q3)[:4]
    for rank_value, (i, s) in enumerate(top, 1):
        marque = "  <-- good" if frags[i]["id"] == 1 else ""
        print(f"    {rank_value}. [{s:.3f}] {frags[i]['subject']}{marque}")
    print("  SYMPTOM: sections sharing vocabulary (the general stop, other pumps)")
    print("  mingle with the good document. Surface proximity is not proximity of")
    print("  relevance.  LINK: embedding.  WHEN: before retrieval.  WITHOUT AN LLM: yes.")

    # =====================================================================
    # FAILURE 4 — Missed at ranking (DURING the search) — pure retrieval
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 4 — MISSED AT RANKING  [during the search | retrieval]")
    print("=" * 78)
    q4 = "What is the emergency stop procedure for the P-42 pump?"
    base = [f["text"] for f in frags]
    rank_before = R.rank_of([i for i, _ in R.Search(base).rank(q4)], 1)
    sabotaged, note = R.sabotage_ranking(frags, 1, near_dups)
    texts = [f["text"] for f in sabotaged]
    order = R.Search(texts).rank(q4)
    # Reto find the rank_value of the good doc (id 1) in the corpus sabotaged.
    pos_good = next(p for p, (i, _) in enumerate(order, 1) if sabotaged[i]["id"] == 1)
    print(f"Question: \"{q4}\"")
    print(f"  Without decoys: the right document sits at rank {rank_before}.")
    print(f"  SABOTAGE     : {note}")
    print(f"  With near-duplicates: the good document is pushed to rank {pos_good}.")
    print("  Top 3 (the near-duplicates squat at the head):")
    for rank_value, (i, s) in enumerate(order[:3], 1):
        print(f"    {rank_value}. [{s:.3f}] {sabotaged[i]['subject']}")
    print("  SYMPTOM: the good doc is retrieved but ranked too low to be read.")
    print("  LINK: ranking (and reranking).  WHEN: during retrieval.  WITHOUT AN LLM: yes.")

    # =====================================================================
    # FAILURE 5 — Context not used (AT THE ANSWER) — generation
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 5 — CONTEXT NOT USED  [at the answer | generation]")
    print("=" * 78)
    q5 = "What is the emergency stop procedure for the P-42 pump?"
    print(f"Question: \"{q5}\"")
    good_txt = by_id[1]["text"]
    distract = [by_id[i]["text"] for i in (8, 9, 14, 16, 18, 19)]
    ctx = R.context_with_distractors(good_txt, distract, position="milieu")
    prec = R.context_precision(ctx, [good_txt])
    print(f"  The model is given {len(ctx)} extracts, of which ONE is relevant,")
    print("  placed in the middle (the \"lost in the middle\" effect).")
    print(f"  Context precision (a RAGAS proxy): {prec:.2f}  "
          f"→ {int(round(prec*len(ctx)))}/{len(ctx)} extraits utiles.")
    print("  SYMPTOM: the good passage is present but drowned in noise. A real LLM")
    print("  (Ollama) then tends to lean on a less relevant passage, or to dilute")
    print("  its answer. Without an LLM, the failure is READ in the context precision,")
    print("  not in the extractive output, which does find the right passage.")
    print("  LINK: generation / ordering.  WHEN: at the answer.")

    # =====================================================================
    # FAILURE 6 — Incomplete answer (AT THE ANSWER) — root cause: no loop
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 6 — INCOMPLETE ANSWER  [at the answer | no loop]")
    print("=" * 78)
    q6 = "Compare the emergency stop procedures of pumps P-12, P-42 and P-88."
    parts = ["P-12", "P-42", "P-88"]
    R_full = R.Search([f["text"] for f in frags])
    # A realistic single pass: ONE search, ONE dominant fragment passed on.
    # The whole question does not know that it covers three distinct subjects.
    top1 = R_full.rank(q6)[0][0]
    ctx = [frags[top1]["text"]]
    answer = R.generate_answer(q6, ctx)
    taux, manquants = R.covers_question(answer, parts)
    print(f"Question (3 parts): \"{q6}\"")
    print(f"  Passe unique (1 search, fragment dominant = {frags[top1]['subject']})")
    print(f"  → coverage {taux*100:.0f} % ({3 - len(manquants)}/3 parts).")
    print(f"  Facets missing: {manquants if manquants else 'none'}")
    print("  SYMPTOM: the system handles the dominant part without KNOWING that some")
    print("  of others. That is the flaw the LOOP (ch. 23) fixes — see Lab 22-4.")
    print("  LINK: no rereading.  WHEN: at the answer.  WITHOUT AN LLM: no.")

    # =====================================================================
    # FAILURE 7 — Instability (AT THE ANSWER) — non-determinism
    # =====================================================================
    print("\n" + "=" * 78)
    print("FAILURE 7 — INSTABILITY  [at the answer | non-determinism]")
    print("=" * 78)
    q7 = "What is the emergency stop procedure for the P-42 pump?"
    base = [f["text"] for f in frags] + [d["text"] for d in near_dups]
    subjects = [f["subject"] for f in frags] + [d["subject"] for d in near_dups]
    Rb = R.Search(base)
    ranks = []
    print("  The same question, 5 runs, with ranking noise (near-equal scores):")
    for attempt in range(5):
        order = Rb.rank(q7, noise=0.05, seed=attempt)
        head = order[0][0]
        # rank_value of the good doc P-42 (first 'arret-P42' in base)
        idx_good = subjects.index("stop-P42")
        rg = next(p for p, (i, _) in enumerate(order, 1) if i == idx_good)
        ranks.append(rg)
        print(f"    run {attempt+1}: head = {subjects[head]:<16s} | "
              f"good doc au rank_value {rg}")
    import statistics
    print(f"  Rank du good doc : variable {ranks} "
          f"(standard deviation {statistics.pstdev(ranks):.2f}).")
    print("  SYMPTOM: tiny differences in score flip the ranking.")
    print("  LINK: non-determinism.  WHEN: at the answer.  To be measured and bounded.")

    # =====================================================================
    # SYNTHESIS
    # =====================================================================
    print("\n" + "=" * 78)
    print("WHAT THE SABOTAGE REVEALS")
    print("=" * 78)
    print("  Visible WITHOUT an LLM (pure retrieval): missing content, shattered")
    print("  chunking, misleading representation, missed at ranking -> 4 of the 7.")
    print("  Belonging to generation or to the loop: context not used,")
    print("  incompleteness, instability.")
    print("\n  REMEMBER: you do not repair a bad search with a good generator.")
    print("  The map of the failures IS the plan of the chapters that follow.")


if __name__ == "__main__":
    main()
