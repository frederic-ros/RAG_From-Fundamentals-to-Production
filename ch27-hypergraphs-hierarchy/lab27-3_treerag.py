# -*- coding: utf-8 -*-
"""
Lab 27-3 — TreeRAG: "searching at the right storey of the hierarchy"

The aim: understand why a hierarchy improves retrieval. The corpus is indexed at
three levels (fragment, section summary, global summary), and the question is
shown to determine the LEVEL at which the answer lives — a detail at the fragment
level, a synthesis at the root.

"Maximum temperature of blade 7?" lives at the component level; "describe the
operation of the turbine" lives at the root.

For questions of varied scope, the lab prints the level chosen by a simple
router, the content returned, and the comparison with a single-level RAG.

No API key. Run generate_corpus.py first.
"""

from multikit import (DocTree, HierarchicalIndex, Search,
                      load_turbine_md, bandeau)


# A minimal scope router: detail words -> fragment, synthesis words ->
# global, sinon section.
def level_of(question: str) -> str:
    bas = question.lower()
    if any(m in bas for m in ["temperature", "value", "maximum", "permissible",
                              "how many", "what is", "circuit", "deg"]):
        return "fragment"
    if any(m in bas for m in ["describe", "operation", "general", "overview",
                              "general", "ensemble", "architecture", "global",
                              "overall summary", "main parts"]):
        return "global"
    return "section"


def main():
    bandeau("Lab 27-3 — TreeRAG: finding the right level")
    md = load_turbine_md()
    arbre = DocTree(md)
    idx = HierarchicalIndex.depuis_arbre(arbre)
    print(f"\nArbre : {len(idx.fragments)} fragments, {len(idx.sections)} "
          f"section summaries, 1 global summary.")

    # RAG to level unique (reference) : seulement the fragments bruts.
    rag_plat = Search(idx.fragments)

    questions = [
        "What is the maximum permissible temperature of blade 7?",   # a detail
        "What are the components of stage 3?",                       # a section
        "Describe the general operation of the turbine.",            # global
    ]

    for q in questions:
        niv = level_of(q)
        print("\n" + "─" * 74)
        print(f"QUESTION : {q}")
        print(f"   -> level chosen by the router: {niv}")

        # TreeRAG : search at the bon level
        res = idx.search(q, niv)
        print(f"   TreeRAG  [{res.get('id','?')}] : {res['content'][:90]}…")

        # RAG plat : always at the level fragment
        plat = rag_plat.cherche(q, k=1)[0]
        print(f"   RAG plat [{plat['id']}] : {plat['content'][:90]}…")

        # commentaire
        if niv == "global":
            print("   -> The synthesis question has NO answer in an isolated fragment:")
            print("      a flat RAG can only return a detail; TreeRAG gives the overview.")
        elif niv == "fragment":
            print("   -> A detail question: both find it, but a flat RAG is enough here.")
        else:
            print("   -> A section question: the section summary condenses what a flat RAG")
            print("      would have to rebuild by concatenating several fragments.")

    print("\n" + "─" * 74)
    print("THE MESSAGE: the problem is not only WHAT to search for,")
    print("             it is also AT WHAT LEVEL to search.")


if __name__ == "__main__":
    main()
