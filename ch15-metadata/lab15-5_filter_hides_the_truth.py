# -*- coding: utf-8 -*-
"""
Lab 15-5 — The filter that hides the truth (Julien)

Learning objective
------------------
The other side of the coin, and the most mature lesson of the chapter. The
previous lab showed the power of filters; this one shows their danger. A filter
is not neutral: to filter is to EXCLUDE. And what is excluded, the system never
sees again — even when it is precisely the right answer.

  To filter is to exclude. So choosing better is not seeing everything.

Scenario: Julien is looking for the flange tightening torque. The right answer
lives in a document dated 2023, but it is a MECHANICAL CONSTANT, valid at all
times. A "date > 2024" filter, reasonable enough for setting aside what has
expired, makes that permanent truth disappear. The damage is shown, then two
remedies: widen the window, or use a SOFT filter that spares the information
marked as permanent.

Search backend: sentence-transformers if available, TF-IDF otherwise.
No API key. Run generate_corpus.py first.
"""

import corpus as C
import embeddings as E

QUESTION = "What is the flange tightening torque?"
STRICT_THRESHOLD = "2024-01-01"


def main() -> None:
    print("=" * 78)
    print("Lab 15-5 — The filter that hides the truth (Julien)")
    print("=" * 78)

    try:
        docs = C.load()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    print(f"\nSearch backend: {E.mode()}")
    print(f"Question: \"{QUESTION}\"")

    engine = E.SimilarityEngine([d.text for d in docs])
    ranking = engine.rank(QUESTION)

    # The right answer, with no filter at all.
    best = docs[ranking[0][0]]
    print("\n" + "=" * 78)
    print("NO FILTER — WHAT THE SEARCH FINDS")
    print("=" * 78)
    print(f"  best document: {best.id} (date {best.meta('date')})")
    print(f"    \"{best.text[:96]}…\"")
    print(f"  Is this information time-bound? status \"{best.meta('status')}\", "
          f"permanence \"{best.meta('permanence', 'not stated')}\".")

    # --- The reasonable filter... that hides the truth -----------------------
    print("\n" + "=" * 78)
    print(f"WITH A \"date > {STRICT_THRESHOLD}\" FILTER (reasonable... in appearance)")
    print("=" * 78)
    survivors = [(i, s) for i, s in ranking
                 if docs[i].meta("date") > STRICT_THRESHOLD]
    if survivors:
        kept = docs[survivors[0][0]]
        print(f"  document kept: {kept.id} (date {kept.meta('date')})")
    else:
        print("  no document passes the filter.")
    excluded = best.meta("date") <= STRICT_THRESHOLD
    if excluded:
        print(f"\n  Yet the right answer ({best.id}, {best.meta('date')}) is EARLIER")
        print("  than the threshold: the filter excluded it. The system never sees it")
        print("  again — even though it is a constant that still holds.")

    # --- Remedy 1: widen the window -----------------------------------------
    print("\n" + "=" * 78)
    print("REMEDY 1 — WIDEN THE WINDOW (date > 2023-01-01)")
    print("=" * 78)
    wide = [(i, s) for i, s in ranking if docs[i].meta("date") > "2023-01-01"]
    if wide:
        r = docs[wide[0][0]]
        print(f"  document kept: {r.id} (date {r.meta('date')}) — the truth reappears.")
    print("  But widening also risks letting expired material back in: this setting")
    print("  moves the problem rather than solving it.")

    # --- Remedy 2: a soft filter --------------------------------------------
    print("\n" + "=" * 78)
    print("REMEDY 2 — A SOFT FILTER (recent date OR marked \"permanent\")")
    print("=" * 78)

    def soft(d):
        return d.meta("date") > STRICT_THRESHOLD or d.meta("permanence") == "permanent"

    softly = [(i, s) for i, s in ranking if soft(docs[i])]
    if softly:
        r = docs[softly[0][0]]
        print(f"  document kept: {r.id} (date {r.meta('date')}, "
              f"permanence \"{r.meta('permanence', 'none')}\").")
    print("  The filter keeps its rigour on time-bound documents, but spares the")
    print("  explicitly permanent ones. You choose better WITHOUT going blind.")

    print("\nWHAT TO REMEMBER")
    print("- To filter is to exclude: what you remove, the system no longer sees.")
    print("- A date filter can hide an older permanent truth.")
    print("- Choosing better is not seeing everything: a good filter plans its exceptions.")


if __name__ == "__main__":
    main()
