# -*- coding: utf-8 -*-
"""
Lab 28-6 — Integrating the semantic layer into a multi-resolution architecture
"The taxonomy at the input, the ontology as a guardrail, the graph at the output"

The aim: assemble the pieces of the earlier labs into a complete pipeline, where
the user's question passes through the semantic layer at every storey:

    query -> (1) taxonomic expansion -> (2) constrained retrieval
          -> (3) an answer supported by fragments plus relations

The three registers — taxonomy, ontology, business graph — do not compete; they
nest around a single flow.

For a query in local business vocabulary ("cavitation"), the pipeline shows the
canonical concept resolved, the fragments retrieved, and the schema-compliant
mini-graph.

No API key. Run generate_corpus.py first.
"""

from businesskit import (Taxonomy, Ontology, Search, mapper_concept,
                       build_ras, load_fragments, bandeau)


def pipeline(requete, taxo, onto, frags, rech, k=4):
    etapes = {}

    # (1) expansion taxonomique of the query
    concept = mapper_concept(requete, taxo)
    termes = taxo.expansion(concept) if concept else []
    requete_enrichie = requete + " " + " ".join(termes)
    etapes["concept"] = concept
    etapes["expansion"] = termes

    # (2) search vector-basedle on the query enrichie
    fragments = rech.chercher(requete_enrichie, k=k)
    etapes["fragments"] = fragments

    # (3) structuration on the fly, contrainte by the ontology
    graphe = build_ras(frags, requete_enrichie, ontologie=onto, k=k)
    etapes["graphe"] = graphe
    return etapes


def main():
    bandeau("Lab 28-6 — Integrating the semantic layer (multi-resolution)")
    taxo = Taxonomy.load()
    onto = Ontology.load()
    frags = load_fragments()
    rech = Search(frags)

    for requete in ["cavitation", "sealing defect"]:
        print("═" * 74)
        print(f"USER QUERY (local vocabulary): \"{requete}\"")
        et = pipeline(requete, taxo, onto, frags, rech)

        print(f"\n  [1] Couche TAXONOMY — concept canonique : {et['concept']}")
        print(f"      expansion: {', '.join(et['expansion'][:5])}…")

        print("\n  [2] RETRIEVAL enrichi — top fragments :")
        for f in et["fragments"][:3]:
            print(f"      {f['id']} (score {f['score']:.2f}) — {f['title']}")

        print(f"\n  [3] The ONTOLOGY layer — a business mini-graph "
              f"({len(et['graphe'])} edges, all schema-compliant):")
        if et["graphe"].aretes:
            for s, l, o in et["graphe"].aretes:
                print(f"      {s} --{l}--> {o}")
        else:
            print("      (no typed relation on these fragments)")
        print()

    print("═" * 74)
    print("THE MESSAGE: the semantic layer is not an isolated module, it is a")
    print("FRAMING of the flow. Upstream, the taxonomy aligns the vocabulary of")
    print("the user onto that of the documents (recall). Downstream, the ontology")
    print("guarantees that the relations extracted are licit (precision). Between")
    print("the two, the vector retrieval does its work — but framed.")
    print("\nThat is the thesis of Part V: structure the KNOWLEDGE of the domain, not")
    print("only the CONTENT of the documents.")


if __name__ == "__main__":
    main()
