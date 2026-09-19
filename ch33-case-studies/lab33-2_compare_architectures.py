# -*- coding: utf-8 -*-
"""
Lab 33-2 — Comparing architectures
"The trade-off between cost, quality and latency"

The aim: compare a classic vector stack with a hybrid one (BM25 plus vectors
plus reranking), and show that "richer" is not always "better": it all depends on
the specification.

The real case: Julien hesitates between two stacks for the aerospace
documentation base. Sophie runs an e-commerce support desk where latency is
king — and the same "rich" choice that wins for Julien can lose for Sophie.

Two of the reference architectures are deliberate counter-examples. They must
score BADLY against the specifications they do not fit; that is the point.

No API key. Run generate_corpus.py first.
"""

from archikit import (bandeau, Architecture, compare, evaluate,
                      load_architectures)
import archikit


def ligne(nom, ev):
    p = ev["profil"]
    return (f"  {nom:<26} score {ev['score_final']:>5}/100  "
            f"| Q {p['qualite']:.2f} C {p['cout']:.2f} "
            f"L {p['latence']:.2f} S {p['securite']:.2f}"
            f"  {'ok' if ev['conforme'] else str(len(ev['violations']))+' viol.'}")


def main():
    bandeau("Lab 33-2 — Comparer deux architectures")
    cahiers = archikit.CAHIERS
    archis = load_architectures()

    # ---- 1) Classic vector against hybrid plus graph, on the aerospace spec ----
    print("\n[1] AEROSPACE — classic vector against hybrid")
    print("─" * 74)
    cahier = cahiers["aeronautique"]
    # Build a "classic vector" variant of the aerospace architecture on the fly.
    aero = archis["Aerospace (maintenance)"]
    vectoriel = Architecture(
        nom="Aerospace classic vector",
        choix={**aero.choix, "retrieval": "vectoriel", "reranking": "aucun"})
    cmp = compare(vectoriel, aero, cahier)
    print(ligne(cmp["a"]["nom"], evaluate(vectoriel, cahier)))
    print(ligne(cmp["b"]["nom"], evaluate(aero, cahier)))
    print(f"  -> Winner: {cmp['gagnant']} (gap {cmp['ecart']} pts)")
    print("    Hybrid plus reranking pays here: quality weighs 45% and latency")
    print("    is tolerated, because it is workshop use.")

    # ---- 2) Rich against cut-to-the-need, on e-commerce ----
    print("\n[2] E-COMMERCE — rich against cut to the need")
    print("─" * 74)
    cahier = cahiers["ecommerce"]
    riche = archis["E-commerce (over-secured)"]
    taille = archis["E-commerce (support)"]
    cmp2 = compare(riche, taille, cahier)
    print(ligne(riche.nom, evaluate(riche, cahier)))
    print(ligne(taille.nom, evaluate(taille, cahier)))
    print(f"  -> Winner: {cmp2['gagnant']} (gap {cmp2['ecart']} pts)")
    print("    Here the \"rich\" one LOSES: latency weighs 35%, cost 25%. LLM")
    print("    reranking and sovereign hosting sink a use where an error is")
    print("    cheap. Richer is not better.")

    # ---- 3) The same choice, two opposed verdicts ----
    print("\n[3] THE SAME CHOICE, TWO VERDICTS — according to the specification")
    print("─" * 74)
    riche_globale = archis["Rich (everything on)"]
    for cle in ("aeronautique", "ecommerce"):
        ev = evaluate(riche_globale, cahiers[cle])
        print(f"  \"Rich (everything on)\" on {cle:<13}: "
              f"{ev['score_final']:>5}/100 "
              f"({'conforme' if ev['conforme'] else str(len(ev['violations']))+' violation(s)'})")
    print("  -> The same \"maximal\" architecture is correct in aerospace and")
    print("     unsuited in e-commerce. The context decides, not the richness.")

    print("\n" + "═" * 74)
    print("THE MESSAGE: comparing is not looking for the most powerful stack,")
    print("it is measuring the TRADE-OFF on the axes the business values. A hybrid")
    print("RAG beats the vector one when quality comes first; it loses when latency")
    print("and cost dominate. The recommendation depends on the specification.")


if __name__ == "__main__":
    main()
