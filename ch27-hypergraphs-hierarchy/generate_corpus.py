# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 27
(beyond the flat graph: hypergraphs and hierarchical navigation).

The corpus is designed to make the chapter's TWO blind spots visible:

  - THE THEMATIC BLIND SPOT. Six quality procedures take part in the same
    crossing theme ("business continuity", "regulatory compliance") WITHOUT
    sharing entities two by two. A pairwise graph cannot express that; a
    hyperedge can.

  - THE HIERARCHICAL BLIND SPOT. A turbine manual with nested headings, where
    the position in the tree is itself information — which a flat index crushes.

And it supplies what is needed to evaluate the MULTI-RESOLUTION engine (Lab 27-5)
and the ablation study (Lab 27-6).

Written to corpus/:
  - procedures.json  : 6 procedures plus the ground-truth crossing themes
  - turbine.md       : hierarchical documentation, heading levels 1 to 3
  - inspections.json : 30 short inspection reports, labelled by domain
  - questions.json   : 50 questions annotated by expected engine

TWO THINGS MUST SURVIVE ANY EDIT.
  1. The procedures must keep sharing NO entity two by two while belonging to
     the same theme. That gap is what makes the hypergraph necessary.
  2. The wording of the 50 questions is calibrated on the router word lists of
     multikit._WORDS.

Lab 27-5 measures the second: routing accuracy plus a confusion matrix. The
French baseline is 41/50.

Run before the labs: python generate_corpus.py
No API key, no network.
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# ===========================================================================
# 1) Documentation quality — the angle mort THEMATIC
# Six procedures. The themes transversaux the regroupent WITHOUT that elles
# partagent of entities deux to deux.
# ===========================================================================
PROCEDURES = [
    {"id": "P-SEC-001", "title": "Cybersecurity of the industrial network",
     "content": "Procedure P-SEC-001 governs the protection of the supervision "
                "network: segmentation, firewall, management of remote access. It "
                "aims to guarantee the availability of the control systems.",
     "entities": ["network", "firewall", "remote access"]},
    {"id": "P-SEC-002", "title": "Physical security of the installations",
     "content": "Procedure P-SEC-002 defines access control to sensitive zones: "
                "badges, patrols, video surveillance. It answers the regulatory "
                "requirements for classified sites.",
     "entities": ["access control", "badge", "video surveillance"]},
    {"id": "P-MNT-001", "title": "Preventive maintenance of the equipment",
     "content": "Procedure P-MNT-001 plans the preventive interventions "
                "(lubrication, vibration checks, replacement of wear parts) so as "
                "to avoid unplanned production stoppages.",
     "entities": ["lubrication", "vibration check", "wear part"]},
    {"id": "P-MNT-002", "title": "Corrective maintenance and return to service",
     "content": "Procedure P-MNT-002 describes fault diagnosis, repair and "
                "requalification before returning failed equipment to service.",
     "entities": ["diagnosis", "repair", "requalification"]},
    {"id": "P-SUR-001", "title": "Process safety",
     "content": "Procedure P-SUR-001 deals with the control of process risks: "
                "relief valves, alarm thresholds, safe-state scenarios. It "
                "contributes to maintaining activity in degraded conditions.",
     "entities": ["relief valve", "alarm", "safe state"]},
    {"id": "P-SUR-002", "title": "Fire safety",
     "content": "Procedure P-SUR-002 organises the prevention of and response to "
                "fire: detection, smoke extraction, evacuation drills. It answers "
                "the regulatory obligations.",
     "entities": ["fire detection", "smoke extraction", "evacuation"]},
]

# The crossing themes (the ground truth): the expected hyperedges.
#
# THE POINT OF THE CHAPTER lives here: these procedures share NO entity two by
# two, yet they belong to the same theme. A pairwise graph cannot express that;
# a hyperedge can. If a translation makes two procedures share vocabulary, the
# hypergraph stops being necessary and Lab 27-1 loses its demonstration.
GROUND_TRUTH_THEMES = {
    "Business continuity": ["P-SEC-001", "P-MNT-001", "P-SUR-001"],
    "Regulatory compliance": ["P-SEC-002", "P-SUR-002"],
}


# ===========================================================================
# 2) Turbine documentation — the HIERARCHICAL blind spot
# A Markdown file with nested headings (levels 1 to 3). The position in the
# tree is itself a piece of retrieval information.
# ===========================================================================
TURBINE_MD = """# Technical manual — Gas turbine TG-90

The TG-90 gas turbine converts the energy of the combustion gases into
mechanical energy. It consists of a compressor, a combustion chamber and an
expansion section. This manual describes each sub-assembly.

## Compressor

The compressor raises the pressure of the intake air before combustion. It is
of the axial, multi-stage type. The overall efficiency depends on the condition
of the stages.

### Stage 3

Stage 3 of the compressor provides an intermediate compression ratio. It
comprises moving blades and a support bearing.

#### Blade 7

Blade 7 of stage 3 is subject to the highest thermal stresses. Its maximum
permissible temperature is 540 degrees C. Beyond that, creep reduces its
service life.

#### Bearing

The bearing of stage 3 carries the radial loads. Its lubrication is provided by
the main oil circuit; the oil temperature must not exceed 110 degrees C.

## Combustion chamber

The combustion chamber mixes the compressed air with the fuel and maintains a
stable flame. The walls are cooled by an air film. The outlet temperature
reaches 1200 degrees C at nominal load.

## Expansion section

The expansion section extracts the energy of the hot gases through several
turbine stages. The first expansion stage receives the hottest gases and uses
cooled vanes.
"""


# ===========================================================================
# 3) Inspection reports — for the clustering (Lab 27-2) and the ablation (27-6)
# 30 short reports, labelled by domain: the ground truth of the clustering.
# ===========================================================================
def _reports():
    # Each report shares a domain vocabulary, as real reports do, which makes the
    # clustering separable without cheating: the thematic signal really is in the
    # text. Keep that vocabulary consistent within a domain if you edit these.
    templates = {
        "maintenance": [
            "Preventive maintenance: vibration check on the bearing, amplitude within thresholds, lubrication verified.",
            "Preventive maintenance: greasing of the roller bearings carried out to plan, bearing wear checked.",
            "Corrective maintenance: replacement of a wear part on the conveyor, lubrication redone, stoppage avoided.",
            "Preventive maintenance: oil analysis on the bearing, wear particles detected, vibration monitoring reinforced.",
            "Corrective maintenance: shaft alignment verified after the intervention, vibration check compliant.",
            "Preventive maintenance: thermographic inspection of the roller bearings, hot spot on one bearing, lubrication to review.",
        ],
        "security": [
            "Physical security: audit of badge access control, two expired badges deactivated, video surveillance verified.",
            "Network security: test of the video surveillance and access control, camera in zone 4 out of service, badge corrected.",
            "Cybersecurity: review of remote access to the supervision network, one dormant account removed, firewall verified.",
            "Physical security: intrusion drill, access control held, video surveillance and badges operational.",
            "Cybersecurity: update of the supervision firewall, network segmentation and remote access controlled.",
            "Physical security: check on badges and access, one blocked access door corrected, video surveillance active.",
        ],
        "quality": [
            "Quality: documentary review of the procedures, three procedures to update, recording of the checks verified.",
            "Quality: product non-conformity detected on one batch, traced and isolated, quality record updated.",
            "Quality: internal audit of the procedures, minor deviation on the recording of the checks, documentary conformity.",
            "Quality: calibration of the measuring instruments, certificates up to date, recording of the checks compliant.",
            "Quality: review of customer complaints, a stable trend, handling procedures compliant with the standard.",
            "Quality: verification of the labelling and records, compliant with the documentary standard.",
        ],
        "environment": [
            "Environment: measurement of atmospheric discharges, below the regulatory thresholds, discharges and emissions traced.",
            "Environment: check on the retention bunds and storage tanks, sealing verified, discharge risk controlled.",
            "Environment: monitoring of water consumption and discharges, a deviation to analyse, environmental measurements traced.",
            "Environment: management of hazardous waste, consignment notes compliant, storage and discharges controlled.",
            "Environment: measurement of noise and emissions at the site boundary, discharges within the regulatory thresholds.",
            "Environment: inspection of the storage tanks, incipient corrosion noted, discharge risk monitored.",
        ],
        "process_safety": [
            "Process safety: test of the relief valves, setting compliant, alarm thresholds and safe state verified.",
            "Process safety: verification of the process alarm thresholds and the relief valves, safe-state scenario compliant.",
            "Process safety: review of a safe-state scenario, relief valves and alarms tested, response time correct.",
            "Process safety: check on the gas detectors and the alarms, one drifting sensor recalibrated, safe state OK.",
            "Process safety: trial of the safe-state system and the relief valves, alarm thresholds compliant.",
            "Process safety: analysis of the safety barriers, one degraded barrier reported, relief valves and alarms verified.",
        ],
    }
    out, rid = [], 1
    for domain, texts in templates.items():
        for t in texts:
            out.append({"id": f"insp{rid:02d}", "domain": domain, "content": t})
            rid += 1
    return out


# ===========================================================================
# 4) The 50 questions annotated by expected engine (the test bench of Lab 27-5)
#    moteurs : vectoriel | graphe | hypergraphe | hierarchie | mixte
# ===========================================================================
QUESTIONS = [
    # THE WORDING OF THESE 50 IS CALIBRATED on the router word lists of
    # multikit._WORDS. Lab 27-5 prints the routing accuracy and a confusion
    # matrix: run it after any edit here. The French baseline is 41/50.

    # --- factual -> vector (10) ---
    {"q": "What is the maximum permissible temperature of blade 7?", "engine": "vector"},
    {"q": "What temperature must the bearing oil not exceed?", "engine": "vector"},
    {"q": "What is the outlet temperature of the combustion chamber?", "engine": "vector"},
    {"q": "What does procedure P-SEC-001 aim at?", "engine": "vector"},
    {"q": "What type of compressor is fitted to the TG-90 turbine?", "engine": "vector"},
    {"q": "What does procedure P-SEC-002 define?", "engine": "vector"},
    {"q": "Which circuit lubricates the bearing of stage 3?", "engine": "vector"},
    {"q": "Which procedure deals with the control of process risks?", "engine": "vector"},
    {"q": "What phenomenon reduces the life of the blade beyond 540 degrees C?", "engine": "vector"},
    {"q": "Which walls are cooled by an air film?", "engine": "vector"},

    # --- relational -> graph (10) ---
    {"q": "Which components depend on the compressor?", "engine": "graph"},
    {"q": "Does blade 7 belong to stage 3?", "engine": "graph"},
    {"q": "Which sub-assembly contains the support bearing?", "engine": "graph"},
    {"q": "Which elements compose stage 3?", "engine": "graph"},
    {"q": "Does the bearing depend on the main oil circuit?", "engine": "graph"},
    {"q": "What are the direct sub-assemblies of the TG-90 turbine?", "engine": "graph"},
    {"q": "Is stage 3 linked to the compressor?", "engine": "graph"},
    {"q": "Which part bears the thermal stresses of stage 3?", "engine": "graph"},
    {"q": "Which components are downstream of the combustion chamber?", "engine": "graph"},
    {"q": "Does the first expansion stage depend on the combustion chamber?", "engine": "graph"},

    # --- thematic -> hypergraph (10) ---
    {"q": "Which procedures participate in business continuity?", "engine": "hypergraph"},
    {"q": "Which procedures come under regulatory compliance?", "engine": "hypergraph"},
    {"q": "Which documents deal with security in the broad sense?", "engine": "hypergraph"},
    {"q": "Which procedures contribute to maintaining activity?", "engine": "hypergraph"},
    {"q": "Which inspection reports come under the maintenance theme?", "engine": "hypergraph"},
    {"q": "Which procedures share an objective of availability?", "engine": "hypergraph"},
    {"q": "Which documents deal with industrial cybersecurity?", "engine": "hypergraph"},
    {"q": "Which crossing themes structure the quality documentation?", "engine": "hypergraph"},
    {"q": "Which inspections come under the process safety theme?", "engine": "hypergraph"},
    {"q": "Which procedures converge on the regulation?", "engine": "hypergraph"},

    # --- navigation -> hierarchy (10) ---
    {"q": "Describe the general operation of the TG-90 turbine.", "engine": "hierarchy"},
    {"q": "What are the main parts of the turbine?", "engine": "hierarchy"},
    {"q": "Give a synthesis of the compressor section.", "engine": "hierarchy"},
    {"q": "What does the chapter on the combustion chamber contain?", "engine": "hierarchy"},
    {"q": "Present the overall architecture of the manual.", "engine": "hierarchy"},
    {"q": "Summarise the expansion section.", "engine": "hierarchy"},
    {"q": "Which sub-assemblies are described in the manual?", "engine": "hierarchy"},
    {"q": "Give an overview of the compressor and its stages.", "engine": "hierarchy"},
    {"q": "What is the general structure of the turbine documentation?", "engine": "hierarchy"},
    {"q": "Give an overall summary of the turbine manual.", "engine": "hierarchy"},

    # --- mixed -> mixed (10) ---
    {"q": "Which safety procedures concern interventions on the equipment, and which come under business continuity?", "engine": "mixed"},
    {"q": "Describe stage 3 and list the components it depends on.", "engine": "mixed"},
    {"q": "Which themes group the procedures linked to maintenance, and which components does preventive maintenance monitor?", "engine": "mixed"},
    {"q": "Summarise the compressor, then give the maximum temperature of blade 7.", "engine": "mixed"},
    {"q": "Which inspections come under security, and where do they sit in the documentary hierarchy?", "engine": "mixed"},
    {"q": "Which components depend on the compressor, and which maintenance theme do they attach to?", "engine": "mixed"},
    {"q": "Give an overview of the turbine and detail the bearing of stage 3.", "engine": "mixed"},
    {"q": "Which procedures share the availability theme, and which components do they cover?", "engine": "mixed"},
    {"q": "Describe the expansion section and list the elements downstream of the combustion chamber.", "engine": "mixed"},
    {"q": "Present the structure of the manual and say which components depend on the compressor.", "engine": "mixed"},
]


# ===========================================================================
# 5) The cost model (Lab 27-7) — relative costs per engine, in arbitrary units,
# consistent with the "cost of indexing" table of the chapter.
# ===========================================================================
COUT = {
    "indexation": {  # cost relatif of construction of each representation
        "vector": 1.0,
        "graph": 3.0,
        "hypergraph": 6.0,        # double extraction (themes + entities)
        "hierarchy": 0.5,         # often already in the titles
    },
    "par_requete": {  # cost relatif of a query on each moteur
        "vector": 1.0,
        "graph": 1.5,
        "hypergraph": 2.0,
        "hierarchy": 1.2,
        "mixed": 3.0,
    },
    "latence_ms": {   # latency simulated by moteur
        "vector": 8, "graph": 20, "hypergraph": 25, "hierarchy": 12, "mixed": 40,
    },
}


def main():
    (CORPUS / "procedures.json").write_text(
        json.dumps({"procedures": PROCEDURES, "themes": GROUND_TRUTH_THEMES},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "turbine.md").write_text(TURBINE_MD, encoding="utf-8")
    (CORPUS / "inspections.json").write_text(
        json.dumps({"reports": _reports()}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (CORPUS / "questions.json").write_text(
        json.dumps({"questions": QUESTIONS}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (CORPUS / "cost.json").write_text(
        json.dumps(COUT, ensure_ascii=False, indent=2), encoding="utf-8")

    rapports = _reports()
    par_moteur = {}
    for q in QUESTIONS:
        par_moteur[q["engine"]] = par_moteur.get(q["engine"], 0) + 1

    print("Chapter 27 corpus written to corpus/")
    print(f"  - procedures.json   : {len(PROCEDURES)} procedures, "
          f"{len(GROUND_TRUTH_THEMES)} crossing themes (ground truth)")
    print("  - turbine.md        : hierarchical documentation (heading levels 1-3)")
    print(f"  - inspections.json  : {len(rapports)} inspection reports "
          f"({len(set(r['domain'] for r in rapports))} domains)")
    print(f"  - questions.json    : {len(QUESTIONS)} annotated questions")
    print("    per engine:", ", ".join(f"{k}={v}" for k, v in sorted(par_moteur.items())))
    print("  - cost.json         : the cost model (indexing, query, latency)")
    print("\nTwo blind spots tooled up: THEMATIC (procedures and crossing themes)")
    print("and HIERARCHICAL (turbine -> compressor -> stage -> blade).")


if __name__ == "__main__":
    main()
