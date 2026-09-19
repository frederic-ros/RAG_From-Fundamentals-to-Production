# -*- coding: utf-8 -*-
"""
Lab 33-1 — Designing a business RAG
"Start from the need and work back to the assembly"

The aim: produce the architecture dossier for a RAG in an imposed domain, and
justify EACH technical choice against the specification.

The case: Claire's banking compliance assistant. A very low tolerance for error,
strongly interdependent regulatory documents, high confidentiality.

The steps: read the specification, choose one block per storey, evaluate the
result (score plus constraint violations), then iterate — showing that a naive
architecture violates the constraints and a justified one respects them.

The mechanism here is NUMERIC (weights, profiles, caps), so it survives
translation untouched.

No API key. Run generate_corpus.py first.
"""

from archikit import bandeau, Architecture, evaluate, BRIQUES, load_architectures
import archikit


def show_archi(archi: Architecture):
    for etage, brique in archi.choix.items():
        prof = BRIQUES[etage][brique]
        print(f"     {etage:<12}: {brique:<20} ({prof.note})")


def main():
    bandeau("Lab 33-1 — Designing a business RAG (domain: banking)")
    cahiers = archikit.CAHIERS
    cahier = cahiers["banque"]
    archis = load_architectures()

    print(f"\nSPECIFICATION — {cahier.nom} ({cahier.domaine})")
    print("─" * 74)
    print(f"  {cahier.note}")
    print(f"  Weights: quality {cahier.poids['qualite']:.0%} - "
          f"cost {cahier.poids['cout']:.0%} - "
          f"latence {cahier.poids['latence']:.0%} · "
          f"security {cahier.poids['securite']:.0%}")
    print(f"  Contraintes dures : latence ≤ {cahier.latence_max:.2f}, "
          f"security >= {cahier.securite_min:.2f}, "
          f"interdependencies = {cahier.interdependances}")

    # ---- 1) A NAIVE attempt (low-cost): it violates the constraints ----
    print("\n[1] A NAIVE ATTEMPT — the low-cost architecture")
    print("─" * 74)
    naive = archis["Minimal (low-cost)"]
    show_archi(naive)
    ev_naive = evaluate(naive, cahier)
    print(f"  Score : {ev_naive['score_final']}/100  "
          f"(conforme : {ev_naive['conforme']})")
    for v in ev_naive["violations"]:
        print(f"     ✗ {v}")

    # ---- 2) A JUSTIFIED architecture for the bank ----
    print("\n[2] A JUSTIFIED ARCHITECTURE — cut for banking compliance")
    print("─" * 74)
    banque = archis["Banking (compliance)"]
    show_archi(banque)
    ev = evaluate(banque, cahier)
    print(f"\n  Score : {ev['score_final']}/100  (conforme : {ev['conforme']})")
    prof = ev["profil"]
    print(f"  Overall profile: quality {prof['qualite']:.2f} - "
          f"cost {prof['cout']:.2f} - latency {prof['latence']:.2f} - "
          f"security {prof['securite']:.2f}")
    if ev["violations"]:
        for v in ev["violations"]:
            print(f"     ✗ {v}")
    else:
        print("     Every hard constraint is respected.")

    # ---- 3) Justification brique by brique ----
    print("\n[3] RATIONALE FOR THE STRUCTURAL CHOICES")
    print("─" * 74)
    for etage, just in banque.justification.items():
        print(f"  · {etage:<12}: {just}")

    # ---- 4) Dossier of architecture (synthesis) ----
    print("\n[4] THE ARCHITECTURE DOSSIER (a defensible synthesis)")
    print("─" * 74)
    print("  From the raw document to the interface:")
    print("   parsing -> chunking -> retrieval -> reranking -> generation -> UX,")
    print("   with security running across all of it (ABAC, audit, sovereignty).")
    print("  The graph at the retrieval answers the regulatory interdependencies;")
    print("  sovereignty answers the confidentiality; citations plus trust states")
    print("  answer the near-zero tolerance for error.")

    print("\n" + "═" * 74)
    print("THE MESSAGE: the right architecture is not the richest, it is the one")
    print("that solves the specification. You start from the need — low error,")
    print("interdependencies, confidentiality — and work back to the blocks: a")
    print("reverse design matrix. Each choice is defended by a trade-off.")


if __name__ == "__main__":
    main()
