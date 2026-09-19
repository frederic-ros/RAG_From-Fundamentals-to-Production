# -*- coding: utf-8 -*-
"""
generate_corpus.py — generates the Chapter 28 corpus.

Written to corpus/:
  - failure_taxonomy.json     : a taxonomy of failure modes, with synonyms
  - maintenance_ontology.json : a meta-model (classes, relations, axioms)
  - reports.json              : 25 maintenance reports in LOCAL vocabulary
  - queries.json              : 10 queries, 5 standard and 5 business

THE DESIGN OF THIS CORPUS IS THE DEMONSTRATION. The reports never use the
canonical labels of the taxonomy; they use the vocabulary technicians actually
write, which the taxonomy records as synonyms. A query on "cavitation" therefore
returns nothing, because the reports speak of "hydrodynamic erosion". Without
expansion the query fails; with the taxonomic guardrail it succeeds.

Two properties must survive any edit:
  1. The canonical labels must stay ABSENT from the reports (the one deliberate
     exception is report 1, which the ontology needs).
  2. The synonym lists must match the wording of the reports.

Lab 28-1 measures both, as a recall with and without expansion. The French
baseline on the business terms is 40% without against 73% with.

Run before the labs: python generate_corpus.py
No API key, no network.
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1) Taxonomy of pannes : tree is-a + synonymes business
# Point key educational : "cavitation" (terme technician) not appears NEVER
# in the reports, which speak of "hydrodynamic erosion". Without expansion,
# the query "cavitation" returns zero fragments.
# ---------------------------------------------------------------------------
TAXONOMY = {
    # THE SYNONYM LISTS ARE THE MECHANISM of the taxonomic guardrail. The
    # expansion of Lab 28-1 maps a free-text term onto its canonical node
    # through them. Left in French against English reports they match nothing,
    # the expansion returns the query unchanged, and the lab reports that the
    # taxonomy brings no gain — with no error.
    "Failure": {
        "type": "class",
        "subclasses": ["Mechanical failure", "Hydraulic failure", "Electrical failure"],
        "synonyms": ["breakdown", "anomaly", "malfunction"],
    },
    "Mechanical failure": {
        "type": "subclass",
        "subclasses": ["Bearing wear", "Misalignment", "Unbalance"],
        "synonyms": ["mechanical damage", "mechanical defect"],
    },
    "Hydraulic failure": {
        "type": "subclass",
        "subclasses": ["Cavitation", "Leak", "Water hammer"],
        "synonyms": ["hydraulic problem", "circuit defect"],
    },
    "Electrical failure": {
        "type": "subclass",
        "subclasses": ["Motor overheating", "Short circuit"],
        "synonyms": ["electrical defect"],
    },
    "Cavitation": {
        "type": "leaf",
        "synonyms": [
            "hydrodynamic erosion",
            "local hydrodynamic erosion",
            "bubble implosion",
            "abnormal pump casing acoustics",
            "pitting on the vanes",
        ],
    },
    "Leak": {
        "type": "leaf",
        "synonyms": ["fluid loss", "sealing defect", "weeping"],
    },
    "Water hammer": {
        "type": "leaf",
        "synonyms": ["pressure surge wave", "pressure shock"],
    },
    "Bearing wear": {
        "type": "leaf",
        "synonyms": ["bearing degradation", "race spalling", "race wear"],
    },
    "Misalignment": {
        "type": "leaf",
        "synonyms": ["alignment defect", "shaft offset"],
    },
    "Unbalance": {
        "type": "leaf",
        "synonyms": ["rotor imbalance", "balancing defect"],
    },
    "Motor overheating": {
        "type": "leaf",
        "synonyms": ["winding heating", "stator temperature rise"],
    },
    "Short circuit": {
        "type": "leaf",
        "synonyms": ["electrical arcing", "insulation fault"],
    },
}


# ---------------------------------------------------------------------------
# 2) The maintenance ontology: a META-MODEL, not data
# ---------------------------------------------------------------------------
ONTOLOGY = {
    "classes": [
        "Pump", "HydraulicCircuit", "FailureMode",
        "Procedure", "Technician", "Supplier", "Component",
    ],
    "relations": [
        {"source": "Pump", "target": "HydraulicCircuit", "label": "fed_by"},
        {"source": "Pump", "target": "FailureMode", "label": "carries_risk_of"},
        {"source": "Pump", "target": "Component", "label": "comprises"},
        {"source": "Component", "target": "Supplier", "label": "supplied_by"},
        {"source": "Procedure", "target": "Pump", "label": "concerns"},
        {"source": "Procedure", "target": "Procedure", "label": "must_precede"},
        {"source": "Technician", "target": "Procedure", "label": "responsible_for"},
    ],
    "axioms": [
        "Every FailureMode must be linked to at least one Pump.",
        "A safety Procedure must_precede any intervention Procedure.",
        "A Pump is fed_by exactly one HydraulicCircuit.",
    ],
}


# ---------------------------------------------------------------------------
# 3) Maintenance reports — LOCAL terms only, never the canonical labels
#
# THIS IS THE HEART OF THE DEMONSTRATION. The reports are written in the
# vocabulary technicians actually use (the synonyms), NOT in the canonical
# vocabulary of the taxonomy. A query using the canonical term therefore finds
# nothing without expansion. If a translation slips a canonical label into a
# report, that query starts succeeding without the taxonomy and Lab 28-1 loses
# its point. The one deliberate exception is report 1, which names "cavitation"
# because the ontology needs the carries_risk_of relation.
# ---------------------------------------------------------------------------
def _frag(i, title, text, failures):
    return {"id": f"R{i:02d}", "title": title, "text": text, "failures": failures}


REPORTS = [
    _frag(1, "Pump P-42 — quarterly inspection",
          "Centrifugal pump P-42 is fed by the primary circuit. Hydrodynamic "
          "erosion has been found on the vanes, with characteristic pitting. "
          "Pump P-42 carries the risk of cavitation on this circuit.",
          ["Cavitation"]),
    _frag(2, "Secondary circuit — pressure reading",
          "The secondary hydraulic circuit shows a pressure surge wave on rapid "
          "valve closures. A pressure shock phenomenon to monitor.",
          ["Water hammer"]),
    _frag(3, "Pump P-17 — vibration analysis",
          "The vibration analysis reveals a marked rotor imbalance on P-17. A "
          "balancing defect is suspected after the last reassembly.",
          ["Unbalance"]),
    _frag(4, "Motor bearing M-3 — thermography",
          "Thermography of bearing M-3 shows bearing degradation with race "
          "spalling. Replacement of the roller bearing recommended.",
          ["Bearing wear"]),
    _frag(5, "Coupling P-42/M-1 — laser check",
          "The laser check on the coupling reveals a residual alignment defect. "
          "Shaft offset above the manufacturer's tolerance.",
          ["Misalignment"]),
    _frag(6, "Mechanical seal P-08 — leak",
          "Weeping found at the mechanical seal of P-08. A progressive sealing "
          "defect, fluid loss estimated at 2 L/h.",
          ["Leak"]),
    _frag(7, "Motor M-7 — electrical reading",
          "Winding heating observed on motor M-7 at nominal load. Stator "
          "temperature rise beyond threshold B.",
          ["Motor overheating"]),
    _frag(8, "Electrical cabinet A-2 — insulation diagnosis",
          "The insulation diagnosis of cabinet A-2 reports an insulation fault "
          "on the pump outgoing way. Risk of electrical arcing.",
          ["Short circuit"]),
    _frag(9, "Pump P-42 — supplier history",
          "Pump P-42 comprises an impeller supplied by Sulzer. The seal "
          "component is supplied by EagleBurgmann.",
          []),
    _frag(10, "Lock-off procedure before intervention",
          "The electrical lock-off procedure must precede any intervention "
          "procedure on a live pump.",
          []),
    _frag(11, "Pump P-19 — erosion confirmed",
          "Endoscopic inspection of P-19: bubble implosion at the impeller "
          "inlet, local hydrodynamic erosion confirmed. Insufficient NPSH "
          "suspected.",
          ["Cavitation"]),
    _frag(12, "Primary circuit — surge",
          "A pressure shock has damaged a bend in the primary circuit. Fitting "
          "of a surge arrester recommended.",
          ["Water hammer"]),
    _frag(13, "Pump P-31 — bearing wear",
          "Advanced race wear on the coupling-side bearing of P-31. Radial "
          "clearance out of tolerance.",
          ["Bearing wear"]),
    _frag(14, "Fan V-5 — imbalance",
          "Rotor imbalance detected on fan V-5 after asymmetric fouling of the "
          "blades.",
          ["Unbalance"]),
    _frag(15, "Pump P-22 — misalignment",
          "Shaft offset found between P-22 and its motor. Alignment shims to be "
          "reworked.",
          ["Misalignment"]),
    _frag(16, "Valve VN-9 — stem leak",
          "Fluid loss at the gland of valve VN-9. A sealing defect on the stem.",
          ["Leak"]),
    _frag(17, "Motor M-12 — overheating",
          "Stator temperature rise on M-12 during frequent starts. Cyclic "
          "winding heating.",
          ["Motor overheating"]),
    _frag(18, "Switchboard TGBT — short circuit",
          "Electrical arcing on the TGBT busbar. Insulation fault traced to the "
          "outgoing way of motor M-12.",
          ["Short circuit"]),
    _frag(19, "Pump P-05 — impeller erosion",
          "Pitting on the vanes of the P-05 impeller. Hydrodynamic erosion "
          "consistent with operation at the NPSH limit.",
          ["Cavitation"]),
    _frag(20, "Pump intervention procedure",
          "The intervention procedure concerns pump P-42, for dismantling the "
          "volute. Technician Julien is responsible for the intervention "
          "procedure.",
          []),
    _frag(21, "Cooling circuit — surge wave",
          "A pressure surge wave measured on the cooling circuit during an "
          "emergency pump stop.",
          ["Water hammer"]),
    _frag(22, "Bearing P-08 — spalling",
          "Outer race spalling on the roller bearing of P-08. Bearing "
          "degradation in its terminal phase.",
          ["Bearing wear"]),
    _frag(23, "Pump P-42 — circuit relation",
          "Pump P-42 is fed by the primary cooling circuit, itself connected to "
          "heat exchanger E-1.",
          []),
    _frag(24, "Compressor C-3 — misalignment",
          "Alignment defect between compressor C-3 and its turbine. Vibration at "
          "the rotation frequency.",
          ["Misalignment"]),
    _frag(25, "Pump P-50 — sealing",
          "Progressive weeping on P-50. The sealing defect on the seal requires "
          "a planned shutdown.",
          ["Leak"]),
]


# ---------------------------------------------------------------------------
# 4) Queries — 5 standard terms (present) plus 5 local business terms (absent)
# The "expected_failures" field gives the ground truth, to measure recall.
#
# Q1-Q5 use SYNONYMS, which appear in the reports: they work without expansion.
# Q6-Q10 use the CANONICAL terms, which do NOT appear: they fail without it.
# That contrast is what Lab 28-1 measures. The French baseline for the business
# terms is a recall of 40% without expansion against 73% with.
# ---------------------------------------------------------------------------
QUERIES = [
    # --- 5 standard terms (these already work without expansion) --------------
    {"id": "Q1", "text": "hydrodynamic erosion", "type": "standard",
     "expected_failures": ["Cavitation"]},
    {"id": "Q2", "text": "pressure surge wave", "type": "standard",
     "expected_failures": ["Water hammer"]},
    {"id": "Q3", "text": "rotor imbalance", "type": "standard",
     "expected_failures": ["Unbalance"]},
    {"id": "Q4", "text": "sealing defect", "type": "standard",
     "expected_failures": ["Leak"]},
    {"id": "Q5", "text": "winding heating", "type": "standard",
     "expected_failures": ["Motor overheating"]},
    # --- 5 local business terms (ABSENT from the reports: failure without expansion)
    {"id": "Q6", "text": "cavitation", "type": "business",
     "expected_failures": ["Cavitation"]},
    {"id": "Q7", "text": "water hammer", "type": "business",
     "expected_failures": ["Water hammer"]},
    {"id": "Q8", "text": "unbalance", "type": "business",
     "expected_failures": ["Unbalance"]},
    {"id": "Q9", "text": "bearing wear", "type": "business",
     "expected_failures": ["Bearing wear"]},
    {"id": "Q10", "text": "short circuit", "type": "business",
     "expected_failures": ["Short circuit"]},
]


def main():
    (CORPUS / "failure_taxonomy.json").write_text(
        json.dumps(TAXONOMY, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "maintenance_ontology.json").write_text(
        json.dumps(ONTOLOGY, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "maintenance_reports.json").write_text(
        json.dumps(REPORTS, ensure_ascii=False, indent=2), encoding="utf-8")
    (CORPUS / "queries.json").write_text(
        json.dumps(QUERIES, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Chapter 28 corpus generated in:", CORPUS)
    print(f"  - failure_taxonomy.json      : {len(TAXONOMY)} concepts")
    print(f"  - maintenance_ontology.json : {len(ONTOLOGY['classes'])} classes, "
          f"{len(ONTOLOGY['relations'])} relations, {len(ONTOLOGY['axioms'])} axioms")
    print(f"  - maintenance_reports.json  : {len(REPORTS)} reports")
    print(f"  - queries.json               : {len(QUERIES)} queries "
          f"(5 standard + 5 business)")


if __name__ == "__main__":
    main()
