# -*- coding: utf-8 -*-
"""
Lab 30-2 — The standalone reformulator
"Reformulation is not padding with words, it is a reconstruction of intent"

The aim: implement a context-aware query transformer that takes the recent
history plus the new question and produces a self-contained query.

For the dependent turns, the raw query ("Who supplies it?") becomes
self-contained ("Who is the supplier of valve V-7?") and brings back the right
fragment.

THIS IS THE VERIFICATION LAB for the reformulation mechanisms of chatkit. It
prints the mean gain in context recall; the French baseline is +25%. A gain of
zero means one of the word lists has stopped matching — the pronouns, the
equipment pattern or the themes.

No API key. Run generate_corpus.py first.
"""

from chatkit import (Search, reformuler, context_recall,
                     load_fragments, load_conversation, bandeau)


def main():
    bandeau("Lab 30-2 — Reformulateur autonome contextuel")
    docs = load_fragments()
    conv = load_conversation()
    rech = Search(docs)
    K = 3

    historique = []
    gains = []
    print()
    for msg in conv:
        if msg["role"] == "assistant":
            historique.append(msg)
            continue
        # tour utilisateur
        question = msg["texte"]
        reformulee = reformuler(question, historique)

        if msg["attendus"]:
            sans = [f["id"] for f in rech.chercher(question, k=K)]
            avec = [f["id"] for f in rech.chercher(reformulee, k=K)]
            r_sans = context_recall(sans, msg["attendus"])
            r_avec = context_recall(avec, msg["attendus"])
            gains.append(r_avec - r_sans)

            print(f"TURN \"{question}\"")
            print(f"   reformulated: \"{reformulee}\"")
            print(f"   without: {sans}  (recall {r_sans:.0%})")
            print(f"   with   : {avec}  (recall {r_avec:.0%})")
            if r_avec > r_sans:
                print(f"   -> gain +{(r_avec - r_sans):.0%}")
            print()
        historique.append(msg)

    moy = sum(gains) / len(gains) if gains else 0.0
    print("═" * 74)
    print(f"MEAN GAIN in context recall from the reformulation: {moy:+.0%}")
    print("\nTHE MESSAGE: reformulation reconstructs the INTENT from the history")
    print("and the question. \"Who supplies it?\" alone is unusable; anchored on")
    print("\"valve V-7\" from the previous turn, it becomes a query the index")
    print("understands. In conversation, reformulation IS the retrieval: it is the")
    print("most decisive block, not the embedding model.")
    print("\nA NUANCE: on already self-contained questions, reformulation must")
    print("breaking anything. A good transformer also knows when NOT to act.")


if __name__ == "__main__":
    main()
