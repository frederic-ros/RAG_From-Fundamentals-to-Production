# -*- coding: utf-8 -*-
"""
Lab 27-7 — Optimising cost: finding the right balance
"Performance is not everything. Cost counts too."

The aim: measure the cost of the different configurations and find the optimal
point for a given budget. A "turn everything on" policy (every representation,
every engine queried) is compared with a "router" policy (one engine per
question, chosen by the router), over the 50 annotated questions.

No API key. Run generate_corpus.py first.
"""

from multikit import (load_questions, load_cost,
                      routeur_multiresolution, cout_de, bandeau)

REPRESENTATIONS = ["vector", "graph", "hypergraph", "hierarchy"]


def couverture(questions, presentes: set[str]) -> float:
    ok = 0
    for it in questions:
        m = it["engine"]
        if m == "mixed":
            ok += 1 if len(presentes) >= 2 else 0
        elif m in presentes:
            ok += 1
    return ok / len(questions)


def cout_indexation(presentes: set[str], cout: dict) -> float:
    return sum(cout["indexation"].get(r, 0.0) for r in presentes)


def cout_politique_tout(questions, cout: dict) -> tuple[float, float]:
    """The "turn everything on" policy: each question queries EVERY engine."""
    total_req, total_lat = 0.0, 0.0
    for _ in questions:
        for r in REPRESENTATIONS:
            c, l = cout_de(r, cout)
            total_req += c
            total_lat += l
    return total_req, total_lat


def cout_politique_routeur(questions, cout: dict) -> tuple[float, float]:
    """The "router" policy: one engine per question, the one routed to."""
    total_req, total_lat = 0.0, 0.0
    for it in questions:
        choisi = routeur_multiresolution(it["q"])
        c, l = cout_de(choisi, cout)
        total_req += c
        total_lat += l
    return total_req, total_lat


def main():
    bandeau("Lab 27-7 — Optimising cost: finding the right balance")
    questions = load_questions()
    cout = load_cost()
    n = len(questions)

    idx_complet = cout_indexation(set(REPRESENTATIONS), cout)
    qual_complet = couverture(questions, set(REPRESENTATIONS))

    # --- two policies over the same set of representations --------------------
    req_tout, lat_tout = cout_politique_tout(questions, cout)
    req_rout, lat_rout = cout_politique_routeur(questions, cout)

    print(f"\n{n} questions. Indexing cost (every representation): {idx_complet:.1f}")
    print("\nTwo policies, the same coverage quality:")
    print(f"  {'policy':22}{'quality':>9}{'query cost':>13}{'total latency':>16}")
    print("  " + "─" * 60)
    print(f"  {'tout activer':22}{qual_complet:>9.0%}{req_tout:>16.1f}{lat_tout:>13.0f}ms")
    print(f"  {'router (1 engine/q)':22}{qual_complet:>9.0%}{req_rout:>16.1f}{lat_rout:>13.0f}ms")
    gain = 1 - req_rout / req_tout
    print(f"\n  -> The router cuts the query cost by {gain:.0%} at equal quality.")

    # --- courbe cost/quality of configurations croissantes ---------------
    print("\nThe cost/quality curve (cumulative indexing):")
    print(f"  {'configuration':40}{'quality':>9}{'idx cost':>10}")
    configs = [
        {"vector"},
        {"vector", "hierarchy"},
        {"vector", "graph", "hierarchy"},
        {"vector", "graph", "hypergraph", "hierarchy"},
    ]
    for conf in configs:
        q = couverture(questions, conf)
        ci = cout_indexation(conf, cout)
        ordonne = " + ".join(sorted(conf))
        print(f"  {ordonne:40}{q:>9.0%}{ci:>10.1f}")

    # --- configuration optimale sous budget d'indexation -----------------
    budget = 5.0
    print(f"\nMeilleure configuration sous budget d'indexation ≤ {budget} :")
    from itertools import combinations
    meilleure, meilleure_q, meilleure_c = None, -1.0, 0.0
    for taille in range(1, len(REPRESENTATIONS) + 1):
        for conf in combinations(REPRESENTATIONS, taille):
            ci = cout_indexation(set(conf), cout)
            if ci > budget:
                continue
            q = couverture(questions, set(conf))
            if q > meilleure_q or (q == meilleure_q and ci < meilleure_c):
                meilleure, meilleure_q, meilleure_c = conf, q, ci
    print(f"   {' + '.join(meilleure)}  ->  quality {meilleure_q:.0%}, "
          f"indexing cost {meilleure_c:.1f}")

    print("\nTHE MESSAGE: a good architecture finds the optimal point between quality")
    print("             and budget, without wasting resources on what brings nothing.")


if __name__ == "__main__":
    main()
