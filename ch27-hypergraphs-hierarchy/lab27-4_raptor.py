# -*- coding: utf-8 -*-
"""
Lab 27-4 — RAPTOR: "exploring a corpus without reading all of it"

The aim: implement the principle of RAPTOR (recursive summaries organised into a
tree) and show that it shrinks the search space: you look at the summary first,
and descend only where it is useful.

A real case: a corpus of inspection reports. A RAPTOR tree is built (fragments ->
group summaries -> a global summary), then a global question is answered ("the
main problems across the fleet?") and a local one ("the vibration check?"),
counting the nodes consulted each time.

The lab prints the nodes explored by RAPTOR against a flat RAG, which reads every
fragment, and the resulting saving.

No API key. Run generate_corpus.py first.
"""

import numpy as np

from multikit import (Embedder, summarize, load_inspections, bandeau)


def build_raptor_tree(rapports, taille_groupe=6):
    """Level 0 = fragments ; level 1 = summaries of groupes ; level 2 = summary
 global. Returns (feuilles, resumes_n1, resume_global)."""
    feuilles = [{"id": r["id"], "content": r["content"]} for r in rapports]
    resumes_n1 = []
    for i in range(0, len(feuilles), taille_groupe):
        groupe = feuilles[i:i + taille_groupe]
        txt = " ".join(f["content"] for f in groupe)
        resumes_n1.append({"id": f"group_{i // taille_groupe}",
                           "content": summarize(txt, n=2),
                           "feuilles": [f["id"] for f in groupe]})
    resume_global = summarize(" ".join(r["content"] for r in resumes_n1), n=3)
    return feuilles, resumes_n1, resume_global


def descendre_raptor(question, feuilles, resumes_n1, emb_n1, emb_feuilles):
    """RAPTOR: find the best level-1 summary, then read only its
 feuilles. Returns (level_atteint, nodes_explores, meilleure_feuille)."""
    q = emb_n1.encode([question])[0]
    scores_n1 = emb_n1.matrice @ q
    meilleur = int(np.argmax(scores_n1))
    nodes = len(resumes_n1)  # on a "lu" the summaries of level 1
    # descendre toward the feuilles of this groupe seulement
    ids_feuilles = resumes_n1[meilleur]["feuilles"]
    idx = [i for i, f in enumerate(feuilles) if f["id"] in ids_feuilles]
    sousmat = emb_feuilles.matrice[idx]
    qf = emb_feuilles.encode([question])[0]
    sf = sousmat @ qf
    best_local = idx[int(np.argmax(sf))]
    nodes += len(idx)
    return resumes_n1[meilleur]["id"], nodes, feuilles[best_local]


def main():
    bandeau("Lab 27-4 — RAPTOR: summarise before searching")
    rapports = load_inspections()
    feuilles, resumes_n1, resume_global = build_raptor_tree(rapports)
    print(f"\nArbre RAPTOR : {len(feuilles)} feuilles → {len(resumes_n1)} "
          f"group summaries -> 1 global summary.")
    print(f"Global summary: {resume_global[:100]}…")

    emb_feuilles = Embedder([f["content"] for f in feuilles])
    emb_n1 = Embedder([r["content"] for r in resumes_n1])

    # === Question GLOBALE ================================================
    qg = "What are the main problems across the industrial fleet?"
    print("\n" + "─" * 74)
    print("A GLOBAL QUESTION :", qg)
    print("   RAPTOR: answers at the GLOBAL SUMMARY level (1 node read).")
    print(f"     → {resume_global[:110]}…")
    print(f"   flat RAG: would have to read and aggregate the {len(feuilles)} fragments.")
    print(f"   saving: 1 node against {len(feuilles)} -> a reduction of "
          f"{(1 - 1/len(feuilles)):.0%} de l'espace lu.")

    # === Question LOCALE =================================================
    ql = "What does the inspection say about the vibration check on the bearing?"
    print("\n" + "─" * 74)
    print("A LOCAL QUESTION :", ql)
    niveau, noeuds_raptor, feuille = descendre_raptor(
        ql, feuilles, resumes_n1, emb_n1, emb_feuilles)
    print(f"   RAPTOR: descends via \"{niveau}\" then reads its leaves "
          f"({noeuds_raptor} nodes explored).")
    print(f"     → [{feuille['id']}] {feuille['content']}")
    print(f"   flat RAG: reads the {len(feuilles)} fragments to find the right one.")
    gain = 1 - noeuds_raptor / len(feuilles)
    print(f"   saving: {noeuds_raptor} vs {len(feuilles)} nodes -> "
          f"{gain:+.0%} of the space read.")

    print("\n" + "─" * 74)
    print("THE MESSAGE: RAPTOR does not summarise for the sake of summarising.")
    print("             It summarises in order to SHRINK the search space.")


if __name__ == "__main__":
    main()
