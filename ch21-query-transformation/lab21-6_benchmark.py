# -*- coding: utf-8 -*-
"""
Lab 21-6 — The benchmark: which transformation, and when?

Learning objective
------------------
Each transformation has been seen separately. But which is best? The question is
a trap: the answer depends on the TYPE of question. This lab proves it in
figures, measuring every method on every query, along with an indicative cost —
the "LLM" transformations cost a call, the others do not.

    No transformation is universally better: the choice depends on the case.

Everything is gathered into one table, and then compared with the router of Lab
21-5: choosing the right strategy per question beats any single method applied
everywhere.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import qtlib as Q

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


# Cost indicatif by method (appels LLM simulateds). the expansion/HyDE/recul/
# and decomposition require a generation; the direct search does not.
COUT = {
    "direct": 0,
    "expansion": 1,
    "hyde": 1,
    "decomposition": 1,
    "step_back": 1,
    "rewriting": 1,
}


def classement_methode(methode: str, question, history, R):
    """Return the ranking of indices for a given method."""
    if methode == "direct":
        return [i for i, _ in R.classer(question)]
    if methode == "expansion":
        return [i for i, _ in R.classer_multi(Q.expansion(question))]
    if methode == "hyde":
        return [i for i, _ in R.classer(Q.hyde(question))]
    if methode == "decomposition":
        return [i for i, _ in R.classer_multi(Q.decomposition(question))]
    if methode == "step_back":
        return [i for i, _ in R.classer(Q.step_back(question))]
    if methode == "rewriting":
        return [i for i, _ in R.classer(Q.rewriting(question, history))]
    return [i for i, _ in R.classer(question)]


def main() -> None:
    print("=" * 78)
    print("Lab 21-6 (BONUS) — Benchmark complet : quelle transformation gagne ?")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    R = Q.Search(texts)
    queries = data["queries"]
    print(f"\nMode de search : {Q.mode()}")
    print(f"{len(queries)} annotated queries, {len(frags)} documents.")

    methodes = ["direct", "expansion", "hyde", "decomposition",
                "step_back", "rewriting"]

    # --- Measuress by method (moyennes on toutes the queries) ------------
    resultats = {}
    for m in methodes:
        mrrs, rappels = [], []
        for req in queries:
            cl = classement_methode(m, req["question"], req.get("history", []), R)
            mrrs.append(Q.mrr(cl, req["relevant"]))
            rappels.append(Q.rappel_at_k(cl, req["relevant"], k=5))
        resultats[m] = (sum(mrrs) / len(mrrs), sum(rappels) / len(rappels))

    print("\n" + "=" * 78)
    print("EACH METHOD, APPLIED TO EVERY QUERY")
    print("=" * 78)
    print(f"  {'method':<16s} | {'MRR':>6s} | {'recall@5':>9s} | {'cost (calls)':>13s}")
    print("  " + "-" * 54)
    for m in methodes:
        mrr_m, rap_m = resultats[m]
        cout_total = COUT[m] * len(queries)
        print(f"  {m:<16s} | {mrr_m:6.3f} | {rap_m:9.0%} | {cout_total:13d}")

    # --- The routeur : the good method for each query -----------------
    mrr_router, rap_routeur, cout_routeur = [], [], 0
    detail_routeur = []
    for req in queries:
        choix = Q.router(req["question"], req.get("history", []))
        cl = classement_methode(choix, req["question"],
                                req.get("history", []), R)
        mrr_router.append(Q.mrr(cl, req["relevant"]))
        rap_routeur.append(Q.rappel_at_k(cl, req["relevant"], k=5))
        cout_routeur += COUT[choix]
        detail_routeur.append((req["question"][:40], choix))

    print("\n" + "=" * 78)
    print("THE ROUTER — THE RIGHT METHOD PER QUERY (see Lab 21-5)")
    print("=" * 78)
    for q, choix in detail_routeur:
        print(f"  \"{q}\" -> {choix}")
    print(f"\n  {'ROUTEUR':<16s} | {sum(mrr_router)/len(mrr_router):6.3f} | "
          f"{sum(rap_routeur)/len(rap_routeur):9.0%} | {cout_routeur:13d}")

    # --- Lecture -----------------------------------------------------------
    meilleure_unique = max(methodes, key=lambda m: resultats[m][0])
    print("\n" + "=" * 78)
    print("LECTURE")
    print("=" * 78)
    print("- No single method wins on every type: the best on average")
    print(f"  ({meilleure_unique}, MRR {resultats[meilleure_unique][0]:.3f}) reste battue,")
    print("  query by query, by another depending on the case.")
    print(f"- The router (MRR {sum(mrr_router)/len(mrr_router):.3f}) picks the right")
    print(f"  strategy each time, at a controlled cost ({cout_routeur} calls instead")
    print(f"  of {len(methodes)}x if everything were tried).")
    print("- HyDE and expansion shine on distant vocabulary; decomposition on compound")
    print("  questions; rewriting on pronouns; the step-back on over-specific cases.")
    print("  Each has ITS OWN ground.")

    print("\nWHAT TO REMEMBER")
    print("- The benchmark proves there is no universal transformation.")
    print("- Measuring (MRR, recall@5, cost) is the only way to choose knowingly.")
    print("- The adaptive router beats the single methods, at a lower cost.")
    print("\n  (A caution if you transpose this to your own data: the benchmark is")
    print("   illustrative, on a small deterministic corpus. Redo it on YOUR real queries.)")


if __name__ == "__main__":
    main()
