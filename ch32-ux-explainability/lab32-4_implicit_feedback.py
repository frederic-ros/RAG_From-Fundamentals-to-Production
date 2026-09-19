# -*- coding: utf-8 -*-
"""
Lab 32-4 — Implicit feedback: what the buttons miss
"A source read for a long time is a silent yes; an immediate reformulation is a no"

Behavioural signals are collected — source reading and its duration, copying,
reformulating, abandoning — and translated into plus or minus, with no explicit
click. Aggregated per query and per document, they point at what needs fixing.

The lab closes the loop: the signals reinforce the score of the relevant
fragments, validate the prompts, and raise an alarm on the chunking — then the
next cycle measures again.

The forced signals in generate_corpus.py name one query verbatim, to make it
plainly problematic. That query text must match one of the answers, or there is
nothing to aggregate the signals onto.

No API key. Run generate_corpus.py first.
"""

from collections import Counter

from uxkit import (bandeau, signal_implicite, agreger_signaux,
                  load_signals)


def diagnostiquer(requete: str, score: float) -> str:
    """Link a negative score to a probable cause and a fix."""
    if "purge" in requete.lower():
        return ("contradiction de sources → revoir la gouvernance (Lab 31-2) et "
                "reranking by freshness")
    if score <= -0.5:
        return "answers judged off-topic -> check the chunking and the retrieval"
    return "mixed satisfaction -> refine the generation prompt"


def main():
    bandeau("Lab 32-4 — Feedback implicite et analyse comportementale")
    signaux = load_signals()

    # ---- 1) Traduction comportements in signaux ----
    print("\n[1] DETECTING THE BEHAVIOURAL SIGNALS")
    print("─" * 74)
    types = Counter(s["type"] for s in signaux)
    polarites = Counter()
    for s in signaux:
        sig = signal_implicite(s)
        pol = "positif" if sig["signal"] > 0 else \
              "negative" if sig["signal"] < 0 else "neutral"
        polarites[pol] += 1
    print(f"  {len(signaux)} events captured. Split by type:")
    for t, n in types.most_common():
        print(f"     {t:<18} : {n}")
    print(f"  Polarity: positive={polarites['positif']}  "
          f"negative={polarites['negative']}  neutral={polarites['neutral']}")
    print("  (No explicit click required: it all comes from natural behaviour.)")

    # ---- 2) Aggregation: the usability indicators ----
    print("\n[2] THE DASHBOARD — a usability score")
    print("─" * 74)
    agg = agreger_signaux(signaux)
    print("  By document (mean score, sorted):")
    for doc, sc in sorted(agg["par_document"].items(), key=lambda x: x[1]):
        barre = "▇" * int(abs(sc) * 10)
        signe = "−" if sc < 0 else "+"
        print(f"     {doc:<22} {signe}{abs(sc):.2f} {barre}")

    # ---- 3) Queries problematics ----
    print("\n[3] PROBLEMATIC QUERIES (a negative signal)")
    print("─" * 74)
    if agg["requetes_problematiques"]:
        for q in agg["requetes_problematiques"]:
            sc = agg["par_requete"][q]
            print(f"  ({sc:+.2f}) \"{q[:54]}\"")
    else:
        print("  No clearly problematic query in this sample.")

    # ---- 4) A prioritised improvement plan ----
    print("\n[4] A PRIORITISED IMPROVEMENT PLAN (the feedback loop closed)")
    print("─" * 74)
    classees = sorted(agg["par_requete"].items(), key=lambda x: x[1])
    for rank, (q, sc) in enumerate(classees[:3], 1):
        if sc >= 0:
            break
        print(f"  {rank}. \"{q[:46]}\" (score {sc:+.2f})")
        print(f"     → {diagnostiquer(q, sc)}")
    print("\n  The loop closed: the signals reinforce the score of the relevant")
    print("  relevant ones, validate the prompts, and raise an alarm on the chunking —")
    print("  puis on re-mesure au cycle suivant.")

    print("\n" + "═" * 74)
    print("THE MESSAGE: implicit feedback captures what the buttons miss.")
    print("A source read for a long time, a copy: so many silent \"yes\" answers.")
    print("An immediate reformulation: a \"no\". Aggregated, these signals drive the")
    print("continuous improvement of the pipeline, without asking the user for")
    print("anything.")


if __name__ == "__main__":
    main()
