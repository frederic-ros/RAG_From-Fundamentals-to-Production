# -*- coding: utf-8 -*-
"""
Lab 29-1 — The triad, and locating the failure

Evaluating a RAG with a single number tells you it is wrong, not WHERE. The
triad separates three questions:

    context recall  — did the retrieval bring back the right fragment?
    fidelity        — is the answer supported by that fragment?
    relevance       — does the answer address the question?

Three cases are designed to make one precise score collapse:

    G08 (distinction)  : D01 and D02 are lexically very close.
    G09 (out of corpus): no fragment holds the answer; recall must collapse.
    G10 (multi-hop)    : recall@1 = 0.50 but recall@3 = 1.00, which points at
                         the chunker rather than the generator.

BASELINE (French edition, reproduced here): G10 gives recall@1 = 0.50 and
recall@3 = 1.00. If recall@3 falls below 1.00, the lesson "raising k fixes it"
is no longer true and the wording of G10 needs checking.

No API key. Run generate_corpus.py first.
"""

from evalkit import (RAGPipeline, load_fragments, load_golden,
                     recall_at_k, mrr, ndcg_at_k, juge_fidelite,
                     juge_pertinence, context_recall, bandeau)


def main():
    bandeau("Lab 29-1 — The evaluation pipeline: the triad")
    docs = load_fragments()
    golden = load_golden()
    pipe = RAGPipeline(docs, k=3)
    K = 3

    print(f"\n{'Q':<5}{'rec@3':>7}{'MRR':>7}{'nDCG':>7}"
          f"{'fidel.':>8}{'relev.':>9}{'ctx_rec':>9}  category")
    print("─" * 72)

    agg = {"rec": [], "mrr": [], "ndcg": [], "fid": [], "per": [], "ctx": []}
    for g in golden:
        rep = pipe.repondre(g["question"])
        recs = [f["id"] for f in pipe.rech.chercher(g["question"], k=5)]
        ctx = " ".join(f["texte"] for f in rep.fragments)

        m_rec = recall_at_k(recs, g["expected_fragments"], K)
        m_mrr = mrr(recs, g["expected_fragments"])
        m_ndcg = ndcg_at_k(recs, g["expected_fragments"], K)
        m_fid = juge_fidelite(rep.reponse, ctx)
        m_per = juge_pertinence(rep.reponse, g["question"])
        m_ctx = context_recall(ctx, g["reference"])

        # the cas hors-corpus not a not of fragment attendu : on neutralise rec/mrr
        if g["category"] != "out_of_corpus":
            agg["rec"].append(m_rec); agg["mrr"].append(m_mrr)
            agg["ndcg"].append(m_ndcg)
        agg["fid"].append(m_fid); agg["per"].append(m_per); agg["ctx"].append(m_ctx)

        print(f"{g['id']:<5}{m_rec:>7.2f}{m_mrr:>7.2f}{m_ndcg:>7.2f}"
              f"{m_fid:>8.2f}{m_per:>9.2f}{m_ctx:>9.2f}  {g['category']}")

    print("─" * 72)
    moy = lambda xs: sum(xs) / len(xs) if xs else 0.0
    print(f"{'MOY':<5}{moy(agg['rec']):>7.2f}{moy(agg['mrr']):>7.2f}"
          f"{moy(agg['ndcg']):>7.2f}{moy(agg['fid']):>8.2f}"
          f"{moy(agg['per']):>9.2f}{moy(agg['ctx']):>9.2f}")

    # === localised diagnosis ==============================================
    print("\n" + "═" * 72)
    print("LOCALISED DIAGNOSIS — reading the triad to find the failure\n")

    g09 = next(g for g in golden if g["id"] == "G09")
    rep09 = pipe.repondre(g09["question"])
    ctx09 = " ".join(f["texte"] for f in rep09.fragments)
    print(f"G09 (out of corpus): \"{g09['question']}\"")
    print(f"   context recall = {context_recall(ctx09, g09['reference']):.2f} (faible)")
    print(f"   abstention     = {rep09.abstention}")
    print("   -> the answer IS NOT in the corpus. A context recall that")
    print("      collapses points at the RETRIEVAL or the corpus, not the generation."),
    print("      The right"),
    print("     expected behaviour is abstention (see Lab 29-5).")

    g10 = next(g for g in golden if g["id"] == "G10")
    recs10 = [f["id"] for f in pipe.rech.chercher(g10["question"], k=5)]
    print(f"\nG10 (multi-hop): \"{g10['question'][:50]}…\"")
    print(f"   expected fragments: {g10['expected_fragments']}")
    print(f"   recall@1 = {recall_at_k(recs10, g10['expected_fragments'], 1):.2f}"
          f"   recall@3 = {recall_at_k(recs10, g10['expected_fragments'], 3):.2f}")
    print("   -> the complete answer is spread across TWO fragments. A low recall@1")
    print("      but a correct recall@3 points at the CHUNKER or the retrieval k:")
    print("      raising k, or grouping the linked fragments, fixes the failure.")

    print("\n" + "═" * 72)
    print("THE MESSAGE: the triad turns \"the system is wrong\" into \"the retrieval")
    print("did not bring back the right fragment on this category of question\".")
    print("High fidelity plus low recall -> retrieval. High recall plus low")
    print("fidelity -> generation. The failure is located without groping.")


if __name__ == "__main__":
    main()
