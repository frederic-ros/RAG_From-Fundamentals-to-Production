# -*- coding: utf-8 -*-
"""
Lab 30-1 — Anaphora and ellipsis: the challenge of the multi-turn
"A human conversation is not a good search query"

The aim: show that anaphora ("on it", "it") and ellipsis ("And for the
trainees?") break vector retrieval, and quantify the failure — then the gain
when the query is reformulated into a self-contained version.

"Have we seen any trouble on it this month?" is limpid to a human and opaque to
an index: the word "it" carries no meaning of its own.

The lab compares the context recall by type of dependency: the already
self-contained turns pass, the anaphoric and elliptical ones collapse.

No API key. Run generate_corpus.py first.
"""

from chatkit import (Search, context_recall, load_fragments,
                     load_conversation, bandeau)


def main():
    bandeau("Lab 30-1 — Anaphora and ellipsis: the challenge of the multi-turn")
    docs = load_fragments()
    conv = load_conversation()
    rech = Search(docs)
    K = 3

    print(f"\n{'type':<10}{'recall brut':>12}{'recall autonome':>17}  question")
    print("─" * 78)

    par_type = {}
    for msg in conv:
        if msg["role"] != "user" or not msg["attendus"]:
            continue
        brut = [f["id"] for f in rech.chercher(msg["texte"], k=K)]
        auto = [f["id"] for f in rech.chercher(msg["autonome"], k=K)]
        r_brut = context_recall(brut, msg["attendus"])
        r_auto = context_recall(auto, msg["attendus"])
        par_type.setdefault(msg["type"], []).append((r_brut, r_auto))
        print(f"{msg['type']:<10}{r_brut:>11.0%}{r_auto:>16.0%}  "
              f"{msg['texte'][:38]}")

    print("─" * 78)
    print("\nMean by type of dependency:")
    moy = lambda xs: sum(xs) / len(xs) if xs else 0.0
    for typ, vals in par_type.items():
        rb = moy([v[0] for v in vals])
        ra = moy([v[1] for v in vals])
        print(f"   {typ:<10} : brut {rb:>4.0%}  →  autonome {ra:>4.0%}")

    # A focus on the emblematic example
    print("\n" + "─" * 78)
    exemple = next(m for m in conv if m["role"] == "user"
                   and "on it" in m["texte"])
    print(f"EXAMPLE: \"{exemple['texte']}\"")
    print(f"   raw     -> {[f['id'] for f in rech.chercher(exemple['texte'], 3)]} "
          f"(recall {context_recall([f['id'] for f in rech.chercher(exemple['texte'],3)], exemple['attendus']):.0%})")
    print(f"   self-contained (\"{exemple['autonome']}\")")
    print(f"           → {[f['id'] for f in rech.chercher(exemple['autonome'], 3)]} "
          f"(recall {context_recall([f['id'] for f in rech.chercher(exemple['autonome'],3)], exemple['attendus']):.0%})")

    print("\n" + "═" * 78)
    print("THE MESSAGE: vector retrieval DOES NOT UNDERSTAND the conversational")
    print("context. The already self-contained questions pass; the anaphora and")
    print("the ellipsis collapse — not through weakness of the embedding model,")
    print("but because the query sent has lost its anchor. The answer")
    print("is not a better embedding: it is a reformulation (Lab 30-2).")


if __name__ == "__main__":
    main()
