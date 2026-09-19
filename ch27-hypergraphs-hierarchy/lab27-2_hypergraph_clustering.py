# -*- coding: utf-8 -*-
"""
Lab 27-2 — Building hypergraphs automatically: discovering the themes
"The hard part is not the hypergraph, it is finding the right themes"

The aim: discover the crossing themes automatically by clustering (k-means, or
HDBSCAN if installed), measuring purity against a ground truth.

A real case: 30 inspection reports spread across 5 domains (maintenance,
security, quality, environment, process safety). We try to recover those domains
automatically, without knowing them in advance.

The lab prints the themes found, their purity and their coherence. Clustering
AMPLIFIES the structure already present in the text; it does not invent it.

No API key. Run generate_corpus.py first.
"""

import time

import numpy as np

from multikit import (Embedder, Hypergraph, load_inspections,
                      build_hypergraph_themes, bandeau, _a_hdbscan)


def purete_domaines(hg: Hypergraph, par_id: dict) -> float:
    """Purity: each cluster is labelled by its majority domain;
    the fraction of documents whose domain is the majority domain of the cluster."""
    total, corrects = 0, 0
    for membres in hg.hyperaretes.values():
        if not membres:
            continue
        doms = [par_id[m]["domain"] for m in membres]
        majoritaire = max(set(doms), key=doms.count)
        corrects += doms.count(majoritaire)
        total += len(doms)
    return corrects / total if total else 0.0


def coherence(hg: Hypergraph, emb: Embedder, index: dict) -> float:
    """Coherence interne moyenne : similarity intra-cluster moyenne."""
    sims = []
    for membres in hg.hyperaretes.values():
        idx = [index[m] for m in membres if m in index]
        if len(idx) < 2:
            continue
        sub = emb.matrice[idx]
        s = sub @ sub.T
        n = len(idx)
        sims.append((s.sum() - n) / (n * (n - 1)))  # hors diagonale
    return float(np.mean(sims)) if sims else 0.0


def main():
    bandeau("Lab 27-2 — Building hypergraphs automatically")
    rapports = load_inspections()
    par_id = {r["id"]: r for r in rapports}
    n_dom = len(set(r["domain"] for r in rapports))
    print(f"\n{len(rapports)} reports, {n_dom} real domains (the ground truth).")

    emb = Embedder([r["content"] for r in rapports])
    index = {r["id"]: i for i, r in enumerate(rapports)}

    print(f"\n{'method':16}{'k':>4}{'themes':>8}{'purity':>9}{'coherence':>11}{'time':>8}")
    print("─" * 60)

    # --- k-means for several k ----------------------------------------
    for k in (3, 5, 7):
        t0 = time.perf_counter()
        hg = build_hypergraph_themes(rapports, k=k, methode="kmeans")
        dt = (time.perf_counter() - t0) * 1000
        print(f"{'k-means':16}{k:>4}{len(hg.hyperaretes):>8}"
              f"{purete_domaines(hg, par_id):>9.2f}"
              f"{coherence(hg, emb, index):>11.2f}{dt:>7.0f}ms")

    # --- HDBSCAN si present ----------------------------------------------
    if _a_hdbscan():
        t0 = time.perf_counter()
        hg = build_hypergraph_themes(rapports, methode="hdbscan")
        dt = (time.perf_counter() - t0) * 1000
        print(f"{'HDBSCAN':16}{'-':>4}{len(hg.hyperaretes):>8}"
              f"{purete_domaines(hg, par_id):>9.2f}"
              f"{coherence(hg, emb, index):>11.2f}{dt:>7.0f}ms")
    else:
        print(f"{'HDBSCAN':16}{'-':>4}{'(not installed: pip install hdbscan)':>38}")

    # --- Inspection qualitative of the meilleur k=5 (= nb of domaines real) --
    print("\n" + "─" * 74)
    print("Themes discovered with k=5 (to compare with the 5 real domains):")
    hg = build_hypergraph_themes(rapports, k=5, methode="kmeans")
    for theme, membres in hg.hyperaretes.items():
        doms = [par_id[m]["domain"] for m in membres]
        majoritaire = max(set(doms), key=doms.count)
        print(f"   ⬡ {theme} ({len(membres)} docs) — dominant domain: {majoritaire}")

    print("\nTHE MESSAGE: building the hypergraph is easy; finding the RIGHT themes")
    print("             is the real challenge. Clustering amplifies the structure,")
    print("             it does not invent it.")


if __name__ == "__main__":
    main()
