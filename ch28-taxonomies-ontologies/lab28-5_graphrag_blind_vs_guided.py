# -*- coding: utf-8 -*-
"""
Lab 28-5 — Blind GraphRAG against guided GraphRAG
"Extracting without a schema is extracting noise"

The aim: measure, on the same corpus, the gap in quality between a "blind"
GraphRAG (free extraction, no ontology) and a "guided" one (extraction
constrained by the ontology). The proportion of out-of-domain triples is
estimated, and the precision of the resulting graph evaluated.

The blind graph is larger but holds out-of-schema relations; the guided graph is
smaller and 100% consistent with the ontology. Precision goes from "middling" to
"total" — at the price of a little recall.

No API key. Run generate_corpus.py first.
"""

from businesskit import (Ontology, extract_triples, load_fragments, bandeau)


def main():
    bandeau("Lab 28-5 — Blind GraphRAG against guided GraphRAG")
    onto = Ontology.load()
    frags = load_fragments()

    # A few realistic trap sentences are injected into the stream: plausible
    # relations that fall outside the domain, as a real noisy corpus would hold.
    # The FIRST is the trap proper; the other two are legitimate. All three must
    # match the templates of businesskit._TEMPLATES, or this lab compares two
    # empty graphs and shows nothing.
    pieges = [
        "The primary circuit feeds the technician on duty during the round.",
        "Pump P-42 is fed by the primary cooling circuit.",
        "Technician Julien is responsible for the intervention procedure.",
    ]
    textes = [f["text"] for f in frags] + pieges

    # === BLIND GraphRAG (no ontology) =====================================
    aveugle = []
    for t in textes:
        aveugle.extend(extract_triples(t, ontologie=None))

    # === GUIDED GraphRAG (constrained by the ontology) ====================
    guide = []
    for t in textes:
        guide.extend([x for x in extract_triples(t, ontologie=onto)
                      if not x.get("rejete")])

    # === Precision: share of valid triples from blind extraction ========
    valides = [t for t in aveugle
               if onto.relation_permise(t.get("classe_sujet", "?"),
                                        t["relation"],
                                        t.get("classe_objet", "?"))]
    hors = [t for t in aveugle if t not in valides]
    prec_aveugle = len(valides) / len(aveugle) if aveugle else 0.0

    print(f"\n{'':<22}{'BLIND':>12}{'GUIDED':>12}")
    print("─" * 46)
    print(f"{'triplets':<22}{len(aveugle):>12}{len(guide):>12}")
    print(f"{'triplets valides':<22}{len(valides):>12}{len(guide):>12}")
    print(f"{'precision':<22}{prec_aveugle:>11.0%}{1.0:>12.0%}")

    print("\nOut-of-domain triples let through by the BLIND GraphRAG:")
    if hors:
        for t in hors:
            print(f"   ❌ {t['sujet']} --{t['relation']}--> {t['objet']} "
                  f"({t.get('classe_sujet')}→{t.get('classe_objet')})")
    else:
        print("   (none on this corpus — raise the noise to see some)")

    print("\n" + "─" * 60)
    print("THE MESSAGE: blind GraphRAG maximises recall but accumulates")
    print("false or off-topic relations — a graph you cannot")
    print("query with confidence. Guided GraphRAG sacrifices a little recall for")
    print("total precision: every edge is guaranteed to conform to the business")
    print("model. In production it is precision that makes the graph")
    print("usable for reasoning.")


if __name__ == "__main__":
    main()
