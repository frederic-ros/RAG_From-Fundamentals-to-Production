# -*- coding: utf-8 -*-
"""
Lab 22-4 — The loop: what a single pass can never see

Learning objective
------------------
Chapter 22 identifies, beneath the gravest failures — incompleteness, misleading
assurance, instability — one common ROOT: the system never rereads itself. It
searches, answers, stops. This lab PROVES it with a controlled experiment,
single pass against loop, on the same question.

  Most serious failures do not come from a FAILED search,
  but from a search that was NEVER REPLAYED.

The loop is: search -> answer -> judge the coverage -> relaunch on the missing
parts -> stop, either covered or out of budget. It is exactly the "enough?"
diamond of Chapter 23, placed here as a revealer of the failure.

No API key. Run this first: python generate_corpus.py
"""

import json
from pathlib import Path

import ragdiag as R

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def passe_unique(question, frags):
    """RAG classique : a search, a fragment dominant, an answer."""
    search = R.Search([f["text"] for f in frags])
    top1 = search.rank(question)[0][0]
    ctx = [frags[top1]["text"]]
    return R.generate_answer(question, ctx), [frags[top1]["subject"]]


def avec_boucle(question, parts, frags, budget=4):
    """RAG with a loop: judge the coverage and relaunch on the missing parts.

    Returns (answer, trace). The trace records each turn: the part targeted,
    the fragment retrieved, the decision taken.
 """
    search = R.Search([f["text"] for f in frags])
    context, trace, seen = [], [], set()
    # Turn 0: search on the whole question.
    query = question
    target = "whole question"
    for turn in range(1, budget + 1):
        top1 = search.rank(query)[0][0]
        frag = frags[top1]
        is_new = frag["subject"] not in seen
        if is_new:
            context.append(frag["text"])
            seen.add(frag["subject"])
        # The agent's answer rests on ALL the context accumulated so far, so
        # coverage is judged over the whole set of fragments gathered.
        answer = "\n".join(context)
        rate, missing = R.covers_question(answer, parts)
        trace.append({"turn": turn, "target": target, "frag": frag["subject"],
                      "coverage": rate, "missing": list(missing)})
        if not missing:
            # The final answer is written from the complete context.
            final_answer = R.generate_answer(question, context)
            return final_answer, trace, "complete coverage"
        # Relancer on the first volet manquant.
        target = missing[0]
        query = f"emergency stop pump {target}" if target.startswith("P-") \
            else f"remote work {target}"
    final_answer = R.generate_answer(question, context)
    return final_answer, trace, "budget exhausted"


def main() -> None:
    print("=" * 78)
    print("Lab 22-4 — La racine commune : passe unique vs boucle")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus introuvable. Lancez d'abord : python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    print(f"\nMode retrieval : {R.mode_retrieval()}   |   "
          f"Mode jugement : {R.generation_mode()}")

    question = ("Compare the emergency stop procedures of pumps "
                "P-12, P-42 et P-88.")
    parts = ["P-12", "P-42", "P-88"]

    # --- Passe unique --------------------------------------------------------
    print("\n" + "=" * 78)
    print("1) PASSE UNIQUE (RAG classique)")
    print("=" * 78)
    print(f"Question (3 parts): \"{question}\"")
    answer, src = passe_unique(question, frags)
    rate, missing = R.covers_question(answer, parts)
    print(f"  Fragment dominant transmis : {src[0]}")
    print(f"  Answer: {answer[:150]}")
    print(f"  Coverage: {rate*100:.0f} %  | missing parts: {missing}")
    print("  The system answers with what it found — and DOES NOT KNOW that")
    print("  misses two of the three parts. It does not re-read itself.")

    # --- With boucle ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("2) WITH A LOOP (search -> judge -> relaunch)")
    print("=" * 78)
    answer, trace, exit_reason = avec_boucle(question, parts, frags, budget=4)
    for t in trace:
        dec = "STOP (all covered)" if not t["missing"] \
            else f"relaunch on {t['missing'][0]}"
        print(f"  Turn {t['turn']} | target: {t['target']:<14s} | "
              f"retrieved: {t['frag']:<11s} | coverage {t['coverage']*100:>3.0f}% "
              f"| {dec}")
    final_coverage = trace[-1]["coverage"]
    final_missing = trace[-1]["missing"]
    print(f"\n  Exit: {exit_reason}.")
    print(f"  Final answer — coverage {final_coverage*100:.0f} % "
          f"| missing parts: {final_missing if final_missing else 'none'}")
    print(f"  Cost: {len(trace)} searches (against 1 for the single pass).")

    # --- Synthesis ------------------------------------------------------------
    print("\n" + "=" * 78)
    print("WHAT THE EXPERIMENT REVEALS")
    print("=" * 78)
    print("  The single pass does not DETECT its own incompleteness. The loop, by")
    print("  judging its own answer, sees the gap and relaunches — the AGENT THRESHOLD.")
    print("  Completeness has a price: more searches, so more cost and latency.")
    print("  Hence the need for a BUDGET and a STOPPING CONDITION (Chapter 23).")
    print("\n  REMEMBER: looping corrects incompleteness; knowing when to stop on an")
    print("  admission (\"I will not find it\") corrects the misleading assurance.")


if __name__ == "__main__":
    main()
