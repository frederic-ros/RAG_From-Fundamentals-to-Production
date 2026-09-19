# -*- coding: utf-8 -*-
"""
Lab 30-4 — The conversational router: not every turn deserves a retrieval
"Running a search on 'Thanks!' costs tokens and injects noise"

The aim: classify each turn as chitchat, followup or search, and trigger the
expensive RAG pipeline only for the last. A good router saves tokens AND
improves quality, because it stops irrelevant fragments entering the context.

THE ROUTER WORD SETS ARE THE MECHANISM. They are matched against the text of the
turns, so they must be in the language of the conversation. This lab prints the
classification turn by turn: all ten should match their annotated type.

One trap worth knowing: the chitchat set is matched on WHOLE WORDS, not
substrings. "hi" is a substring of "this", and a substring test misclassified a
technical question as chitchat.

No API key. Run generate_corpus.py first.
"""

from chatkit import router_tour, load_conversation, bandeau


# Indicative costs in tokens, by category of turn.
COUT = {"chitchat": 10, "followup": 20, "search": 200}
COUT_TOUJOURS = 200  # the naive policy: run the full RAG on every turn


def main():
    bandeau("Lab 30-4 — Routeur conversationnel")
    conv = load_conversation()

    historique = []
    classes = []
    print(f"\n{'category':<12}{'cost':>6}  question")
    print("─" * 60)
    for msg in conv:
        if msg["role"] == "assistant":
            historique.append(msg)
            continue
        cat = router_tour(msg["texte"], historique)
        classes.append(cat)
        print(f"{cat:<12}{COUT[cat]:>6}  {msg['texte'][:40]}")
        historique.append(msg)

    # The summary by category
    n = len(classes)
    print("─" * 60)
    print(f"\n{'category':<14}{'turns':>7}{'share':>8}{'mean cost':>12}")
    print("─" * 44)
    from collections import Counter
    compte = Counter(classes)
    cout_routeur = 0
    for cat in ("chitchat", "followup", "search"):
        c = compte.get(cat, 0)
        cout_routeur += c * COUT[cat]
        print(f"{cat:<14}{c:>7}{c / n:>8.0%}{COUT[cat]:>12}")
    print("─" * 44)

    cout_moyen_routeur = cout_routeur / n
    cout_naif = COUT_TOUJOURS  # by tour
    economie = 1 - cout_moyen_routeur / cout_naif
    print(f"\nMean cost with the router : {cout_moyen_routeur:.0f} tokens/turn")
    print(f"Cost of \"always search\"   : {cout_naif} tokens/turn")
    print(f"SAVING (on this dialogue) : {economie:.0%}")

    # === projected onto a typical production split =======================
    # In production the turns often split like this, as observed:
    repartition = {"chitchat": 0.20, "followup": 0.30, "search": 0.50}
    cout_proj = sum(repartition[c] * COUT[c] for c in repartition)
    eco_proj = 1 - cout_proj / cout_naif
    print("\nProjection over 100 turns (20% chitchat, 30% follow-up, 50% search):")
    print(f"   projected mean cost: {cout_proj:.0f} tokens/turn")
    print(f"   PROJECTED SAVING   : {eco_proj:.0%}")
    print("   (this demonstration dialogue is dense in searches; in")
    print("    production, the share of chitchat and follow-up makes the gain sharper)")

    # The emblematic examples
    print("\n" + "─" * 60)
    print("EXAMPLES:")
    print("   \"Thanks!\"                          -> chitchat (no retrieval)")
    print("   \"Can you rephrase the last step?\"  -> followup (history only)")
    print("   \"What is the procedure?\"           -> search (the RAG pipeline)")

    print("\n" + "═" * 60)
    print("THE MESSAGE: a good router saves tokens AND improves quality.")
    print("Running a retrieval on \"Thanks!\" costs tokens and injects noise into")
    print("the context. Routing means spending the search effort where it really")
    print("serves — and keeping the other turns fast and clean.")


if __name__ == "__main__":
    main()
