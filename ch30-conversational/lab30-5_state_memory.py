# -*- coding: utf-8 -*-
"""
Lab 30-5 — Semantic state memory
"A question asked at turn 45 finds its answer in the state, without rereading
the 44 turns before it"

The aim: maintain a small structured state — equipment, problem, supplier,
technician, contract, date — extracted as the conversation runs, and show that
it answers late anaphoric turns at a constant cost.

THE STATE EXTRACTORS ARE THE MECHANISM. They are regexes over the wording of the
conversation, and a pattern that stops matching leaves its variable empty: the
late turns then resolve to "(absent)" with no error raised. This lab prints the
resolution of all five late turns, which is the check to run.

No API key. Run generate_corpus.py first.
"""

from chatkit import (StateMemory, RawMemory,
                     load_long_conversation, bandeau)


# Mapping from a state key to the wording of the corresponding late turn.
# These must match the late turns built by generate_corpus.build_long_conversation().
ROBUSTESSE = {
    "fournisseur": "Late turn: \"And its supplier, who was that again?\"",
    "date": "Late turn: \"What was the intervention date?\"",
    "technicien": "Late turn: \"Who was taking the intervention, again?\"",
    "contrat": "Late turn: \"And the contract, its number?\"",
    "equipement": "Late turn: \"Which equipment were we talking about?\"",
}


def main():
    bandeau("Lab 30-5 — A long conversation with semantic state memory")
    conv = load_long_conversation()

    # === construction of the state + suivi of the cost ==========================
    etat_mem = StateMemory()
    brut_mem = RawMemory()
    cout_etat, cout_brut = [], []
    for msg in conv:
        etat_mem.add(msg["role"], msg["texte"])
        brut_mem.add(msg["role"], msg["texte"])
        cout_etat.append(etat_mem.cout())
        cout_brut.append(brut_mem.cout())

    tours = sum(1 for m in conv if m["role"] == "user")
    total_etat = sum(cout_etat)
    total_brut = sum(cout_brut)

    print(f"\nConversation de {tours} tours utilisateur.\n")
    print("The final semantic state:")
    for k, v in etat_mem.etat.items():
        print(f"   {k:<14}: {v}")

    print("\n" + "─" * 60)
    print(f"{'strategy':<22}{'cumulative cost':>17}{'final cost/turn':>17}")
    print("─" * 60)
    print(f"{'historique brut':<22}{total_brut:>13}{cout_brut[-1]:>17}")
    print(f"{'semantic state':<22}{total_etat:>17}{cout_etat[-1]:>17}")
    gain = 1 - total_etat / total_brut if total_brut else 0
    print("─" * 60)
    print(f"COST SAVING (state against raw): {gain:.0%}")

    # === robustness: late anaphora resolved through the state ============
    print("\n" + "─" * 60)
    print("ROBUSTNESS — late anaphora resolved from the state:")
    for msg in conv:
        cible = msg.get("cible_etat")
        if cible:
            valeur = etat_mem.etat.get(cible, "(absent)")
            print(f"   {ROBUSTESSE.get(cible, cible)}")
            print(f"      -> resolved from the state: {cible} = \"{valeur}\"")

    print("\n" + "═" * 60)
    print("THE MESSAGE: the raw history grows at every turn and becomes expensive;")
    print("the semantic state stays constant — a few key variables. In a domain as")
    print("structured as maintenance it is the optimal strategy: compact,")
    print("deterministic and robust. A question asked at turn 45 finds its answer")
    print("in the state, without rereading the 44 turns before it.")
    print("\nTHE LIMIT: the state captures only what you thought to model. In an")
    print("open domain, the rolling summary or the hybrid take the advantage back.")


if __name__ == "__main__":
    main()
