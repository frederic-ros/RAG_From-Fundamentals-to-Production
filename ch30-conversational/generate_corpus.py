# -*- coding: utf-8 -*-
"""
generate_corpus.py — generates the Chapter 30 corpus (conversational RAG).

Writes in corpus/ :
 - documents.json : 16 fragments of documentation maintenance ;
 - conversation.json : a conversation multi-tours (technician Karim /
    RAG) with annotated anaphora and ellipsis, of which
 each tour 'user' porte sa query autonome of
 reference and the fragments attendus ;
 - conversation_longue.json : a conversation of 50 tours on a same
 intervention (pompe P-42), for the TP memory.

Fil rouge : maintenance industrielle, Karim (technician) & Julien (architecte).
Lancer : python generate_corpus.py
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


def D(i, titre, texte):
    return {"id": f"D{i:02d}", "titre": titre, "texte": texte}


DOCUMENTS = [
    D(1, "Pump P-42 — supplier",
      "Centrifugal pump P-42 is supplied by Sulzer under contract "
      "MAINT-2026-001. Spare parts are referenced with the same supplier."),
    D(2, "Pump P-42 — failure history",
      "Pump P-42 had two seal leak episodes in June 2026, traced in the "
      "intervention log."),
    D(3, "Valve V-7 — supplier",
      "The motorised valve V-7 is supplied by KSB. Six-monthly preventive "
      "maintenance is recommended by the manufacturer."),
    D(4, "Valve V-7 — failure history",
      "Valve V-7 jammed in the closed position in June 2026, resolved by "
      "replacing the actuator."),
    D(5, "Cavitation — diagnosis",
      "Cavitation is diagnosed by a gravel-like noise and pitting on the vanes, "
      "often due to an insufficient NPSH."),
    D(6, "Cavitation — remedy",
      "To correct cavitation, raise the pressure at the suction: raise the tank "
      "level, reduce the upstream pressure losses."),
    D(7, "Seal leak — procedure",
      "Replacing a mechanical seal requires prior electrical lock-off, draining "
      "of the pump casing, then a pressure test after reassembly."),
    D(8, "Electrical lock-off",
      "Electrical lock-off has five steps: separation, locking, identification, "
      "verification of the absence of voltage, earthing. It precedes any "
      "intervention."),
    D(9, "Trainees — authorisations",
      "Trainees are not authorised to carry out an electrical lock-off alone: "
      "they must be accompanied by an authorised technician."),
    D(10, "Bearings P-42 — greasing",
      "The bearings of pump P-42 are greased every 2000 hours with a lithium "
      "NLGI 2 grease."),
    D(11, "Sulzer supply lead times",
      "The supply lead time for Sulzer parts for the P-42 is three weeks as "
      "standard, one week under contractual urgency."),
    D(12, "Pressure test after intervention",
      "After reassembling a seal, a pressure test at 1.5 times the service "
      "pressure validates the sealing before restarting."),
    D(13, "Vibration P-42 — thresholds",
      "Vibration monitoring of the P-42 raises an alert beyond 7.1 mm/s of RMS "
      "velocity."),
    D(14, "Technician Karim — authorisations",
      "Technician Karim holds a B2V authorisation for electrical lock-offs and "
      "is certified on Sulzer centrifugal pumps."),
    D(15, "General supplier manual",
      "General directory of the site's suppliers: contact details, framework "
      "contracts and general purchasing conditions, across all equipment."),
    D(16, "Intervention schedule June 2026",
      "The June 2026 schedule lists the interventions planned on the critical "
      "pumps and valves, with the technicians assigned."),
]


# ---------------------------------------------------------------------------
# The multi-turn conversation (Karim and the RAG). Each user turn carries:
#   - 'texte'    : what Karim actually says, with its anaphora or ellipsis;
#   - 'autonome' : the self-contained reference query (the ground truth);
#   - 'attendus' : the fragments that query should retrieve;
#   - 'type'     : autonome | anaphore | ellipse | suivi | chitchat | followup.
#
# THE WORDING OF THE USER TURNS IS THE MECHANISM. The anaphoric turns must
# contain a pronoun from chatkit._PRONOUNS; the elliptical ones must open with
# "and " or be two words or fewer. If neither fires, the reformulation leaves
# the turn untouched and Lab 30-2 reports a gain of zero — with no error.
# Lab 30-1 prints, turn by turn, what the raw retrieval finds; run it after any
# edit here. The French baseline for the mean gain is +25%.
# ---------------------------------------------------------------------------
def U(texte, autonome, attendus, type_):
    return {"role": "user", "texte": texte, "autonome": autonome,
            "attendus": attendus, "type": type_}


def A(texte):
    return {"role": "assistant", "texte": texte}


CONVERSATION = [
    U("Who is the supplier of pump P-42?",
      "Who is the supplier of pump P-42?",
      ["D01"], "autonome"),
    A("Pump P-42 is supplied by Sulzer, contract MAINT-2026-001."),

    # NOTE: "seen any trouble" rather than "had any failures". The document D02
    # contains "had", so the raw anaphoric query would already find it and the
    # turn would show no gain from reformulation — which is precisely what this
    # turn exists to demonstrate. Check Lab 30-2 if you reword it.
    U("Have we seen any trouble on it this month?",
      "Failure reports for pump P-42 in June 2026",
      ["D02"], "anaphore"),
    A("Yes, two seal leaks in June 2026."),

    U("And the lead time for the parts?",
      "Supply lead time for the parts of pump P-42 (Sulzer)",
      ["D11"], "ellipse"),
    A("Three weeks as standard, one week under contractual urgency."),

    U("How do we repair it, this leak?",
      "Procedure for repairing a seal leak on a pump",
      ["D07"], "anaphore"),
    A("Lock-off, drain, replace the seal, then a pressure test."),

    U("And for the trainees?",
      "Can trainees carry out an electrical lock-off?",
      ["D09"], "ellipse"),
    A("No, they must be accompanied by an authorised technician."),

    U("Thanks!",
      "Thanks!",
      [], "chitchat"),
    A("My pleasure."),

    U("Can you rephrase the last step?",
      "Rephrase the last step of the repair procedure",
      [], "followup"),
    A("The last step is the pressure test at 1.5 times the service pressure."),

    U("What is the electrical lock-off procedure, by the way?",
      "What is the electrical lock-off procedure?",
      ["D08"], "autonome"),
    A("Five steps: separation, locking, identification, verification of the "
      "absence of voltage, earthing."),

    U("And on the V-7, any trouble?",
      "Failure history of valve V-7",
      ["D04"], "suivi"),
    A("It jammed in the closed position in June 2026, actuator replaced."),

    U("Who supplies it?",
      "Who is the supplier of valve V-7?",
      ["D03"], "anaphore"),
    A("Valve V-7 is supplied by KSB."),
]


# ---------------------------------------------------------------------------
# A long conversation (50 turns) on a single P-42 intervention. User turns and
# answers alternate. The aim is to test the robustness of the memory:
# information laid down early (the supplier, the contract, the technician) is
# asked about again by anaphora very late (turns 42, 47...).
#
# THE STATE EXTRACTORS OF chatkit MATCH ON THIS WORDING. The opening block sets
# the state — equipment, problem, actors — and the late turns interrogate it.
# Both sides must stay in step, and the extractors are regexes over the French
# vocabulary in the original: "cause probable est", "technicien Karim". They are
# translated alongside this block.
# ---------------------------------------------------------------------------
def build_long_conversation():
    conv = []
    # The opening block: it lays down the state (equipment, problem, actors).
    ouverture = [
        ("Let us open the intervention on pump P-42.",
         "Intervention recorded on pump P-42."),
        ("The problem is a seal leak.",
         "Noted: seal leak on P-42."),
        ("The supplier is Sulzer, is it not?",
         "Yes, supplier Sulzer, contract MAINT-2026-001."),
        ("Karim takes the intervention.",
         "Technician Karim assigned to the intervention."),
        ("The probable cause is a worn gasket.",
         "Cause retained: worn gasket."),
        ("The solution: replace the gasket, then a pressure test.",
         "Solution planned: gasket replacement plus pressure test."),
        ("Schedule the intervention for 2026-06-25.",
         "Intervention scheduled for 2026-06-25."),
    ]
    for u, a in ouverture:
        conv.append({"role": "user", "texte": u})
        conv.append({"role": "assistant", "texte": a})

    # Filling: varied technical exchanges, as noise, to lengthen the thread.
    bruit = [
        ("What is the vibration threshold?", "An alert beyond 7.1 mm/s."),
        ("And the greasing of the bearings?", "Every 2000 hours, NLGI 2 grease."),
        ("The pressure test, at what level?", "1.5 times the service pressure."),
        ("The lock-off, how many steps?", "Five regulatory steps."),
        ("Is Karim authorised?", "Yes, a B2V authorisation."),
        ("Is cavitation involved?", "No, this is a seal leak."),
        ("Sulzer parts lead time?", "Three weeks standard, one in urgency."),
        ("Do we note that in the schedule?", "Added to the June 2026 schedule."),
    ]
    i = 0
    while len(conv) < 2 * 40:  # up to about 40 user turns
        u, a = bruit[i % len(bruit)]
        conv.append({"role": "user", "texte": u})
        conv.append({"role": "assistant", "texte": a})
        i += 1

    # Late robustness turns: anaphora reaching back to the state set at the start.
    tardifs = [
        ("And its supplier, who was that again?", "fournisseur"),   # -> Sulzer
        ("What was the intervention date?", "date"),                # -> 2026-06-25
        ("Who was taking the intervention, again?", "technicien"),  # -> Karim
        ("And the contract, its number?", "contrat"),               # -> MAINT-2026-001
        ("Which equipment were we talking about?", "equipement"),   # -> pump P-42
    ]
    for u, cible in tardifs:
        conv.append({"role": "user", "texte": u, "cible_etat": cible})
        conv.append({"role": "assistant", "texte": "(answered from memory)"})
    return conv


def main():
    (CORPUS / "documents.json").write_text(
        json.dumps(DOCUMENTS, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "conversation.json").write_text(
        json.dumps(CONVERSATION, ensure_ascii=False, indent=2), encoding="utf-8")
    longue = build_long_conversation()
    (CORPUS / "conversation_longue.json").write_text(
        json.dumps(longue, ensure_ascii=False, indent=2), encoding="utf-8")

    tours_user = sum(1 for m in CONVERSATION if m["role"] == "user")
    print("Chapter 30 corpus generated in:", CORPUS)
    print(f"  - documents.json           : {len(DOCUMENTS)} fragments")
    print(f"  - conversation.json        : {tours_user} user turns "
          f"(anaphora, ellipsis, follow-on, chitchat, follow-up)")
    print(f"  - conversation_longue.json : {sum(1 for m in longue if m['role']=='user')} "
          f"user turns (memory robustness)")


if __name__ == "__main__":
    main()
