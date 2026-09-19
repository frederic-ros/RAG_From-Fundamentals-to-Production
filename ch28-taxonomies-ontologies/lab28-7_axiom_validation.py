# -*- coding: utf-8 -*-
"""
Lab 28-7 — Validating the axioms
"The schema says what CAN exist; the axiom says what MUST exist"

The aim: go beyond the constraint of TYPE (Lab 28-3) and check ABSOLUTE business
rules — the axioms of the ontology. A relation can be of the right type and still
violate a rule of completeness or of order:

    A1. Every failure mode must be attached to at least one pump.
    A2. A safety procedure must precede any intervention procedure.
    A3. Every pump must be fed by exactly one circuit.

The axiom checker reports precisely which rule was violated and on which
instance.

No API key. Run generate_corpus.py first.
"""

from businesskit import (Ontology, BusinessGraph, check_axioms,
                       build_ras, load_fragments, bandeau)


def conforming_graph(onto):
    g = BusinessGraph(onto)
    g.add_instance("P-42", "Pump")
    g.add_instance("primary circuit", "HydraulicCircuit")
    g.add_instance("cavitation", "FailureMode")
    g.add_edge("P-42", "fed_by", "primary circuit")
    g.add_edge("P-42", "carries_risk_of", "cavitation")
    return g


def faulty_graph(onto):
    g = BusinessGraph(onto)
    # A pump with NO circuit violates A3; an orphan failure mode violates A1.
    g.add_instance("P-99", "Pump")
    g.add_instance("unbalance", "FailureMode")  # attached to no pump
    g.add_instance("circuit A", "HydraulicCircuit")
    g.add_instance("circuit B", "HydraulicCircuit")
    g.add_instance("P-77", "Pump")
    # P-77 fed by TWO circuits violates A3, which demands exactly one.
    g.add_edge("P-77", "fed_by", "circuit A")
    g.add_edge("P-77", "fed_by", "circuit B")
    return g


def rapport(nom, g):
    print(f"\n{nom}: {len(g.nodes)} instances, {len(g)} edges.")
    violations = check_axioms(g)
    if not violations:
        print("   every absolute business rule is satisfied.")
    else:
        for v in violations:
            print(f"   ❌ [{v['axiome']}] {v['message']}")
    return violations


def main():
    bandeau("Lab 28-7 — Validating the absolute business rules (axioms)")
    onto = Ontology.load()

    print("\nAXIOMS CHECKED:")
    for a in onto.axiomes:
        print(f"   - {a}")

    print("\n" + "─" * 74)
    rapport("CONFORMING GRAPH", conforming_graph(onto))

    print("\n" + "─" * 74)
    rapport("FAULTY GRAPH", faulty_graph(onto))

    # === on a true mini-graph RAS ====================================
    print("\n" + "─" * 74)
    print("A CHECK ON A REAL RAS MINI-GRAPH")
    frags = load_fragments()
    g = build_ras(frags, "pompe P-42 circuit cavitation", ontologie=onto, k=4)
    g.nodes.setdefault("pompe p 42", "Pump")
    rapport("RAS graph (question P-42)", g)

    print("\n" + "─" * 74)
    print("THE MESSAGE: the constraint of TYPE (Lab 28-3) prevents absurd relations;")
    print("the AXIOMS go further and impose COMPLETENESS and ORDER — \"every fault")
    print("must have a cause\", \"safety precedes intervention\". Those absolute rules")
    print("turn a correct graph into a graph WORTHY OF TRUST for decision making —")
    print("the last lock before letting an agent act on this data.")


if __name__ == "__main__":
    main()
