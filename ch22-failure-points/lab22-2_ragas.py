# -*- coding: utf-8 -*-
"""
Lab 22-2 — Measuring the failures: a mini-RAGAS (LLM judge)

Learning objective
------------------
A failure that is not measured cannot be repaired. This lab builds a small
RAGAS-style dashboard and ties each metric to a FAMILY of failures:

  - recall@k and nDCG@k -> missing content, chunking, missed at ranking;
  - context precision   -> retrieval bias, context not used;
  - faithfulness        -> an answer that is false but confident.

"Repairing without measuring is treating blind." Everything is measured BEFORE
and AFTER a correction, so as to turn "it seems better" into "recall went from
X to Y".

As close as possible to real usage
----------------------------------
With Ollama running, the faithfulness and coverage judge is a REAL local LLM —
exactly the mechanism RAGAS uses. Without it, a deterministic proxy keeps the
lab runnable and reproducible.

No API key. Run this first: python generate_corpus.py
"""

import json
from pathlib import Path

import ragdiag as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def evaluate_q(question, relevant, frags, k=5, remove=None):
    """Evaluate one question: retrieval (recall, nDCG), context (precision), answer

 (fidelity). `remove` allows of simuler a panne (ex. remove the good doc), then
 of to measure the correction in the remettant.
 """
    pool = [f for f in frags if remove is None or f["id"] != remove]
    texts = [f["text"] for f in pool]
    ids = [f["id"] for f in pool]
    search = R.Search(texts)
    ordre = search.rank(question)
    order_ids = [ids[i] for i, _ in ordre]

    recall_score = R.recall_at_k(order_ids, relevant, k=k)
    ndcg = R.ndcg_at_k(order_ids, relevant, k=k)

    # Context transmis = top-k. Precision = part really relevant.
    ctx_idx = [i for i, _ in ordre[:k]]
    ctx = [texts[i] for i in ctx_idx]
    ref = [f["text"] for f in frags if f["id"] in relevant]
    prec = R.context_precision(ctx, ref)

    answer = R.generate_answer(question, ctx)
    fid = R.faithfulness(answer, ctx)
    return {"recall_score": recall_score, "ndcg": ndcg, "precision": prec,
            "fidelite": fid, "answer": answer}


def row(nom, m):
    print(f"  {nom:<26s} | {m['recall_score']:>7.2f} | {m['ndcg']:>6.2f} | "
          f"{m['precision']:>9.2f} | {m['fidelite']:>8.2f}")


def main() -> None:
    print("=" * 78)
    print("Lab 22-2 — Measuring the failures: a mini-RAGAS (LLM judge)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus introuvable. Lancez d'abord : python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]

    print(f"\nMode retrieval : {R.mode_retrieval()}   |   "
          f"Mode juge : {R.generation_mode()}")
    if R.generation_mode() == "ollama":
        print("Faithfulness judge = a real local LLM (Ollama). Production behaviour.")
    else:
        print("Faithfulness judge = a deterministic proxy (overlap). Start Ollama")
        print("for the real LLM-as-a-judge:  OLLAMA_MODEL=llama3.2 python lab22-2_ragas.py")

    header = (f"\n  {'metric':<26s} | {'recall@5':>8s} | {'nDCG':>6s} | "
              f"{'ctx prec.':>9s} | {'faithful.':>9s}")

    # =====================================================================
    # Case A — Missing content: before and after correcting ingestion
    # =====================================================================
    print("\n" + "=" * 78)
    print("CASE A — MISSING CONTENT: measuring the ingestion fix")
    print("=" * 78)
    q = "What are the remote work entitlements of apprentices?"
    good = 4
    print(f"Question: \"{q}\"  (good document #{good})")
    print(header)
    print("  " + "-" * 68)
    before = evaluate_q(q, [good], frags, remove=good)   # document removed = the failure
    row("BEFORE (document removed)", before)
    after = evaluate_q(q, [good], frags, remove=None)    # document restored = fixed
    row("AFTER (document restored)", after)
    print(f"\n  Reading: recall@5 goes from {before['recall_score']:.2f} to "
          f"{after['recall_score']:.2f}. The RECALL metric quantifies exactly this failure")
    print("  \"missing content\" — and proves the correction.")

    # =====================================================================
    # Case B — Missed at ranking: before and after a reranking proxy
    # =====================================================================
    print("\n" + "=" * 78)
    print("CASE B — MISSED AT RANKING: what nDCG captures")
    print("=" * 78)
    near_dups = data["near_duplicates"]
    q = "What is the emergency stop procedure for the P-42 pump?"
    good = 1
    print(f"Question: \"{q}\"  (good document #{good})")
    print(header)
    print("  " + "-" * 68)
    # "Before": with the near-duplicates squatting at the head.
    sabotaged = frags + near_dups
    before = evaluate_q(q, [good], sabotaged, remove=None)
    row("BEFORE (near-duplicates)", before)
    # "After" (a reranking proxy): the near-duplicates are removed.
    after = evaluate_q(q, [good], frags, remove=None)
    row("AFTER (a re-ranking proxy)", after)
    print(f"\n  Reading: nDCG goes from {before['ndcg']:.2f} to {after['ndcg']:.2f}.")
    print("  RECALL could stay good, since the document was there; it is the RANK")
    print("  that fails — exactly what nDCG and MRR measure, and what reranking targets.")

    # =====================================================================
    # Case C — Faithfulness: a grounded answer against an embroidered one
    # =====================================================================
    print("\n" + "=" * 78)
    print("CASE C — FAITHFULNESS: detecting the \"false but confident\"")
    print("=" * 78)
    ctx = [frags[1]["text"]]   # procedure P-42, the good context
    answer_grounded = ("To stop the P-42 in an emergency, hit the mushroom-head button, "
                       "isolate the discharge circuit and lock out the equipment.")
    answer_embroidered = ("To stop the P-42, cut the auxiliary diesel engine, drain the oil "
                          "tank and notify the purchasing department within 48 hours.")
    f_ok = R.faithfulness(answer_grounded, ctx)
    f_ko = R.faithfulness(answer_embroidered, ctx)
    print("  Context supplied: the real stop procedure for the P-42.")
    print(f"  GROUNDED answer (drawn from the context): faithfulness = {f_ok:.2f}")
    print(f"  EMBROIDERED answer (invented, confident): faithfulness = {f_ko:.2f}")
    print("\n  Reading: faithfulness collapses when the model invents. It is the")
    print("  thermometer of the \"false but confident\" — the most dangerous failure.")

    # =====================================================================
    # SYNTHESIS
    # =====================================================================
    print("\n" + "=" * 78)
    print("TO EACH FAMILY OF FAILURES, ITS METRIC")
    print("=" * 78)
    print("  recall@k / nDCG    -> missing content, chunking, missed at ranking")
    print("  context precision  -> retrieval bias, context not used")
    print("  faithfulness       -> an answer that is false but confident")
    print("\n  REMEMBER: a set of annotated questions plus a table of metrics turns")
    print("  \"it seems better\" into figures. RAGAS automates that principle, often")
    print("  with an LLM as judge; the principle outlives the tool.")


if __name__ == "__main__":
    main()
