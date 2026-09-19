# -*- coding: utf-8 -*-
"""
Lab 23-5 — The instability of the agent: measuring, then reducing the variance

Learning objective
------------------
The power to decide when to search has a price: the agent loses determinism. Two
runs on the SAME question may follow different paths — above all when the
retrieval scores are close (near-equivalent fragments) or when the brain is an
LLM at a non-zero temperature.

This lab MEASURES that instability, then shows how to reduce it:

  1. ranking noise is injected (near-equal scores that flip) and the same loop is
     run N times: the variability of the trajectories and of the cost (the number
     of turns) is measured, through the standard deviation;
  2. the variance is REDUCED by stabilising the ranking (no noise, temperature 0):
     the trajectory becomes unique again;
  3. the result is tied back to the "instability" of Chapter 22 (failure 7): the
     same cause, one storey higher.

Without Ollama, the source of instability is simulated by ranking noise, made
deterministic by a seed so that the lab itself stays reproducible. With Ollama,
the temperature of the brain adds a second, real source of instability.

No API key. Run generate_corpus.py first.
"""

import json
import statistics
from pathlib import Path

import agentlib as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def loop_with_noise(question, facets, frags, budget, noise, seed):
    """A ReAct loop whose retrieval is noisy: near-equal scores that flip.

 On reconstruit here the boucle for pouvoir injecter the bruit To EACH appel of tool
    with a given seed, which the standard loop does not do.
 """
    rech = A.Search([f["text"] for f in frags])
    context, vus, trace = [], set(), []
    query = question
    for tour in range(1, budget + 1):
        ordre = rech.rank(query, k=3, noise=noise, seed=seed + tour)
        obs = [frags[i]["subject"] for i, _ in ordre]
        nouveau = next((s for s in obs if s not in vus), obs[0])
        if nouveau not in vus:
            context.append(next(f for f in frags if f["subject"] == nouveau))
            vus.add(nouveau)
        trace.append(nouveau)
        couv, missing = A.coverage(context, facets)
        if not missing:
            break
        query = f"emergency stop pump {missing[0]}"
    return trace


def main() -> None:
    print("=" * 78)
    print("Lab 23-5 — The instability of the agent: measuring, then reducing the variance")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Brain: {A.mode_brain()}")

    question = "Compare the emergency stop procedures of pumps P-12, P-42 and P-88."
    facets = ["P-12", "P-42", "P-88"]
    N = 8

    # =====================================================================
    # 1) With bruit of classement : trajectoires and costs variables
    # =====================================================================
    print("\n" + "=" * 78)
    print(f"1) WITH RANKING NOISE — {N} runs of the same question")
    print("=" * 78)
    print(f"Question (3 facets): \"{question}\"")
    trajectoires, couts = [], []
    for essai in range(N):
        tr = loop_with_noise(question, facets, frags, budget=6,
                               noise=0.12, seed=essai * 100)
        trajectoires.append(tr)
        couts.append(len(tr))
        print(f"    run {essai+1}: {len(tr)} turns | path {tr}")
    distinctes = len({tuple(t) for t in trajectoires})
    print(f"\n  Trajectoires distinctes : {distinctes} / {N}")
    print(f"  Cost (turns): mean {statistics.mean(couts):.1f}, "
          f"standard deviation {statistics.pstdev(couts):.2f}, "
          f"min {min(couts)}, max {max(couts)}")
    print("  The same question, the same documents — but different PATHS and a cost")
    print("  that varies. This is the instability specific to the agent.")

    # =====================================================================
    # 2) Without bruit : the trajectoire redevient unique
    # =====================================================================
    print("\n" + "=" * 78)
    print(f"2) WITHOUT NOISE (a stabilised ranking) — {N} runs")
    print("=" * 78)
    trajectoires, couts = [], []
    for essai in range(N):
        tr = loop_with_noise(question, facets, frags, budget=6,
                               noise=0.0, seed=essai * 100)
        trajectoires.append(tr)
        couts.append(len(tr))
    distinctes = len({tuple(t) for t in trajectoires})
    print(f"  Trajectoires distinctes : {distinctes} / {N}")
    print(f"  Cost (turns): mean {statistics.mean(couts):.1f}, "
          f"standard deviation {statistics.pstdev(couts):.2f}")
    print(f"  Chemin unique : {trajectoires[0]}")
    print("  By removing the source of instability, scores that are too close, the")
    print("  loop becomes deterministic again: one path, a constant cost.")

    # =====================================================================
    # 3) The lien with the panne 7 of the chapitre 22
    # =====================================================================
    print("\n" + "=" * 78)
    print("3) THE LINK WITH THE INSTABILITY OF CHAPTER 22 (failure 7)")
    print("=" * 78)
    print("  In Chapter 22, scores that were too close made the RANKING vary")
    print("  from one run to the next. Here, in agent mode, the same cause makes the")
    print("  WHOLE PATH vary: which facet is handled first, how many turns, what cost.")
    print("  The instability propagates from the search to the decision.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  The autonomy of the agent introduces variance: trajectories and costs")
    print("  change from one run to the next. It is MEASURED (standard deviation, the")
    print("  number of distinct trajectories) and REDUCED (stabilise the ranking,")
    print("  temperature 0, break ties deterministically).")
    print("\n  WHAT TO REMEMBER: an agent you cannot reproduce, you cannot")
    print("  test. Measuring the variance is the first step towards mastering it.")


if __name__ == "__main__":
    main()
