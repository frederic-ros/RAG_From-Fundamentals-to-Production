# -*- coding: utf-8 -*-
"""
Lab 21-2 — HyDE: searching for the answer rather than the question

Learning objective
------------------
HyDE (Hypothetical Document Embeddings) reverses the usual move: first an answer
is INVENTED — never mind whether it is correct — and then the search is run with
that hypothetical document.

Why? Because the false answer is itself written in the language of the real
documents. It serves as a bridge across the vocabulary gap.

    A false answer already speaks the language of the real documents.

This lab applies HyDE to "Why does motor M-18 run hot?", compares it with the
direct search, and puts the gain in figures. It also says plainly when HyDE
does NOT help.

No API key: the hypothetical document is generated deterministically.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import qtlib as Q

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 21-2 — HyDE: searching for the answer rather than the question")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    R = Q.Search(texts)
    print(f"\nMode de search : {Q.mode()}")

    best = 1
    question = "Why does motor M-18 run hot?"
    print(f"\nQuestion: \"{question}\"")
    print(f"Expected right document: #{best} — \"{texts[best][:60].strip()}…\"")

    # --- 1) Search directe ----------------------------------------------
    direct = [i for i, _ in R.classer(question)]
    rank_direct = Q.rank_of(direct, best)
    print("\n" + "=" * 78)
    print("1) DIRECT SEARCH")
    print("=" * 78)
    for rank, (i, s) in enumerate(R.classer(question)[:5], start=1):
        mark = "  <-- le best" if i == best else ""
        print(f"  rank {rank} : #{i:2d} [{frags[i]['subject']}]{mark}")
    print(f"  -> The best document sits at rank {rank_direct}.")

    # --- 2) HyDE -----------------------------------------------------------
    doc_hypo = Q.hyde(question)
    hyde_cl = [i for i, _ in R.classer(doc_hypo)]
    rank_hyde = Q.rank_of(hyde_cl, best)
    print("\n" + "=" * 78)
    print("2) HyDE — an answer is invented first, then searched with")
    print("=" * 78)
    print("  Hypothetical document generated (a false answer, but the right vocabulary):")
    print(f"    \"{doc_hypo}\"")
    print("\n  Search with that hypothetical document:")
    for rank, (i, s) in enumerate(R.classer(doc_hypo)[:3], start=1):
        mark = "  <-- the good one, lifted" if i == best else ""
        print(f"  rank {rank} : #{i:2d} [{frags[i]['subject']}]{mark}")
    print(f"  -> The best document sits at rank {rank_hyde}.")

    # --- 3) Comparaison with the expansion -----------------------------------
    reforms = Q.expansion(question)
    exp_cl = [i for i, _ in R.classer_multi(reforms)]
    rank_exp = Q.rank_of(exp_cl, best)
    print("\n" + "=" * 78)
    print("3) COMPARISON WITH THE EXPANSION")
    print("=" * 78)
    print(f"  Reformulations : {reforms}")
    print(f"  -> With the expansion, the best document sits at rank {rank_exp}.")

    # --- 4) Metrics ------------------------------------------------------
    print("\n" + "=" * 78)
    print("4) THE GAIN, IN FIGURES (MRR)")
    print("=" * 78)
    print(f"  {'method':<16s} | {'rank of right doc':>17s} | {'MRR':>6s}")
    print("  " + "-" * 44)
    for nom, cl in [("directe", direct), ("expansion", exp_cl), ("HyDE", hyde_cl)]:
        r = Q.rank_of(cl, best)
        print(f"  {nom:<16s} | {str(r):>15s} | {Q.mrr(cl, [best]):6.3f}")

    print("\n" + "=" * 78)
    print("LE RISQUE DE HyDE")
    print("=" * 78)
    print("- HyDE shines when the model \"knows the shape\" of the answer, on common")
    print("  technical subjects: the false answer then uses the right vocabulary.")
    print("- But if the invention goes astray (an outright hallucination on a subject")
    print("  niche subject, the hypothetical document becomes a BAD key and sends the")
    print("  search astray. Use HyDE knowingly, not by reflex.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The right document was found by searching for an INVENTED answer.")
    print("- The hypothetical document is a BRIDGE between the language of the problem")
    print("  of the question) and the language of the solution (the real documents).")
    print("- Here HyDE and expansion tie, because the code M-18 stays recoverable;")
    print("  the gap opens in HyDE's favour when the question holds NO usable technical")
    print("  term at all — which was the case of the \"odd noise\" in Lab 21-1.")

    print("\nWHAT TO REMEMBER")
    print("- HyDE looks for a document resembling the ANSWER, not the question.")
    print("- A well-phrased false answer already speaks the language of the real documents.")
    print("- Handle with care: a hallucination becomes a bad key.")


if __name__ == "__main__":
    main()
