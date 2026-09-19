# -*- coding: utf-8 -*-
"""
Lab 15-6 — Sophie against Julien (bonus)

Learning objective
------------------
The synthesis of the chapter, carried by the running example. The same question,
the same engine, the same corpus. All that changes is which metadata each
profile privileges — and the answer changes with it.

  There is no such thing as a relevant document.
  There is a document relevant to a given context.

Sophie (local authority) wants what is official, current and approved. Julien
(industry) wants the manufacturer's manual, including the historical one for an
older machine still in service. A deliberately ambiguous maintenance question is
asked, and each profile's "lens" is applied: two legitimate, opposite answers to
the same query.

Search backend: sentence-transformers if available, TF-IDF otherwise.
No API key. Run generate_corpus.py first.
"""

import corpus as C
import embeddings as E

QUESTION = "Which maintenance procedure should be applied?"


# A profile's "lens": a filtering predicate plus a sort key.
PROFILES = {
    "Sophie (local authority)": {
        "wants": "official, current, approved",
        "filter": lambda d: d.meta("status") == "in force"
                  and d.meta("source") in {"official", "regulatory"},
        "sort": lambda d: d.meta("date"),     # most recent first
    },
    "Julien (industry)": {
        "wants": "manufacturer's manual, the relevant revision, history included",
        "filter": lambda d: d.meta("source") == "supplier"
                  and d.meta("type", "") == "technical manual",
        "sort": lambda d: d.meta("date"),
    },
}


def main() -> None:
    print("=" * 78)
    print("Lab 15-6 — Sophie against Julien (bonus)")
    print("=" * 78)

    try:
        docs = C.load()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    print(f"\nSearch backend: {E.mode()}")
    print(f"Shared question: \"{QUESTION}\"")

    # The search is IDENTICAL for both: the whole corpus is ranked.
    engine = E.SimilarityEngine([d.text for d in docs])
    ranking = engine.rank(QUESTION)
    global_order = [docs[i] for i, _ in ranking]

    print("\n" + "=" * 78)
    print("THE SAME SEARCH FOR EVERYONE (top 4 by similarity)")
    print("=" * 78)
    for i, s in ranking[:4]:
        d = docs[i]
        print(f"  sim {s:.3f} — {d.id} (source {d.meta('source')}, status {d.meta('status')})")

    # Then each profile's lens is applied.
    for name, profile in PROFILES.items():
        print("\n" + "=" * 78)
        print(f"LENS — {name}")
        print("=" * 78)
        print(f"  wants: {profile['wants']}")
        candidates = [d for d in global_order if profile["filter"](d)]
        candidates = sorted(candidates, key=profile["sort"], reverse=True)
        if candidates:
            kept = candidates[0]
            print(f"  document kept: {kept.id}")
            print(f"    \"{kept.text[:92]}…\"")
            print(f"    (source {kept.meta('source')}, status {kept.meta('status')}, "
                  f"date {kept.meta('date')})")
        else:
            print("  no document matches this profile.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The same question, the same engine, the same corpus, the same scores.")
    print("- Only the privileged metadata changes — and the answer with it.")
    print("- Sophie gets the official document in force; Julien, the manufacturer's manual.")
    print("- Neither answer is \"the\" right one in the absolute: each is the right one")
    print("  FOR its context.")

    print("\nWHAT TO REMEMBER")
    print("- There is no such thing as a relevant document in itself.")
    print("- There is a document relevant to a given context.")
    print("- Metadata is the link between the information and its user.")


if __name__ == "__main__":
    main()
