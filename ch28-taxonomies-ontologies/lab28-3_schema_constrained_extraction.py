# -*- coding: utf-8 -*-
"""
Lab 28-3 — Schema-constrained extraction (ontology-driven)
"Giving the extractor a schema is forbidding it to invent"

The aim: only triples whose type (subject class, relation, object class) is
permitted by the ontology are kept.

The text holds a trap — "a circuit feeds a technician" — which free extraction
picks up and constrained extraction rejects.

With Ollama the extraction becomes a real LLM call guided by the schema; offline
it runs on deterministic templates. The lesson is the same either way.

No API key. Run generate_corpus.py first.
"""

from businesskit import Ontology, extract_triples, load_fragments, bandeau


# A few rapports + a sentence trap (relation plausible, but interdite)
# The FIRST sentence is the trap: "a circuit feeds a technician" is perfectly
# plausible English, and the free extractor picks it up — but the ontology does
# not declare that relation, so the constrained extractor must reject it. The
# other sentences are legitimate and must survive. If the wording drifts away
# from the templates of businesskit._TEMPLATES, this lab silently reports zero
# triples and zero rejections, and the comparison shows nothing.
TRAP = ("The primary circuit feeds the technician on duty. "
        "Pump P-42 is fed by the primary circuit. "
        "Pump P-42 carries the risk of cavitation. "
        "The lock-off procedure concerns pump P-42. "
        "Technician Julien is responsible for the intervention procedure.")


def show(triplets, titre):
    print(f"\n{titre} — {len(triplets)} triple(s):")
    if not triplets:
        print("   (none)")
    for t in triplets:
        marque = ""
        if t.get("rejete"):
            marque = "  REJECTED (outside the schema)"
        print(f"   {t['sujet']:<22} --{t['relation']:<18}--> {t['objet']:<22}"
              f"  [{t.get('classe_sujet','?')} → {t.get('classe_objet','?')}]{marque}")


def main():
    bandeau("Lab 28-3 — Schema-constrained extraction (ontology-driven)")
    onto = Ontology.load()

    # Combine the trap sentence with two real reports.
    frags = load_fragments()
    textes = [TRAP,
              next(f["text"] for f in frags if f["id"] == "R20"),  # procedure / technician
              next(f["text"] for f in frags if f["id"] == "R23")]  # pump / circuit
    texte = " ".join(textes)

    print("\nTHE TEXT ANALYSED (an extract):")
    print("  " + texte[:160] + "…")

    # === FREE extraction (no ontology passed) ===========================
    libre = extract_triples(texte, ontologie=None)
    show(libre, "FREE EXTRACTION (no guardrail)")

    # === CONSTRAINED extraction (filtered by the schema) ================
    # First identify what the schema allows, then filter accordingly.
    contraint = extract_triples(texte, ontologie=onto)
    show(contraint, "CONSTRAINED EXTRACTION (filtered by the ontology)")

    # === bilan comparatif ===============================================
    rejetes = [t for t in libre
               if not onto.relation_permise(t.get("classe_sujet", "?"),
                                            t["relation"],
                                            t.get("classe_objet", "?"))]
    print("\n" + "─" * 74)
    print(f"Triples extracted freely      : {len(libre)}")
    print(f"Triples kept (constrained)    : "
          f"{len([t for t in contraint if not t.get('rejete')])}")
    print(f"Triples rejected by the schema: {len(rejetes)}")
    for t in rejetes:
        print(f"   ❌ {t['sujet']} --{t['relation']}--> {t['objet']} "
              f"(type {t.get('classe_sujet')}->{t.get('classe_objet')} not permitted)")

    print("\n" + "─" * 74)
    print("THE MESSAGE: the ontology does not enrich the extraction, it DISCIPLINES it.")
    print("The schema acts as a contract: any triple whose type is not declared")
    print("is discarded. A little recall is traded for a great deal of precision")
    print("— a smaller graph, but one you can"),
    print("confidence for reasoning.")


if __name__ == "__main__":
    main()
