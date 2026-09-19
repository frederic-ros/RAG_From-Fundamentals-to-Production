# -*- coding: utf-8 -*-
"""
Lab 22-3 — Diagnosis: faced with a bad answer, which link gave way?

Learning objective
------------------
In production, a user reports a bad answer. The key skill is to walk back up the
chain — ingestion, retrieval, ranking, consolidation, generation — and to name
THE precise link that gave way, instead of "repairing the RAG" blind.

A systematic diagnostic procedure is implemented, answering in order:

  1. Is the document PRESENT in the index?          (if not: missing content)
  2. Did it COME BACK among the candidates?         (if not: representation / ingestion)
  3. Was it HIGH enough to be read (top-k)?         (if not: missed at ranking)
  4. Was the context passed on actually USED?       (if not: context not used)
  5. Is the answer FAITHFUL to the context?         (if not: false but confident)

The same procedure is what you would wire onto real logs: question, fragments
with their scores, answer.

No API key. Run this first: python generate_corpus.py
"""

import json
from pathlib import Path

import ragdiag as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"
K = 3   # the system reads only the top K results


def diagnostiquer(question, good_id, pool, k=K):
    """Remonte the string and returns (panne, parade, trace)."""
    texts = [f["text"] for f in pool]
    ids = [f["id"] for f in pool]
    trace = []

    # 1. INDEX ----------------------------------------------------------------
    dans_index = good_id in ids
    trace.append(("ingestion", "the right document is in the index", dans_index))
    if not dans_index:
        return ("Missing content", "improve the ingestion (formats, OCR), "
                "or let the loop try other keys", trace)

    # 2. RECALL (present in the ranking, regardless of rank) -----------
    search = R.Search(texts)
    ordre = search.rank(question)
    order_ids = [ids[i] for i, _ in ordre]
    rank_value = R.rank_of(order_ids, good_id)
    remonte = rank_value is not None and rank_value <= 10
    trace.append(("retrieval", f"the right document is a candidate (rank {rank_value})", remonte))

    # 3. CLASSEMENT (in the top-k transmis ?) -------------------------------
    dans_topk = rank_value is not None and rank_value <= k
    trace.append(("ranking", f"the right document is in the top-{k}", dans_topk))
    if not dans_topk:
        return ("Missed at ranking", "rerank, to bring the good document back "
                "in the top-k)", trace)

    # 4. CONTEXT USED / 5. FAITHFULNESS -------------------------------------
    ctx = [texts[i] for i, _ in ordre[:k]]
    ref = [f["text"] for f in pool if f["id"] == good_id]
    prec = R.context_precision(ctx, ref)
    answer = R.generate_answer(question, ctx)
    fid = R.faithfulness(answer, ctx)
    bon_cite = any(t in answer for t in _termes(ref[0])) if ref else False
    trace.append(("generation",
                  f"the good fragment is used in the answer "
                  f"(context precision: {prec:.0%})",
                  bon_cite))
    if not bon_cite:
        return ("Context not used", "tend to the order of the fragments, cut the "
                "noise (MMR), compress the context", trace)
    if fid < 0.6:
        return ("False but confident", "verification, plus permission to say \"I do "
                "not know\"", trace)
    return ("No failure detected", "the answer is grounded and complete", trace)


def _termes(text):
    import re
    stop = R._STOP_WORDS
    return [t for t in re.findall(r"\w+", text.lower())
            if t not in stop and len(t) > 3][:6]


def show(cas, question, good_id, pool):
    print("\n" + "=" * 78)
    print(f"CAS — {cas}")
    print("=" * 78)
    print(f"Question: \"{question}\"")
    panne, parade, trace = diagnostiquer(question, good_id, pool)
    print("\n  Walking back up the chain:")
    for stage, label, ok in trace:
        mark = "OK " if ok else "FAIL"
        print(f"    [{mark:>5s}] {stage:<11s} — {label}")
    print(f"\n  >>> DIAGNOSTIC : {panne}")
    print(f"  >>> PARADE     : {parade}")


def main() -> None:
    print("=" * 78)
    print("Lab 22-3 — Diagnosis: faced with a bad answer, which link gave way?")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus introuvable. Lancez d'abord : python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    near_dups = data["near_duplicates"]
    print(f"\nMode retrieval : {R.mode_retrieval()}   |   "
          f"Generation mode: {R.generation_mode()}   |   top-k read = {K}")

    # Case 1 — missing content: the good document (#4) was removed from the index.
    pool1 = [f for f in frags if f["id"] != 4]
    show("Claire reports a wrong answer on remote work for apprentices",
             "What are the remote work entitlements of apprentices?", 4, pool1)

    # Case 2 — missed at ranking: near-duplicates drown the good document (#1).
    pool2 = frags + near_dups
    show("Julien: the P-42 stop procedure does not come back",
             "What is the emergency stop procedure for the P-42 pump?", 1, pool2)

    # Cas 3 — healthy : the string tient of bout in bout.
    show("A control: a healthy question, to check the procedure",
             "How is motor M-18 cooled in the event of overheating?", 3, frags)

    print("\n" + "=" * 78)
    print("WHAT THE DIAGNOSIS REVEALS")
    print("=" * 78)
    print("  The same complaint, \"a bad answer\", hides DIFFERENT failures at")
    print("  different stages, and therefore different remedies. Walking back up the")
    print("  chain in order avoids reranking what belongs to ingestion, or enriching")
    print("  the index when the problem is a simple matter of order.")
    print("\n  REMEMBER: you do not repair \"the RAG\", you repair the right STAGE.")


if __name__ == "__main__":
    main()
