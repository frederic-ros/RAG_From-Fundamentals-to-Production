# -*- coding: utf-8 -*-
"""
Lab 23-1 — Retrieval exposed as a tool: the ReAct loop

Learning objective
------------------
Build an agent's loop — Thought / Action / Observation — where search is no
longer a fixed step but a TOOL called when needed. The search is exposed as a
tool (name, description, schema, call log), and the minimal loop is run:

    plan -> retrieve (a tool call) -> judge "enough?" -> relaunch or answer

bounded by an iteration budget and a stopping condition.

The "brain" that decides is a rule function WITH NO LLM — and that is the whole
point: the loop already works. The day an LLM (Ollama) replaces the rule, the
STRUCTURE of the loop does not change. That is checked here: the same code, an
interchangeable brain.

A single-pass question (one turn) is compared with a multi-facet one (several
turns triggered by the brain). This is the incompleteness of Chapter 22, resolved
by a SECOND search decided by the agent.

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentlib as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def montrer_outil(tool):
    print("  The tool exposed to the model:")
    print(f"    name         : {tool.name}")
    print(f"    description : {tool.description}")
    print(f"    schema      : {json.dumps(tool.schema, ensure_ascii=False)}")


def jouer(question, facets, tool, budget=4):
    res = A.react_loop(question, facets, tool, budget=budget)
    for t in res["trace"]:
        follow = "STOP — answer" if t["decision"] == "STOP" \
            else f"relaunch -> \"{t['next']}\""
        print(f"    Turn {t['turn']} | Thought: {t['thought']}")
        print(f"             Action: search(\"{t['query']}\")  "
              f"→ Observation: {t['observation']}")
        print(f"             Judgement: {follow}")
    couv, manq = A.coverage(res["context"], facets)
    print(f"    Sortie: {res['exit']} | coverage {couv*100:.0f}% "
          f"| cost {res['cost']} call(s)")
    return res


def main() -> None:
    print("=" * 78)
    print("Lab 23-1 — Retrieval exposed as a tool: the ReAct loop")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]
    rech = A.Search([f["text"] for f in frags])
    tool = A.SearchTool(rech, frags)

    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Active brain: {A.mode_brain()}")
    if A.mode_brain() == "rule":
        print("Brain = the rule function, with no LLM. For a real local LLM:")
        print("  OLLAMA_MODEL=llama3.2 python lab23-1_react_loop.py")
    print()
    montrer_outil(tool)

    # --- Question mono-passe -------------------------------------------------
    print("\n" + "=" * 78)
    print("1) A SINGLE-PASS QUESTION — one turn is enough")
    print("=" * 78)
    q1 = "What is the emergency stop procedure for pump P-42?"
    print(f"Question: \"{q1}\"")
    jouer(q1, ["P-42"], tool, budget=4)

    # --- Question multi-facets ----------------------------------------------
    print("\n" + "=" * 78)
    print("2) A MULTI-FACET QUESTION — the agent triggers further searches itself")
    print("=" * 78)
    q2 = "Compare the emergency stop procedures of pumps P-12, P-42 and P-88."
    print(f"Question (3 facets): \"{q2}\"")
    jouer(q2, ["P-12", "P-42", "P-88"], tool, budget=5)

    # --- The journal of the tool ----------------------------------------------
    print("\n" + "=" * 78)
    print("3) THE TOOL LOG (the successive calls)")
    print("=" * 78)
    for i, call in enumerate(tool.log, 1):
        print(f"    call {i}: search(\"{call['query']}\") "
              f"→ {call['results']}")

    # --- Cerveau interchangeable --------------------------------------------
    print("\n" + "=" * 78)
    print("4) THE LOOP DOES NOT CHANGE WHEN THE BRAIN CHANGES")
    print("=" * 78)
    print("    The same react_loop() function runs with rule_brain (here) or with")
    print("    llm_brain (if Ollama is running). The rule brain is forced here, for")
    print("    showing that the trace is identical in structure:")
    res = A.react_loop(q2, ["P-12", "P-42", "P-88"], tool, budget=5,
                         brain=A.rule_brain)
    print(f"    rule_brain: {res['cost']} turns, exit \"{res['exit']}\".")
    print("    Plugging in Ollama does not touch the loop — only the JUDGEMENT.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  Search has become a TOOL called when needed, not a fixed step.")
    print("  The single-pass question resolves in one turn; the multi-facet one")
    print("  triggers successive searches by itself — the incompleteness of Chapter 22")
    print("  gives way to a SECOND search decided by the agent.")
    print("\n  WHAT TO REMEMBER: the brain may be a rule or an LLM; the ReAct loop")
    print("  (Thought/Action/Observation) is the same. It is the agent's skeleton.")


if __name__ == "__main__":
    main()
