# -*- coding: utf-8 -*-
"""
Lab 15-1 — Two exact answers, only one valid (Sophie)

Learning objective
------------------
The flagship lab of the chapter. Two documents answer the same question, both
exact, both relevant. Only one is valid. The search alone cannot separate them —
and without metadata the system can answer falsely, with assurance.

  Relevance is not validity.

Corpus: the regulatory rate, 2021 edition (five per cent, repealed) against the
2024 edition (eight per cent, in force). Question: "what is the applicable
rate?". Both documents hold an exact rate. But only one rate is still in force —
and it is a piece of metadata, not the text, that says so.

Search backend: sentence-transformers if available, TF-IDF otherwise.
No API key. Run generate_corpus.py first.
"""

import re
import corpus as C
import embeddings as E


def extract_rate(text: str) -> str:
    m = re.search(r"(\w+)\s+per\s+cent", text)
    return f"{m.group(1)} per cent" if m else "(not found)"


def main() -> None:
    print("=" * 78)
    print("Lab 15-1 — Two exact answers, only one valid (Sophie)")
    print("=" * 78)

    try:
        docs = C.load()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    # Isolate the two editions of the rate.
    rates = [d for d in docs if d.id.startswith("rate-")]
    print(f"\nSearch backend: {E.mode()}")

    print("\nTHE TWO DOCUMENTS")
    print("-" * 78)
    for d in rates:
        print(f"  [{d.id}]  status={d.meta('status')}, date={d.meta('date')}")
        print(f"    \"{d.text[:88]}…\"")
        print(f"    rate stated: {extract_rate(d.text)}")

    question = "What is the applicable rate?"
    print("\n" + "=" * 78)
    print("NAIVE SEARCH (no metadata)")
    print("=" * 78)
    print(f"  question: \"{question}\"")

    engine = E.SimilarityEngine([d.text for d in rates])
    ranking = engine.rank(question)
    for rank, (i, score) in enumerate(ranking, start=1):
        d = rates[i]
        print(f"  {rank}. score {score:.3f} — {d.id} "
              f"(rate {extract_rate(d.text)}, status {d.meta('status')})")

    naive_winner = rates[ranking[0][0]]
    print(f"\n  The system would keep: {naive_winner.id} "
          f"-> answer \"{extract_rate(naive_winner.text)}\".")

    print("\n" + "=" * 78)
    print("THE PROBLEM")
    print("=" * 78)
    print("  Both answers are EXACT: those rates exist, word for word.")
    print("  Both documents are RELEVANT: they do talk about the rate.")
    if naive_winner.meta("status") != "in force":
        print(f"  But the document kept is \"{naive_winner.meta('status')}\": its answer")
        print("  is exact... and nonetheless FALSE, because out of date. No alarm rings.")
    else:
        print("  Here the best score happens to be right — but nothing GUARANTEED it:")
        print("  that is a stroke of luck in the wording, not a grounded decision.")

    print("\n" + "=" * 78)
    print("THE SOLUTION: A PIECE OF METADATA DECIDES")
    print("=" * 78)
    in_force = [d for d in rates if d.meta("status") == "in force"]
    valid = in_force[0]
    print("  Filter on status == \"in force\":")
    print(f"    valid document: {valid.id} -> \"{extract_rate(valid.text)}\".")
    print("  The text has not changed. What decides is the status metadata,")
    print("  invisible to the similarity engine.")

    print("\nWHAT TO REMEMBER")
    print("- Relevance is not validity: retrieval succeeds, the answer is false.")
    print("- Similarity is blind to time and to authority.")
    print("- A piece of metadata (status, date) restores the decision the vector ignores.")


if __name__ == "__main__":
    main()
