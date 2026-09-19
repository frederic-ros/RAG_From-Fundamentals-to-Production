# -*- coding: utf-8 -*-
"""
Lab 28-2 — Building and validating a business ontology
"A taxonomy classifies; an ontology permits and forbids"

The aim: understand concretely what separates a taxonomy (an is-a tree) from an
ontology (a meta-model: classes, permitted relations, axioms). The ontology is
validated (isolated classes, relations towards unknown classes, cycles), a fault
is deliberately injected, and the detection is checked.

The starting ontology is sound; the faulty version is rejected with a diagnosis;
a relation outside the schema is correctly refused.

No API key. Run generate_corpus.py first.
"""

from businesskit import Ontology, bandeau


def main():
    bandeau("Lab 28-2 — Building and validating a business ontology")
    onto = Ontology.load()

    print("\nCLASSES :", ", ".join(onto.classes))
    print("\nPERMITTED RELATIONS (the schema):")
    for r in onto.relations:
        print(f"   {r['source']:<18} --{r['label']:<24}--> {r['target']}")
    print("\nAXIOMS (the logical rules of the domain):")
    for a in onto.axiomes:
        print(f"   - {a}")

    # === 1) validate the starting ontology ================================
    print("\n" + "─" * 74)
    pbs = onto.validate()
    if not pbs:
        print("VALIDATION: the ontology is sound (no isolated class, no cycle,")
        print("            every relation references a declared class).")
    else:
        print("VALIDATION: problems detected")
        for p in pbs:
            print("   -", p)

    # === 2) break the ontology, to see the validator react ================
    print("\n" + "─" * 74)
    print("INJECTING A FAULT: a relation towards an unknown class is added,")
    print("along with an orphan class, then the validation is run again.")
    fautive = Ontology(
        classes=onto.classes + ["ClasseOrpheline"],
        relations=onto.relations + [
            {"source": "Pump", "target": "Martian", "label": "piloted_by"}
        ],
        axiomes=onto.axiomes,
    )
    for p in fautive.validate():
        print("   ❌", p)

    # === 3) a cycle interdit ===========================================
    print("\n" + "─" * 74)
    print("INJECTING A CYCLE: Component -> Pump -> Component.")
    cyclique = Ontology(
        classes=onto.classes,
        relations=onto.relations + [
            {"source": "Component", "target": "Pump", "label": "mounted_on"}
        ],
        axiomes=onto.axiomes,
    )
    pbs = cyclique.validate()
    print("   ->", "cycle detected" if any("cycle" in p.lower() for p in pbs)
          else "cycle NOT detected")

    # === 4) The schema can reject invalid relations =====================================
    print("\n" + "─" * 74)
    print("PERMISSION TEST — the central role of the ontology: permit or forbid")
    cas = [
        ("Pump", "fed_by", "HydraulicCircuit"),   # permitted
        ("Pump", "carries_risk_of", "FailureMode"), # permise
        ("HydraulicCircuit", "alimente", "Technician"),   # interdite (n'existe pas)
        ("Technician", "carries_risk_of", "FailureMode"),  # interdite
    ]
    for s, l, t in cas:
        ok = onto.relation_permise(s, l, t)
        verdict = "PERMISE   ✅" if ok else "INTERDITE ❌"
        print(f"   {s:<18} --{l:<20}--> {t:<22} {verdict}")

    print("\n" + "─" * 74)
    print("THE MESSAGE: a taxonomy can only CLASSIFY (is-a). An ontology")
    print("defines what CAN exist — and so what cannot. That is")
    print("exactly the guardrail that will turn, in the next lab, a noisy extraction")
    print("noisy extraction into a semantically coherent graph.")


if __name__ == "__main__":
    main()
