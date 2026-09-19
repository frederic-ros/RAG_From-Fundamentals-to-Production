# -*- coding: utf-8 -*-
"""
Lab 23-4 — The counterpart: an iteration budget and a stopping condition

Learning objective
------------------
An agentic loop that can relaunch itself can also never stop. This lab shows,
on a question with no answer ("the emergency stop of P-99", which is absent from
the corpus):

  1. the loop WITH NO BRAKE, which would reformulate for ever;
  2. the iteration BUDGET: a hard ceiling on the number of calls;
  3. the STOPPING CONDITION: stopping on an ADMISSION too ("I did not find it"),
     rather than hammering the search — which answers the "misleading
     confidence" of the earlier chapters;
  4. the cost compared: the same agent, with and without guard rails, on all
     three kinds of question.

On determinism: at temperature 0 and with no noise, two runs give the same trace,
which matters for reproducible tests. Lab 23-5 explores the opposite instability.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentlib as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def boucle_sans_frein(question, facets, tool, plafond_secu=12):
    """Illustrate a loop that stops only on coverage, which is dangerous when the

 answer not existe not. `plafond_secu` is a garde-fou ultime for this TP (sinon the
 programme not se terminerait not) : it is precisely the argument of the chapitre.
 """
    tool.reset()
    context, vus, tours = [], set(), 0
    query = question
    while tours < plafond_secu:
        tours += 1
        obs = tool.call(query, k=3)
        nouveau = next((r for r in obs if r["subject"] not in vus), obs[0])
        if nouveau["subject"] not in vus:
            context.append(nouveau)
            vus.add(nouveau["subject"])
        couv, missing = A.coverage(context, facets)
        if not missing:
            return {"tours": tours, "exit": "coverage", "couv": couv}
        # Reformulates without let-up, and goes round in circles if no answer exists.
        query = f"emergency stop pump {missing[0]}"
    return {"tours": tours, "exit": "SAFETY CEILING reached (otherwise: infinite)",
            "couv": 0.0}


def boucle_arret_intelligent(question, facets, tool, budget=4):
    """A bounded loop plus a stopping condition on failure: if a turn brings back
    NO new relevant fragment, the conclusion is "not found" and the loop stops,
    instead of consuming the whole budget. The honest admission, rather than
    stubbornness.
 """
    tool.reset()
    context, vus, trace = [], set(), []
    query = question
    for tour in range(1, budget + 1):
        obs = tool.call(query, k=3)
        nouveau = next((r for r in obs if r["subject"] not in vus), None)
        progres = nouveau is not None
        if progres:
            context.append(nouveau)
            vus.add(nouveau["subject"])
        couv, missing = A.coverage(context, facets)
        trace.append({"turn": tour, "query": query, "progres": progres,
                      "couv": couv})
        if not missing:
            return {"trace": trace, "exit": "coverage complete", "couv": couv,
                    "tours": tour}
        if not progres:
            # Deux options : soit on cible a other volet, soit (here) on conclut
            # Failure, if no new fragment arrives any more.
            return {"trace": trace, "exit": "aveu : information introuvable",
                    "couv": couv, "tours": tour}
        query = f"emergency stop pump {missing[0]}"
    return {"trace": trace, "exit": "budget exhausted", "couv": couv, "tours": budget}


def main() -> None:
    print("=" * 78)
    print("Lab 23-4 — The counterpart: an iteration budget and a stopping condition")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = A.Search([f["text"] for f in frags])

    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Brain: {A.mode_brain()}")

    # =====================================================================
    # 1) The boucle without frein, on a question without answer
    # =====================================================================
    print("\n" + "=" * 78)
    print("1) THE LOOP WITH NO BRAKE — a question whose answer does not exist")
    print("=" * 78)
    q99 = "What is the emergency stop procedure for pump P-99?"
    print(f"Question: \"{q99}\"  (P-99 is NOT in the corpus)")
    tool = A.SearchTool(rech, frags)
    r = boucle_sans_frein(q99, ["P-99"], tool)
    print(f"  → {r['tours']} tours, exit : {r['exit']}")
    print("  With no ceiling this loop would NEVER stop: it reformulates a question")
    print("  with no answer, indefinitely. Hence the need for guard rails.")

    # =====================================================================
    # 2) Budget + condition of stop intelligente
    # =====================================================================
    print("\n" + "=" * 78)
    print("2) BUDGET PLUS A STOPPING CONDITION (admission rather than stubbornness)")
    print("=" * 78)
    tool = A.SearchTool(rech, frags)
    r = boucle_arret_intelligent(q99, ["P-99"], tool, budget=4)
    for t in r["trace"]:
        etat = "a new fragment" if t["progres"] else "NOTHING new"
        print(f"    Turn {t['turn']} | search(\"{t['query'][:40]}…\") -> {etat}")
    print(f"  → exit : {r['exit']} en {r['tours']} tour(s) (budget 4).")
    print("  The agent CONCLUDES failure instead of consuming its whole budget: the")
    print("  honest admission that answers the \"misleading confidence\" of Chapter 22.")

    # =====================================================================
    # 3) The cost compared, over the three kinds of question
    # =====================================================================
    print("\n" + "=" * 78)
    print("3) COST COMPARED — the same bounded agent, on 3 kinds of question")
    print("=" * 78)
    cas = [("single-pass", "What is the emergency stop procedure for pump "
            "P-42 ?", ["P-42"]),
           ("multi-facet", "Compare the emergency stop procedures of pumps "
            "P-12, P-42 et P-88.", ["P-12", "P-42", "P-88"]),
           ("no-answer", q99, ["P-99"])]
    print(f"  {'type':<14s} | {'tours':>5s} | exit")
    print("  " + "-" * 56)
    for typ, q, facets in cas:
        tool = A.SearchTool(rech, frags)
        r = boucle_arret_intelligent(q, facets, tool, budget=5)
        print(f"  {typ:<14s} | {r['tours']:>5d} | {r['exit']}")
    print("\n  The cost ADAPTS to the difficulty — and stays BOUNDED in every case.")

    # =====================================================================
    # 4) Determinism
    # =====================================================================
    print("\n" + "=" * 78)
    print("4) DETERMINISM — two identical runs (temperature 0, no noise)")
    print("=" * 78)
    q2 = "Compare the emergency stop procedures of pumps P-12, P-42 and P-88."
    traces = []
    for _ in range(2):
        tool = A.SearchTool(rech, frags)
        r = A.react_loop(q2, ["P-12", "P-42", "P-88"], tool, budget=5,
                           brain=A.rule_brain)
        traces.append([t["observation"] for t in r["trace"]])
    print(f"  Run 1: {traces[0]}")
    print(f"  Run 2: {traces[1]}")
    print(f"  Identiques : {traces[0] == traces[1]}")
    print("  With no randomness the loop is reproducible — indispensable for testing it.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  Giving an agent a tool is giving it an expense. Two guard rails frame it:")
    print("  the BUDGET (a hard ceiling on iterations) and the STOPPING CONDITION")
    print("  (knowing how to conclude, including \"not found\").")
    print("\n  WHAT TO REMEMBER: the loop gains in completeness what it loses in")
    print("  predictability. A budget plus a stopping condition make that trade-off")
    print("  manageable — and an honest admission beats a confidently invented answer.")


if __name__ == "__main__":
    main()
