# -*- coding: utf-8 -*-
"""
Lab 21-4 — The trap of "its" (conversational rewriting)

Learning objective
------------------
As soon as a RAG holds a dialogue, one transformation becomes unavoidable. The
user asks "tell me about pump P-42", and then follows with "and what is ITS
safety procedure?". Taken alone the second question cannot be found: the search
engine knows nothing of the thread of the dialogue, and the pronoun "its" refers
to nothing for it.

    Retrieval does not understand pronouns. The question must become
    self-contained.

This lab shows the failure of the search on the raw conversational question, then
rewrites it by injecting the subject from the history ("the safety procedure of
pump P-42"), and the right answer reappears.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import qtlib as Q

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 21-4 — The trap of \"its\" (conversational rewriting)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    R = Q.Search(texts)
    print(f"\nMode de search : {Q.mode()}")

    # The dialogue turns, taken from the annotated corpus.
    req = next(r for r in data["queries"] if r["type"] == "rewriting")
    history = req["history"]
    question = req["question"]
    best = req["relevant"][0]

    print("\nDialogue en cours :")
    for tour in history:
        print(f"    > {tour}")
    print(f"    > {question}   <-- \"its\" refers to what?")
    print(f"\nExpected right document: #{best} — \"{texts[best][:55].strip()}…\"")

    # --- The raw search, on the conversational question -----------------------
    direct = [i for i, _ in R.classer(question)]
    rank_direct = Q.rank_of(direct, best)
    print("\n" + "=" * 78)
    print("1) THE RAW SEARCH (on \"its safety procedure\")")
    print("=" * 78)
    for rank, (i, s) in enumerate(R.classer(question)[:5], start=1):
        mark = "  <-- le best" if i == best else ""
        print(f"  rank {rank} : #{i:2d} [{frags[i]['subject']}]{mark}")
    print(f"\n  The best document #{best} sits at rank {rank_direct}: without the subject, the")
    print("  the search lands on the GENERAL safety procedure, not the one for P-42.")

    # --- The rewriting --------------------------------------------------------
    subject = Q.extract_subject(history)
    rewritten_question = Q.rewriting(question, history)
    rewritten = [i for i, _ in R.classer(rewritten_question)]
    rewritten_rank = Q.rank_of(rewritten, best)
    print("\n" + "=" * 78)
    print("2) WITH REWRITING (the pronoun is resolved through the history)")
    print("=" * 78)
    print(f"  Subject found in the history: \"{subject}\"")
    print(f"  Rewritten question (self-contained): \"{rewritten_question}\"")
    print()
    for rank, (i, s) in enumerate(R.classer(rewritten_question)[:3], start=1):
        mark = "  <-- the right one, found" if i == best else ""
        print(f"  rank {rank} : #{i:2d} [{frags[i]['subject']}]{mark}")
    print(f"\n  The right document #{best} is now at rank {rewritten_rank}.")

    # --- Metrics ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("THE GAIN, IN FIGURES")
    print("=" * 78)
    print(f"  {'method':<16s} | {'rank of right doc':>17s} | {'MRR':>6s}")
    print("  " + "-" * 44)
    print(f"  {'brute':<16s} | {str(rank_direct):>15s} | {Q.mrr(direct, [best]):6.3f}")
    print(f"  {'rewriting':<16s} | {str(rewritten_rank):>15s} | "
          f"{Q.mrr(rewritten, [best]):6.3f}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The search engine ignores the thread of the dialogue: \"its\" designates")
    print("  nothing for it, and the raw question goes astray.")
    print("- To rewrite is to re-inject the subject from the history, making the")
    print("  question SELF-CONTAINED, understandable without the conversational context.")
    print("- This is the key transformation of conversational RAG; a later chapter")
    print("  returns to it in detail.")

    print("\nWHAT TO REMEMBER")
    print("- Retrieval does not understand pronouns: \"its\", \"their\", \"that one\"...")
    print("- A conversational question must become self-contained before the search.")
    print("- Rewriting resolves the references from the previous turns.")


if __name__ == "__main__":
    main()
