# -*- coding: utf-8 -*-
"""
Lab 28-1 — The taxonomic guardrail (query expansion)
"The technician says 'cavitation', the report writes 'hydrodynamic erosion'"

The aim: show that a simple, well-built taxonomy eliminates the semantic false
negatives of a vector RAG. The technician's local business term ("cavitation") is
absent from the reports, which use the official term ("hydrodynamic erosion").
Without a semantic layer, the search fails.

The steps: resolve the query term onto its canonical concept, then widen the
query with the parents, siblings and children AND their synonyms.

Recall on the "business" queries collapses without expansion and recovers with
it. THIS IS THE VERIFICATION LAB for the synonym lists of the taxonomy: if they
stop matching the reports, the gain here falls to zero with no error raised. The
French baseline on the business terms is 40% without against 73% with.

No API key. Run generate_corpus.py first.
"""

from businesskit import (Taxonomy, Search, mapper_concept, recall,
                       load_fragments, bandeau, CORPUS)
import json


def rapports_pertinents(frags, pannes_attendues):
    """The report IDs whose failure matches the ground truth."""
    return [f["id"] for f in frags
            if set(f["failures"]) & set(pannes_attendues)]


def main():
    bandeau("Lab 28-1 — The taxonomic guardrail (query expansion)")
    taxo = Taxonomy.load()
    frags = load_fragments()
    requetes = json.loads((CORPUS / "queries.json").read_text(encoding="utf-8"))
    rech = Search(frags)
    K = 5

    print(f"\n{'Req':<4}{'type':<10}{'terme':<26}"
          f"{'recall W/OUT':>13}{'recall WITH':>12}  concept")
    print("─" * 78)

    cumul_sans, cumul_avec = [], []
    for q in requetes:
        cibles = rapports_pertinents(frags, q["expected_failures"])

        # --- without expansion ---------------------------------------------
        rec_sans = [f["id"] for f in rech.chercher(q["text"], k=K)]
        r_sans = recall(rec_sans, cibles)

        # --- with expansion taxonomique ---------------------------------
        concept = mapper_concept(q["text"], taxo)
        if concept:
            termes = taxo.expansion(concept)
            requete_enrichie = q["text"] + " " + " ".join(termes)
        else:
            requete_enrichie = q["text"]
        rec_avec = [f["id"] for f in rech.chercher(requete_enrichie, k=K)]
        r_avec = recall(rec_avec, cibles)

        cumul_sans.append(r_sans)
        cumul_avec.append(r_avec)
        print(f"{q['id']:<4}{q['type']:<10}{q['text'][:24]:<26}"
              f"{r_sans:>11.0%}{r_avec:>12.0%}  {concept or '—'}")

    print("─" * 78)
    moy = lambda xs: sum(xs) / len(xs)
    i_std = [i for i, q in enumerate(requetes) if q["type"] == "standard"]
    i_met = [i for i, q in enumerate(requetes) if q["type"] == "business"]

    print(f"\nMean recall OVERALL   without {moy(cumul_sans):.0%}  ->  with {moy(cumul_avec):.0%}")
    print(f"Mean recall STANDARD  without {moy([cumul_sans[i] for i in i_std]):.0%}"
          f"  ->  with {moy([cumul_avec[i] for i in i_std]):.0%}")
    print(f"Mean recall BUSINESS  without {moy([cumul_sans[i] for i in i_met]):.0%}"
          f"  ->  with {moy([cumul_avec[i] for i in i_met]):.0%}")

    print("\n" + "─" * 78)
    print("READING: on the STANDARD terms, already present in the reports, the")
    print("expansion brings little. On the LOCAL BUSINESS terms, absent from the")
    print("reports, it lifts recall from almost nothing to the essential: that is")
    print("the direct value of the semantic layer — no fine-tuning,")
    print("no graph, no heavy infrastructure.")
    print("\nA NUANCE: watch the noise as well. Too wide an expansion brings")
    print("back neighbouring fragments that are not relevant (false positives). The")
    print("taxonomy reduces the false negatives; it does not remove every risk.")


if __name__ == "__main__":
    main()
