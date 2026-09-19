# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 25 (agentic RAG, multi-agent).

A deterministic corpus organised BY DOMAIN, so that the specialist agents of
Lab 25-4 each have their own territory: maintenance (Julien), HR (Claire),
architecture (Sophie).

It also supplies:

  - a chain of DEPENDENCIES (P-42 -> E-7 -> L-3) for the investigator agent of
    Lab 25-2, which follows the links hop by hop;
  - a multi-turn CONVERSATION for the memory of Lab 25-3, holding two ELLIPTICAL
    questions ("And for the P-42?") whose subject exists only in the previous
    turn.

A NOTE ON THE ELLIPTICAL QUESTIONS. Turns 2 and 5 of the conversation are the
whole point of Lab 25-3: without short-term memory they lose their referent. The
detection is done by agentkit.resolve_referent(), on a list of ellipsis markers
("and for", "what about", "the same"). Those markers must match the wording of
the conversation below. Lab 25-3 prints, turn by turn, whether the referent was
resolved: run it after any edit here.

Run before the labs: python generate_corpus.py
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# --- The global corpus, annotated by domain -------------------------------
FRAGMENTS = [
    # ===== MAINTENANCE (Julien) =====
    {"id": 0, "domain": "maintenance", "subject": "P-42-role",
     "text": "Pump P-42 supplies cooling water to heat exchanger E-7 and to the "
             "circuit of production line L-3. It is a critical item of equipment."},
    {"id": 1, "domain": "maintenance", "subject": "E-7-dependency",
     "text": "Heat exchanger E-7 depends on the cooling water supplied by pump "
             "P-42; without it, the exchanger overheats within minutes."},
    {"id": 2, "domain": "maintenance", "subject": "L-3-dependency",
     "text": "Production line L-3 stops automatically if heat exchanger E-7 "
             "exceeds its set temperature, as a safety measure."},
    {"id": 3, "domain": "maintenance", "subject": "P-42-stop",
     "text": "Emergency stop of pump P-42: mushroom button, isolation of the "
             "discharge, lock off. Hydraulic brake, a stop in five seconds."},
    {"id": 4, "domain": "maintenance", "subject": "P-12-stop",
     "text": "Emergency stop of pump P-12: main isolator, closing the suction "
             "valve, purge. Immobilisation in thirty seconds."},
    {"id": 5, "domain": "maintenance", "subject": "M-18-overheating",
     "text": "Overheating of motor M-18: check the ventilation, the bearings and "
             "the load; clean the fins of the heat sink."},
    # ===== HR (Claire) =====
    {"id": 6, "domain": "hr", "subject": "remote-permanent",
     "text": "Remote work for permanent staff: up to three days a week after six "
             "months of service, subject to the manager's approval."},
    {"id": 7, "domain": "hr", "subject": "remote-apprentice",
     "text": "Remote work for apprentices: limited to one day a week, subject to "
             "the supervisor's agreement and a compliant workstation."},
    {"id": 8, "domain": "hr", "subject": "night-bonus",
     "text": "Night maintenance work gives entitlement to a salary supplement and "
             "to compensatory rest, under the collective agreement."},
    # ===== ARCHITECTURE (Sophie) =====
    {"id": 9, "domain": "archi", "subject": "rag-vs-finetuning",
     "text": "RAG injects fresh knowledge without retraining; fine-tuning adjusts "
             "the behaviour of the model. The two are often combined."},
    {"id": 10, "domain": "archi", "subject": "agent-vs-workflow",
     "text": "A workflow fixes the sequence of steps; an agent decides its own "
             "actions. The difference is where the decision sits, not the "
             "technology."},
    {"id": 11, "domain": "archi", "subject": "supervision",
     "text": "Every reliable multi-agent system has a supervisor that applies "
             "budgets and can interrupt execution: without one, it is an "
             "amplifier of risk."},
]

# Explicit dependencies, for the investigator agent of Lab 25-2.
DEPENDENCIES = {
    "P-42": ["E-7", "L-3"],
    "E-7": ["L-3"],
}


# --- Split by domain, for the specialist agents ---------------------------
DOMAINS = {
    "maintenance": {
        "agent": "Julien",
        "keywords": ["pump", "motor", "stop", "failure", "overheating",
                     "exchanger", "p-42", "p-12", "m-18", "e-7", "l-3",
                     "maintenance", "equipment", "cooling"],
        "fragments": [0, 1, 2, 3, 4, 5],
    },
    "hr": {
        "agent": "Claire",
        "keywords": ["remote work", "telework", "apprentice", "bonus", "salary",
                     "leave", "service", "permanent", "rest", "agreement",
                     "night"],
        "fragments": [6, 7, 8],
    },
    "archi": {
        "agent": "Sophie",
        "keywords": ["rag", "agent", "workflow", "architecture", "fine-tuning",
                     "supervisor", "multi-agent", "embedding", "decision"],
        "fragments": [9, 10, 11],
    },
}


# --- The multi-turn conversation (memory, Lab 25-3) ------------------------
# Turns 2 and 5 are ELLIPTICAL: their subject lives only in the previous turn.
# They must contain a marker from agentkit._ELLIPSIS_MARKERS ("and for" here),
# or Lab 25-3 has no reference left to resolve.
CONVERSATION = [
    "What is the emergency stop procedure for pump P-12?",
    "And for the P-42, is it the same protocol?",
    "What equipment does it cool?",
    "On the HR side, how many days of remote work for an apprentice?",
    "And for a permanent employee?",
]


def main() -> None:
    (CORPUS / "fragments.json").write_text(
        json.dumps({"fragments": FRAGMENTS, "dependencies": DEPENDENCIES},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "domains.json").write_text(
        json.dumps(DOMAINS, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "conversation.json").write_text(
        json.dumps({"turns": CONVERSATION}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    print("Generating the Chapter 25 test corpus:")
    print(f"  + fragments.json    : {len(FRAGMENTS)} fragments "
          f"(maintenance / HR / architecture) plus dependencies")
    print("  + domains.json      : 3 specialist domains "
          "(Julien / Claire / Sophie)")
    print(f"  + conversation.json : {len(CONVERSATION)} turns, for the memory")
    print("\n  Dependencies P-42 -> E-7 -> L-3: the investigator agent must decompose.")
    print("  The running threads: Julien (maintenance), Claire (HR), Sophie (architecture).")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
