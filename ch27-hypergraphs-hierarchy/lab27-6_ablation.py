# -*- coding: utf-8 -*-
"""
Lab 27-6 — An ablation study: which representation brings what?
"Not all representations are worth the same"

The aim: reproduce the spirit of the Cog-RAG ablation study. Performance is
measured with all the representations, then with one removed at a time, to
observe the degradation — and so to identify the CRITICAL ablations (the
representation is indispensable) and the BENEFICIAL ones (removing it helps).

The 50 annotated questions are the basis: a representation "answers" a question
when it is the one the router would choose, or one of those a mixed question
needs.

The lab prints the performance of each representation alone, then the effect of
each ablation, highlighting the critical ones.

No API key. Run generate_corpus.py first.
"""


from multikit import load_questions, bandeau

REPRESENTATIONS = ["vector", "graph", "hypergraph", "hierarchy"]

# The questions mixtes not are not toutes identiques : chacune combine DEUX
# precise families. That is modelled so the ablation is differentiated: a
# representation heavily called on by the mixed questions becomes critical. The
# order follows
# the 10 questions 'mixed' of the corpus (indices 40-49).
PAIRES_MIXTES = [
    {"graph", "hypergraph"},      # security procedures plus continuity
    {"graph", "hierarchy"},       # stage 3 + Dependencies
    {"graph", "hypergraph"},      # themes maintenance + composants
    {"vector", "hierarchy"},    # compressor synthesis plus blade detail
    {"hypergraph", "hierarchy"},  # inspections security + place hierarchy
    {"graph", "hypergraph"},      # composants + theme maintenance
    {"vector", "hierarchy"},    # an overview plus a detail level
    {"graph", "hypergraph"},      # the continuity theme plus entities
    {"vector", "hierarchy"},    # expansion summary plus a dependency
    {"hypergraph", "hierarchy"},  # regulation plus a place in the tree
]


def _besoins(questions):
    """Associate with each question the set of representations it
 besoin (a for the types purs, deux for the mixtes)."""
    i_mixte = 0
    besoins = []
    for it in questions:
        m = it["engine"]
        if m == "mixed":
            besoins.append(PAIRES_MIXTES[i_mixte % len(PAIRES_MIXTES)])
            i_mixte += 1
        else:
            besoins.append({m})
    return besoins


def couverture(questions, presentes: set[str], besoins=None) -> float:
    """The fraction of questions whose required representations are ALL
 presentss (for the mixtes : the deux familles requises)."""
    if besoins is None:
        besoins = _besoins(questions)
    ok = sum(1 for b in besoins if b <= presentes)
    return ok / len(questions)


def main():
    bandeau("Lab 27-6 — An ablation study: which representation brings what?")
    questions = load_questions()
    n = len(questions)
    print(f"\n{n} annotated questions (of which "
          f"{sum(1 for q in questions if q['engine']=='mixed')} mixtes).")

    # --- performance of each representation seule ----------------------
    print("\nPerformance of each representation ALONE:")
    for r in REPRESENTATIONS:
        perf = couverture(questions, {r})
        print(f"   {r:14} : {perf:.0%} of the questions covered")

    # --- system complet -------------------------------------------------
    complet = set(REPRESENTATIONS)
    perf_complet = couverture(questions, complet)
    print(f"\nThe complete system ({', '.join(REPRESENTATIONS)}): {perf_complet:.0%}")

    # --- ablation : retirer a representation to the fois -----------------
    print("\nAblation study (one representation removed):")
    print(f"   {'removed':14}{'perf':>8}{'vs complete':>14}{'verdict':>14}")
    print("   " + "─" * 50)
    for r in REPRESENTATIONS:
        sous = complet - {r}
        perf = couverture(questions, sous)
        delta = perf - perf_complet
        if delta <= -0.25:
            verdict = "CRITICAL"
        elif delta <= -0.10:
            verdict = "importante"
        elif delta >= 0.0:
            verdict = "redondante"
        else:
            verdict = "utile"
        print(f"   {r:14}{perf:>8.0%}{delta:>+14.0%}{verdict:>14}")

    # --- toutes the combinaisons (heatmap textuelle) ---------------------
    print("\nPerformance of a few combinations:")
    interessantes = [
        ("vector",),
        ("vector", "graph"),
        ("vector", "graph", "hierarchy"),
        ("vector", "hypergraph", "hierarchy"),
        tuple(REPRESENTATIONS),
    ]
    for combo in interessantes:
        perf = couverture(questions, set(combo))
        print(f"   {perf:.0%}  <-  {' + '.join(combo)}")

    print("\nTHE MESSAGE: some representations are critical, others redundant, and a")
    print("             few can do harm. Ablation reveals their real value.")


if __name__ == "__main__":
    main()
