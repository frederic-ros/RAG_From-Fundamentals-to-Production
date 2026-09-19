# -*- coding: utf-8 -*-
"""
Lab 30-3 — Memory strategies: window, summary, state, hybrid
"Remembering everything is expensive; remembering nothing is useless"

The aim: compare four ways of carrying a conversation forward, on the same long
thread of 45 turns:

    the raw history  — complete but its cost grows without bound;
    a sliding window — compact but forgetful;
    a rolling summary— condenses the old, keeps the recent fresh;
    a semantic state — a few key variables, constant cost;
    the hybrid       — state plus a small recent window.

Each is measured on cost (in tokens) and on its ability to answer a question
asked at turn 45 about something said at turn 3.

No API key. Run generate_corpus.py first.
"""

from chatkit import (RawMemory, WindowMemory, SummaryMemory, StateMemory,
                     HybridMemory, load_long_conversation, normaliser,
                     bandeau)


# Late robustness questions: the information was laid down early in the thread.
SONDES = [
    ("son fournisseur", "sulzer"),
    ("date d'intervention", "2026-06-25"),
    ("le technicien", "karim"),
    ("la cause", "joint"),
]


def info_accessible(contexte: str, attendu: str) -> bool:
    return attendu.lower() in normaliser(contexte) or attendu.lower() in contexte.lower()


def main():
    bandeau("Lab 30-3 — Conversational memory strategies")
    conv = load_long_conversation()
    tours_user = sum(1 for m in conv if m["role"] == "user")

    strategies = [RawMemory(), WindowMemory(5), SummaryMemory(3),
                  StateMemory(), HybridMemory(2)]

    # Replay the conversation and record the cumulative cost
    couts = {s.nom: [] for s in strategies}
    for msg in conv:
        for s in strategies:
            s.add(msg["role"], msg["texte"])
            couts[s.nom].append(s.cout())

    print(f"\nConversation de {tours_user} tours utilisateur.\n")
    print(f"{'strategy':<26}{'cost/turn':>11}{'final cost':>12}"
          f"{'robustesse':>12}")
    print("─" * 64)

    for s in strategies:
        cout_moyen = sum(couts[s.nom]) / len(couts[s.nom])
        cout_final = couts[s.nom][-1]
        # robustesse : combien of sondes tardives restent accessibles ?
        ctx = s.contexte()
        ok = sum(1 for _, att in SONDES if info_accessible(ctx, att))
        robust = f"{ok}/{len(SONDES)}"
        print(f"{s.nom:<26}{cout_moyen:>10.0f}{cout_final:>12.0f}{robust:>12}")

    print("─" * 64)

    # zoom on the robustesse
    print("\nACCESS TO OLD INFORMATION (laid down at the start of the thread):")
    for s in strategies:
        ctx = s.contexte()
        details = []
        for label, att in SONDES:
            details.append(f"{label}={'yes' if info_accessible(ctx, att) else 'no'}")
        print(f"   {s.nom:<26} {'  '.join(details)}")

    # state semantic final (lisible)
    etat = next(s for s in strategies if isinstance(s, StateMemory))
    print("\nThe final semantic state (a compact dictionary):")
    for k, v in etat.etat.items():
        print(f"   {k:<14}: {v}")

    print("\n" + "═" * 64)
    print("KEY MESSAGE: raw history is expensive and eventually dilutes the useful information;")
    print("the sliding window is compact but forgets whatever leaves the window;")
    print("the semantic state is BOTH compact and robust — it holds the key")
    print("variables whatever the number of turns. In a structured domain such as")
    print("maintenance it is the winning strategy; the hybrid adds the freshness")
    print("of the last few exchanges.")


if __name__ == "__main__":
    main()
