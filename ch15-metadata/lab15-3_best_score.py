# -*- coding: utf-8 -*-
"""
Lab 15-3 — When the best score is not the best document (Julien)

Learning objective
------------------
A counter-intuitive but common phenomenon: an OBSOLETE document, if it is
wordier, can obtain a better similarity score than a more concise OFFICIAL one.
The vector rewards lexical resemblance, not validity.

  The best vector is not always the best document.

Two sets of safety instructions are compared: the 2021 edition (obsolete, long,
repeating the word "safety") and the 2024 edition (in force, concise). With no
filter, the search crowns the obsolete one. It is corrected by a metadata
filter, and then the good practice is formalised: a two-stage RERANKING — filter
by metadata first, rank by similarity second.

Search backend: sentence-transformers if available, TF-IDF otherwise.
No API key. Run generate_corpus.py first.
"""

import corpus as C
import embeddings as E

QUESTION = "What are the applicable safety rules?"


def main() -> None:
    print("=" * 78)
    print("Lab 15-3 — When the best score is not the best document (Julien)")
    print("=" * 78)

    try:
        docs = C.load()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    safety = [d for d in docs if d.id.startswith("safety-")]
    print(f"\nSearch backend: {E.mode()}")
    print(f"Question: \"{QUESTION}\"")

    engine = E.SimilarityEngine([d.text for d in safety])
    ranking = engine.rank(QUESTION)

    print("\n" + "=" * 78)
    print("RANKING BY SIMILARITY (no metadata)")
    print("=" * 78)
    print(f"  {'score':>7}  {'status':12}  {'length':>8}  document")
    for i, score in ranking:
        d = safety[i]
        print(f"  {score:>7.3f}  {d.meta('status'):12}  {len(d.text.split()):>8}  {d.id}")

    winner = safety[ranking[0][0]]
    print(f"\n  Best score: {winner.id} (status \"{winner.meta('status')}\").")

    print("\n" + "=" * 78)
    print("THE PROBLEM")
    print("=" * 78)
    if winner.meta("status") != "in force":
        print("  The best-scored document is OBSOLETE. Why does it win?")
        print("  Because it is longer and repeats the vocabulary of the question:")
        print("  it \"resembles\" more. But resembling is not being valid.")
    else:
        print("  Here the official one wins on score — but that is not guaranteed:")
        print("  a wordier obsolete document can very well come out ahead.")

    print("\n" + "=" * 78)
    print("FIX 1 — A METADATA FILTER")
    print("=" * 78)
    in_force = [d for d in safety if d.meta("status") == "in force"]
    print("  Filter: status == \"in force\".")
    for d in in_force:
        print(f"    -> {d.id}  ({d.meta('date')})")
    print("  The filter sets the obsolete one aside, whatever its score.")

    print("\n" + "=" * 78)
    print("FIX 2 — TWO-STAGE RERANKING (the good practice)")
    print("=" * 78)
    print("  Stage 1: filter by metadata (status == \"in force\").")
    print("  Stage 2: rank the survivors by similarity.")
    survivors = [(i, s) for i, s in ranking
                 if safety[i].meta("status") == "in force"]
    for rank, (i, s) in enumerate(survivors, start=1):
        print(f"    {rank}. score {s:.3f} — {safety[i].id}")
    if survivors:
        kept = safety[survivors[0][0]]
        print(f"\n  Document kept: {kept.id}. Similarity does the separating,")
        print("  but only AFTER the metadata has guaranteed validity.")

    print("\nWHAT TO REMEMBER")
    print("- The vector score measures resemblance; the metadata measures validity.")
    print("- The best vector is not always the best document.")
    print("- Reranking: filter first, rank second — the basis of the advanced chapters.")


if __name__ == "__main__":
    main()
