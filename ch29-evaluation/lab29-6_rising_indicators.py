# -*- coding: utf-8 -*-
"""
Lab 29-6 — The rising indicators: the attribution rate (citation rate)
"An answer without a source is an assertion; with one, it is evidence"

The aim: measure two "rising" indicators of the chapter, the ones that separate
an impressive RAG from a trustworthy one:

  - the ATTRIBUTION rate: does the answer point to the source that supports it?
    Is each assertion traceable to a fragment?
  - the PRECISION of the citation: does the source cited really support the
    assertion, or is it a citation of convenience?

The steps: generate answers citing the fragments used; measure the attribution
rate (answers supported by a real source); check the precision — does the source
cited actually hold the answer? — and exhibit a citation of convenience, a source
cited but not supporting.

No API key. Run generate_corpus.py first.
"""

from evalkit import (RAGPipeline, load_fragments, load_golden,
                     juge_fidelite, taux_attribution, bandeau)


def main():
    bandeau("Lab 29-6 — The rising indicators: attribution and citation")
    docs = load_fragments()
    golden = load_golden()
    pipe = RAGPipeline(docs, k=3)

    reponses = []
    print(f"\n{'Q':<5}{'cites':>8}{'attrib.':>9}{'cite_ok':>10}  source cited")
    print("─" * 60)

    bien_cites = 0
    total_repondus = 0
    for g in golden:
        if g["category"] == "out_of_corpus":
            continue
        rep = pipe.repondre(g["question"])
        reponses.append(rep)
        if rep.abstention or not rep.fragments:
            continue
        total_repondus += 1
        source = rep.fragments[0]
        cite = source["id"]
        attribue = source["score"] > 0

        # Is the citation CORRECT? Is the source cited among the
        # fragments attendus of the golden set ?
        cite_juste = cite in g["expected_fragments"] if g["expected_fragments"] else False
        if cite_juste:
            bien_cites += 1
        marque = "✅" if cite_juste else "—"
        print(f"{g['id']:<5}{'yes':>8}{'yes' if attribue else 'no':>9}"
              f"{marque:>10}    {cite} ({source['titre'][:24]})")

    taux_attr = taux_attribution(reponses)
    prec_cit = bien_cites / total_repondus if total_repondus else 0.0
    print("─" * 60)
    print(f"\nTaux d'attribution        : {taux_attr:.0%}  "
          "(answers supported by a real source)")
    print(f"Precision of the citations: {prec_cit:.0%}  "
          "(source cited = source expected)")

    # === a citation of convenience =======================================
    print("\n" + "─" * 60)
    print("A CITATION OF CONVENIENCE (an anti-pattern):")
    print("  Answer: \"Cavitation is corrected by doubling the speed. [D03]\"")
    d03 = next(d["texte"] for d in docs if d["id"] == "D03")
    affirmation = "Cavitation is corrected by doubling the speed."
    soutien = juge_fidelite(affirmation, d03)
    print(f"  Does the cited source [D03] support the assertion? "
          f"fidelity = {soutien:.2f}")
    print("  -> the citation exists BUT does not support the claim. Citing a")
    print("     a source is not enough: you must check it says what the answer")
    print("     claims. That is the difference between attribution and fidelity.")

    print("\n" + "═" * 60)
    print("THE MESSAGE: the attribution rate is a RISING indicator — it does not say")
    print("THE MESSAGE: the rising indicators measure not only that the answer is")
    print("correct but that it is TRACEABLE. In a critical context, an answer")
    print("verifiable through its source is worth more than a correct but")
    print("unverifiable one. Attribution AND fidelity of the citation: the two")
    print("together make trust.")


if __name__ == "__main__":
    main()
