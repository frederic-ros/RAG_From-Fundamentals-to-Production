# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 26 (GraphRAG in practice).

A deterministic industrial corpus, designed to make VISIBLE the frontier between
what a vector search can do and what a graph can do:

  - A CHAIN OF DEPENDENCIES (Labs 26-1 and 26-4): pump P-42 feeds heat exchanger
    E-7, which feeds line L-3, which manufactures product X. NO document holds
    the complete chain: it must be REBUILT by following the relations. That is
    the heart of the demonstration — "the vector finds documents, the graph finds
    paths".

  - SUPPLIERS AND CONTRACTS (Lab 26-4): E-7 is manufactured by Rexel; Rexel is
    linked to contract 2024-07. Walking up from L-3 to the supplier takes several
    hops.

  - COMMUNITIES (Lab 26-3, the global search): the equipment groups into two
    zones (production, utilities). Aggregation questions ("which lines exist on
    the site?") call for a global search rather than a local one.

  - 25 QUESTIONS annotated by expected type (factual / relational / aggregation /
    supplier), to evaluate the router of Lab 26-5.

The reference graph (the "ground truth" of the relations) is also written out, so
the quality of the extraction can be measured.

TWO THINGS MUST SURVIVE ANY EDIT.
  1. The relation labels of EXPECTED_TRIPLES are matched literally by the
     extraction patterns of graphkit._PATTERNS.
  2. The wording of the 25 questions is calibrated on the router's word lists.

Both are measured: Lab 26-2 prints precision, recall and F1 of the extraction
(French baseline: 1.00 / 0.73 / 0.84), Lab 26-5 the routing accuracy (22/25).

Run before the labs: python generate_corpus.py
No API key, no network.
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1) The documents. Each document porte a or deux faits. AUCUN not contient
# the complete chain P-42 -> E-7 -> L-3 -> product X. That is the whole point.
# ---------------------------------------------------------------------------
DOCUMENTS = [
    # --- The utilities zone (upstream) ---
    {"id": "doc01", "zone": "utilities",
     "content": "Pump P-42 feeds heat exchanger E-7. The nominal pressure of P-42 "
                "is 3 bar. P-42 is installed in the utilities zone, level 0.",
     "source": "technical_manual_P42.pdf"},
    {"id": "doc02", "zone": "utilities",
     "content": "Heat exchanger E-7 feeds production line L-3. E-7 is manufactured "
                "by Rexel. Its maximum service temperature is 180 degrees C.",
     "source": "datasheet_E7.pdf"},
    {"id": "doc03", "zone": "production",
     "content": "Line L-3 manufactures product X. The maintenance of L-3 is carried "
                "out by team B. L-3 runs continuously, on three shifts.",
     "source": "maintenance_procedure_L3.pdf"},
    # --- Suppliers and contracts (upstream) ---
    {"id": "doc04", "zone": "utilities",
     "content": "The supplier Rexel is linked to contract 2024-07. That contract "
                "covers the supply and maintenance of the heat exchangers in the "
                "utilities zone.",
     "source": "contract_2024_07.pdf"},
    {"id": "doc05", "zone": "utilities",
     "content": "The parts for pump P-42 are supplied by Rexel under contract "
                "2024-07. Restocking lead time: six weeks.",
     "source": "parts_logistics.pdf"},
    # --- Procedures (aggregation and safety) ---
    {"id": "doc06", "zone": "production",
     "content": "The emergency stop procedure for L-3 requires the upstream "
                "equipment to be isolated first. Any work on L-3 requires a permit "
                "signed by team B.",
     "source": "safety_procedure_L3.pdf"},
    {"id": "doc07", "zone": "utilities",
     "content": "Procedure SE-12 describes the safe shutdown of pump P-42: cut the "
                "supply, purge, lock off. It replaces procedure SE-09 of 2022.",
     "source": "procedure_SE12.pdf"},
    {"id": "doc08", "zone": "production",
     "content": "An incident on L-3 in March was caused by overheating of E-7. The "
                "report recommends closer monitoring of the upstream temperature.",
     "source": "incident_report_march.pdf"},
    # --- Noise and distractors: close entities that are NOT connected ---
    {"id": "doc09", "zone": "production",
     "content": "Line L-5 manufactures product Y. It is independent of the utilities "
                "zone and has its own supply.",
     "source": "datasheet_L5.pdf"},
    {"id": "doc10", "zone": "utilities",
     "content": "Pump P-17 feeds buffer tank R-2. P-17 has no connection with line "
                "L-3. Nominal pressure: 2 bar.",
     "source": "datasheet_P17.pdf"},
]


# ---------------------------------------------------------------------------
# 2) The expected graph (the ground truth). Triples (subject, relation, object).
# Used to measure the quality of the extraction in Lab 26-2 and beyond.
#
# THE RELATION LABELS ARE MATCHED LITERALLY by the extraction patterns of
# graphkit._PATTERNS. The two must stay in step: a label changed on one side
# only makes the extraction score collapse without any error.
# ---------------------------------------------------------------------------
EXPECTED_TRIPLES = [
    ["P-42", "feeds", "E-7"],
    ["E-7", "feeds", "L-3"],
    ["L-3", "manufactures", "product X"],
    ["E-7", "manufactured_by", "Rexel"],
    ["Rexel", "linked_to", "contract 2024-07"],
    ["P-42", "parts_supplied_by", "Rexel"],
    ["L-3", "maintained_by", "team B"],
    ["P-42", "shutdown_by", "procedure SE-12"],
    ["procedure SE-12", "replaces", "procedure SE-09"],
    # Distractors (isolated zones), useful to check nothing is wrongly connected.
    ["L-5", "manufactures", "product Y"],
    ["P-17", "feeds", "R-2"],
]


# ---------------------------------------------------------------------------
# 3) The 25 questions, annotated by expected type. This is the test bench for
# the router (Lab 26-5). Each type calls for a different strategy.
# - factuelle : a seul saut, answer in a document -> vector-based
# - relationnelle: several sauts to suivre -> graph local / VectorCypher
# - supplier    : a multi-hop walk upstream -> VectorCypher
# - aggregation : "all the...", themes -> the global search
# ---------------------------------------------------------------------------
QUESTIONS = [
    # NOTE. Each question is calibrated on a branch of graphkit.routeur_complexite,
    # which decides from three word lists (relation, aggregation, supplier). Those
    # lists must match the wording here. Lab 26-5 prints the routing accuracy over
    # all 25: run it after any edit. The French baseline is 22/25.
    {"q": "What is the nominal pressure of P-42?", "type": "factual", "rep": "3 bar"},
    {"q": "What is the maximum service temperature of E-7?", "type": "factual", "rep": "180 degrees C"},
    {"q": "Who carries out the maintenance of L-3?", "type": "factual", "rep": "team B"},
    {"q": "Which procedure replaces SE-09 of 2022?", "type": "factual", "rep": "procedure SE-12"},
    {"q": "Where is pump P-42 installed?", "type": "factual", "rep": "the utilities zone"},

    {"q": "What does the line fed by P-42 manufacture?", "type": "relational", "rep": "product X"},
    {"q": "Which equipment depends on P-42?", "type": "relational", "rep": "E-7, L-3"},
    {"q": "Which product is at the end of the chain from P-42?", "type": "relational", "rep": "product X"},
    {"q": "Does line L-3 depend on P-42?", "type": "relational", "rep": "yes (P-42 -> E-7 -> L-3)"},
    {"q": "Which components lie between P-42 and product X?", "type": "relational", "rep": "E-7, L-3"},

    {"q": "Which supplier manufactures the exchanger fed by P-42?", "type": "supplier", "rep": "Rexel"},
    {"q": "Which supplier risks impacting production on L-3?", "type": "supplier", "rep": "Rexel"},
    {"q": "Which contract covers heat exchanger E-7?", "type": "supplier", "rep": "contract 2024-07"},
    {"q": "Which suppliers are involved in the chain of P-42?", "type": "supplier", "rep": "Rexel"},
    {"q": "Which contract is linked to the parts of P-42?", "type": "supplier", "rep": "contract 2024-07"},

    {"q": "What are the main critical points of the network?", "type": "aggregation", "rep": "the chain P-42 -> E-7 -> L-3"},
    {"q": "Which safety procedures concern the utilities zone?", "type": "aggregation", "rep": "SE-12"},
    {"q": "Which equipment belongs to the production zone?", "type": "aggregation", "rep": "L-3, L-5"},
    {"q": "What are the main maintenance themes of the site?", "type": "aggregation", "rep": "shutdown, upstream monitoring"},
    {"q": "Which production lines exist on the site?", "type": "aggregation", "rep": "L-3, L-5"},

    {"q": "Which components depend indirectly on P-42?", "type": "relational", "rep": "L-3, product X"},
    {"q": "Does pump P-17 feed line L-3?", "type": "relational", "rep": "no"},
    {"q": "Which equipment caused the March incident on L-3?", "type": "factual", "rep": "E-7 (overheating)"},
    {"q": "Which equipment must be isolated before shutting down L-3?", "type": "relational", "rep": "upstream: E-7, P-42"},
    {"q": "What is the restocking lead time for the parts of P-42?", "type": "factual", "rep": "six weeks"},
]


def main():
    (CORPUS / "fragments.json").write_text(
        json.dumps({"documents": DOCUMENTS}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (CORPUS / "expected_graph.json").write_text(
        json.dumps({"triplets": EXPECTED_TRIPLES}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (CORPUS / "questions.json").write_text(
        json.dumps({"questions": QUESTIONS}, ensure_ascii=False, indent=2),
        encoding="utf-8")

    n_doc = len(DOCUMENTS)
    n_tri = len(EXPECTED_TRIPLES)
    n_q = len(QUESTIONS)
    par_type = {}
    for q in QUESTIONS:
        par_type[q["type"]] = par_type.get(q["type"], 0) + 1

    print("Chapter 26 corpus (GraphRAG) written to corpus/")
    print(f"  - fragments.json       : {n_doc} documents")
    print(f"  - expected_graph.json  : {n_tri} triples (the ground truth)")
    print(f"  - questions.json       : {n_q} annotated questions")
    print("    split:", ", ".join(f"{k}={v}" for k, v in sorted(par_type.items())))
    print("\nNo document holds the complete chain P-42 -> E-7 -> L-3 -> product X.")
    print("That is deliberate: the vector finds documents, the graph finds the path.")


if __name__ == "__main__":
    main()
