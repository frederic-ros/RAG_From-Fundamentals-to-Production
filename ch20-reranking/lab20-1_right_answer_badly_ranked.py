# -*- coding: utf-8 -*-
"""
Lab 20-1 — The right answer, badly ranked (retrieval is not ranking)

Learning objective
------------------
The earlier chapters won RECALL: the right answer is, almost certainly, somewhere
in the candidate list. But "somewhere" is not "at the top". This lab shows the
problem full size: the right fragment, perfectly present, ranked FAR DOWN by the
initial retrieval — behind neighbouring codes (M-17, M-19) that resemble it.

    Finding and ranking are two different problems.

A query with an exact reference is asked ("motor M-18"). The bi-encoder, the
first-stage retrieval, confuses the neighbouring codes and relegates the right
fragment. The harm is observed here; the remedy, the cross-encoder, comes in the
next lab.

No API key. Reloads corpus/fragments.json.
Run generate_corpus.py first.
"""

import json
from pathlib import Path

import reranklib as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 20-1 — The right answer, badly ranked (retrieval is not ranking)")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    texts = [f["text"] for f in frags]
    print(f"\nModel mode: {R.mode()}")
    print(f"Corpus : {len(frags)} fragments de maintenance "
          "(motors M-17, M-18, M-19; pump P-42...).")

    # The right fragment: the reference procedure for motor M-18 (id=0).
    best = 0
    question = "motor M-18"
    print(f"\nQuery (with an exact reference): \"{question}\"")
    print(f"Expected right fragment: #{best} — \"{texts[best][:60].strip()}…\"")

    # --- The initial retrieval: the bi-encoder --------------------------------
    bi = R.BiEncoder(texts)
    ranking = bi.rank(question)
    order = [i for i, _ in ranking]
    best_rank = R.rank_of(order, best)

    print("\n" + "=" * 78)
    print("WHAT THE INITIAL RETRIEVAL BRINGS BACK (the bi-encoder)")
    print("=" * 78)
    print(f"  {'rank':>4s} | {'id':>3s} | {'score':>6s} | subject")
    print("  " + "-" * 50)
    for rank, (i, s) in enumerate(ranking[:8], start=1):
        mark = "  <-- THE RIGHT ONE, at last" if i == best else ""
        print(f"  {rank:4d} | {i:3d} | {s:6.3f} | {frags[i]['subject']}{mark}")
    print("  ...")
    print(f"\n  -> The right fragment #{best} is ranked {best_rank} out of {len(frags)}.")
    print("     Ahead of it: fragments about M-17 and M-19 (NEIGHBOURING codes) and")
    print("     restatements about the M-18. The retrieval did FIND the right")
    print("     fragment... but it RANKED it badly.")

    print("\n" + "=" * 78)
    print("WHY? (the blind spot on codes)")
    print("=" * 78)
    print("- The bi-encoder encodes each text SEPARATELY, then compares by distance.")
    print("- To it, \"M-17\", \"M-18\" and \"M-19\" are near-identical subjects: the same")
    print("  motor family, the same words around them. It does not read the number.")
    print("- The result: it mixes the right fragment with its neighbours, and it drowns.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- All the recall in the world is useless if the PRECISION at the top is bad:")
    print("  the generation model will read only the first few fragments.")
    print("- Finding (recall) and ranking (precision at the top) are two distinct trades.")
    print("- What is missing is a step that RE-READS the question and each candidate together.")

    print("\nWHAT TO REMEMBER")
    print(f"- The right fragment is in the list (rank {best_rank}), but not at the top.")
    print("- Retrieval optimises recall, not the fine order of the summit.")
    print("- The remedy is called re-ranking: the subject of Lab 20-2.")


if __name__ == "__main__":
    main()
