# -*- coding: utf-8 -*-
"""
Lab 15-2 — The library with no labels (Sophie)

Learning objective
------------------
This lab makes the metaphor of the chapter concrete: a library whose labels have
all been torn off. Several versions of the same procedure, several sources,
several statuses — and, without metadata, the system can no longer separate
them: every jar looks alike.

  A piece of metadata does not improve the search, it improves the decision.

It proceeds in three stages: first the search alone (the scores are close,
nothing decides), then the DOCUMENT metadata is put back (date, version,
source), which identifies, and finally the BUSINESS metadata (status), which
judges. By the end the decision is obvious — and yet the SEARCH has not moved an
inch.

Search backend: sentence-transformers if available, TF-IDF otherwise.
No API key. Run generate_corpus.py first.
"""

import corpus as C
import embeddings as E

QUESTION = "What is the current remote work procedure?"


def main() -> None:
    print("=" * 78)
    print("Lab 15-2 — The library with no labels (Sophie)")
    print("=" * 78)

    try:
        docs = C.load()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    # Keep only the remote work documents (several versions and sources).
    library = [d for d in docs if d.id.startswith("remote-work-")]
    print(f"\nSearch backend: {E.mode()}")
    print(f"Question: \"{QUESTION}\"")

    engine = E.SimilarityEngine([d.text for d in library])
    ranking = engine.rank(QUESTION)

    # --- Stage 1: the search alone ------------------------------------------
    print("\n" + "=" * 78)
    print("STAGE 1 — THE SEARCH ALONE (labels torn off)")
    print("=" * 78)
    for i, score in ranking:
        print(f"  score {score:.3f} — {library[i].id}")
    leader = library[ranking[0][0]]
    print(f"\n  In the lead: {leader.id} (status \"{leader.meta('status')}\").")
    print("  The search names a favourite — but look at its status: nothing")
    print("  guarantees that the best-scored is the right one. With no validity")
    print("  label there is no way to decide. Every jar looks alike.")

    # --- Stage 2: document metadata (identify) ------------------------------
    print("\n" + "=" * 78)
    print("STAGE 2 — THE DOCUMENT METADATA GOES BACK ON (date, version, source)")
    print("=" * 78)
    by_date = sorted(library, key=lambda d: d.meta("date"), reverse=True)
    for d in by_date:
        print(f"  {d.meta('date')}  v={d.meta('version'):6} source={d.meta('source'):9} — {d.id}")
    most_recent = by_date[0]
    print(f"\n  The most recent is {most_recent.id} ({most_recent.meta('date')}).")
    print("  We can identify and order at last — but is that enough?")
    if most_recent.meta("status") != "in force":
        print(f"  Careful: the most recent one is \"{most_recent.meta('status')}\". The date")
        print("  alone does not guarantee validity.")

    # --- Stage 3: business metadata (judge) ---------------------------------
    print("\n" + "=" * 78)
    print("STAGE 3 — THE BUSINESS METADATA IS ADDED (status, trusted source)")
    print("=" * 78)
    valid = [d for d in library
             if d.meta("status") == "in force" and d.meta("source") == "official"]
    print("  Filter: status == \"in force\" AND source == \"official\".")
    for d in valid:
        print(f"    -> {d.id}  ({d.meta('date')}, {d.meta('version')})")
    print("\n  The decision is now obvious — and yet the SEARCH has not changed")
    print("  one iota. It is the metadata that decided.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Document metadata (date, version, source) IDENTIFIES.")
    print("- Business metadata (status, criticality) JUDGES.")
    print("- Neither touched the similarity scores: they act on the decision.")

    print("\nWHAT TO REMEMBER")
    print("- With no label, every document is worth the same.")
    print("- A piece of metadata does not improve the search, it improves the decision.")
    print("- Identify, then judge: two families of metadata, two roles.")


if __name__ == "__main__":
    main()
