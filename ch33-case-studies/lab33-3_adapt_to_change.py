# -*- coding: utf-8 -*-
"""
Lab 33-3 — Adapting an architecture to a change of need
"Adapting is not rebuilding everything"

The aim: take a working architecture, change the specification under it, and
identify which storeys the new need puts at fault — then make those storeys, and
only those, evolve.

The lab then VERIFIES that the regressions have been removed without degrading
the rest. An architecture is a living thing.

No API key. Run generate_corpus.py first.
"""

from archikit import bandeau, analyze_impact, load_architectures
import archikit


def main():
    bandeau("Lab 33-3 — Adapting the pipeline to a change of business need")
    cahiers = archikit.CAHIERS
    archis = load_architectures()

    # The original architecture: the light e-commerce stack, designed for another
    # need, which we try (wrongly) to reuse for aerospace.
    origine = archis["E-commerce (support)"]
    cahier_avant = cahiers["ecommerce"]
    cahier_apres = cahiers["aeronautique"]

    print(f"\nOriginal architecture: \"{origine.nom}\"")
    print(f"Change of need: {cahier_avant.domaine} -> {cahier_apres.domaine}")
    print(f"  Nouveau besoin : {cahier_apres.note}")

    # ---- 1) The regression, with no adaptation ----
    print("\n[1] REGRESSION WITH NO ADAPTATION")
    print("─" * 74)
    impact_brut = analyze_impact(origine, cahier_avant, cahier_apres, modifs=None)
    print(f"  Original score in the original context: "
          f"{impact_brut['score_origine_contexte_origine']}/100")
    print(f"  The same architecture, a new context (aerospace): "
          f"{impact_brut['score_origine_contexte_nouveau']}/100")
    print(f"  -> Regression: "
          f"{impact_brut['regression_sans_adaptation']} pts")
    print("  Violations introduites :")
    for v in impact_brut["violations_avant_adaptation"]:
        print(f"     ✗ {v}")

    # ---- 2) A targeted adaptation ----
    print("\n[2] A TARGETED ADAPTATION (minimal modifications)")
    print("─" * 74)
    modifs = {
        "parsing": "multimodal",        # scanned plans
        "chunking": "hierarchique",     # documents techniques denses
        "reranking": "cross_encoder",   # precision technique
        "generation": "modele_specialise",
        "securite": "abac_audit",       # exigence of governance
        "ux": "citations_confiance",
    }
    print("  Modifications applied:")
    for etage, brique in modifs.items():
        print(f"     {etage:<12}: {origine.choix[etage]:<16} → {brique}")

    impact = analyze_impact(origine, cahier_avant, cahier_apres, modifs=modifs)
    print(f"\n  Score after adaptation: "
          f"{impact['score_adapte_contexte_nouveau']}/100")
    print(f"  → Gain de l'adaptation : +{impact['gain_adaptation']} pts")
    if impact["violations_apres_adaptation"]:
        print("  Violations restantes :")
        for v in impact["violations_apres_adaptation"]:
            print(f"     ✗ {v}")
    else:
        print("     No violation left: conformity restored.")

    # ---- 3) Schema before and after ----
    print("\n[3] BEFORE AND AFTER (the storeys touched)")
    print("─" * 74)
    print(f"  {'storey':<12}{'before':<20}{'after':<20}")
    print("  " + "─" * 52)
    for etage in origine.choix:
        avant = origine.choix[etage]
        apres = modifs.get(etage, avant)
        marque = "  <-modified" if etage in modifs else ""
        print(f"  {etage:<12}{avant:<20}{apres:<20}{marque}")

    print("\n" + "═" * 74)
    print("THE MESSAGE: adapting is not rebuilding everything. You identify the")
    print("storeys the new need puts at fault — multimodal parsing, security — you")
    print("make those evolve in a targeted way, and you VERIFY that the regressions")
    print("are gone without degrading the rest. An architecture is a living thing.")


if __name__ == "__main__":
    main()
