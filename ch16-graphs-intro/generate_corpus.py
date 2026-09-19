# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 16.

Chapter 16 has a single thesis: some answers are not IN a document, but BETWEEN
the documents, in the link that joins them. The corpus is therefore built so
that:

  - every elementary FACT is written down somewhere (a search finds it);
  - but NO document holds the complete CHAIN (the answer stays invisible to a
    retrieval, however perfect).

The setting: an industrial bottling line (Julien's domain), with a fictional
supplier, "Mecafluid". The chapter's chain of procedures is preserved —
P-17 -> P-18 -> P-21 — where no document ever says that P-21 "supersedes P-17".

Two outputs, deliberately kept apart, and that separation is the heart of the
lesson:

    corpus/documents/*.txt — the documents, in free text. This is what a
        classic RAG sees: they are vectorised, and searched by resemblance.

    corpus/triples.tsv — the RELATIONS, extracted and made explicit as triples
        (subject relation object). This is what a graph sees. In real life these
        triples would be EXTRACTED from the documents (Part V); here they are
        supplied, to isolate the idea: a relation is information in its own
        right.

A NOTE ON THE RELATION LABELS. The strings in TRIPLES are the graph's edge
labels, and several labs match on them literally ("superseded by", "depends on",
"supplied by"). They must stay in step across generate_corpus.py, graph.py and
every lab. A label changed in one place and not the others produces an empty
traversal and a lab that silently finds nothing.

Deterministic. Run before the labs: python generate_corpus.py
"""

from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent / "corpus"
DOCS = BASE / "documents"


# ===========================================================================
# 1. THE DOCUMENTS (what a similarity search sees)
# ===========================================================================
# The golden rule: each document knows ONLY its immediate neighbour. The P-21
# sheet never mentions P-17. The motor sheet never mentions the production line.
# The complete chain is written nowhere.

DOCUMENTS = {
    # --- The chain of procedures (the chapter's "moment of shock") ------------
    "procedure_P17.txt": """\
Procedure P-17 — Setting up the pumping unit (original version).

This procedure describes the initial setting up of the pumping unit on the
bottling line. It fixes the service pressures and the start-up sequences.
Status: archived. This procedure is no longer applied as it stands; refer to the
setting-up documentation in force.
""",
    "procedure_P18.txt": """\
Procedure P-18 — Setting up the pumping unit (intermediate revision).

This procedure P-18 supersedes procedure P-17. It updates the service pressures
after the change of seals and specifies the priming sequence. Status: archived.
A later revision has been published.
""",
    "procedure_P21.txt": """\
Procedure P-21 — Setting up the pumping unit (revision in force).

This procedure P-21 supersedes procedure P-18. It takes in the new variable-speed
drive and the associated safety instructions. Status: in force. This is the
setting-up procedure applicable today on the bottling line.
""",
    # --- Equipment on the bottling line ---------------------------------------
    "pump_P42.txt": """\
Equipment sheet — Pump P-42.

Pump P-42 transfers the product to the filler. It is driven by an electric motor
and controlled by speed. Level 2 maintenance, quarterly. Pump P-42 depends on
motor M-18 for its drive.
""",
    "motor_M18.txt": """\
Equipment sheet — Motor M-18.

The asynchronous motor M-18 supplies the mechanical drive power. It is fed by a
variable-speed drive. Motor M-18 is supplied by the company Mecafluid. Catalogue
reference MF-3000.
""",
    "drive_V7.txt": """\
Equipment sheet — Variable-speed drive V-7.

The variable-speed drive V-7 sets the speed of the drive motor. It applies the
settings defined by the setting-up procedure in force. Drive V-7 is supplied by
the company Voltis.
""",
    "line_L3.txt": """\
Installation sheet — Bottling line L-3.

Line L-3 packages one-litre bottles. Its nominal throughput is twelve thousand
bottles an hour. Line L-3 uses pump P-42 to transfer the product. Any stoppage of
that pump interrupts production on L-3.
""",
    # --- Suppliers ------------------------------------------------------------
    "supplier_mecafluid.txt": """\
Supplier sheet — Mecafluid.

The company Mecafluid manufactures asynchronous motors and motor-pump units for
the food industry. Usual restocking lead time: six weeks. A dedicated sales
contact for critical parts.
""",
    "supplier_voltis.txt": """\
Supplier sheet — Voltis.

The company Voltis distributes variable-speed drives and controllers. It offers a
loan service for equipment in the event of a breakdown. Usual restocking lead
time: two weeks.
""",
    # --- "Distractor" documents: relevant, but off the chain -------------------
    "workshop_safety.txt": """\
Safety note — Bottling workshop.

Wearing personal protective equipment is compulsory in the workshop. Work on the
pumping units and the motors must follow the electrical lockout procedure before
any operation.
""",
    "general_maintenance.txt": """\
Maintenance plan — Bottling line.

The preventive maintenance plan covers the pumps, the motors and the drives.
Setting-up operations follow the setting-up procedure in force. The equipment
sheets give the interval specific to each item.
""",
}


# ===========================================================================
# 2. THE TRIPLES (what a knowledge graph sees)
# ===========================================================================
# Format: subject \t relation \t object
# In Part V these triples would be EXTRACTED from the documents automatically.
# Here they are supplied, to isolate the lesson: a relation is data in itself.

TRIPLES = [
    # The chain of procedures. BOTH directions are stored, because the same
    # succession reads one way ("P-18 supersedes P-17") or the other ("P-17 is
    # superseded by P-18"). Following "superseded by" as a chain leads from P-17
    # to P-21 — the multi-hop answer Julien is looking for.
    ("P-18", "supersedes", "P-17"),
    ("P-21", "supersedes", "P-18"),
    ("P-17", "superseded by", "P-18"),
    ("P-18", "superseded by", "P-21"),
    # Equipment dependencies (the "depends on" / "uses" chain)
    ("L-3", "uses", "P-42"),
    ("P-42", "depends on", "M-18"),
    ("M-18", "powered by", "V-7"),
    # Suppliers
    ("M-18", "supplied by", "Mecafluid"),
    ("V-7", "supplied by", "Voltis"),
    # The procedure applying to a piece of equipment
    ("P-21", "adjusts", "M-18"),
]

# Node types, from a small taxonomy: useful for the taxonomy plus graph lab.
TYPES = {
    "P-17": "Procedure", "P-18": "Procedure", "P-21": "Procedure",
    "P-42": "Equipment", "M-18": "Equipment", "V-7": "Equipment",
    "L-3": "Installation",
    "Mecafluid": "Supplier", "Voltis": "Supplier",
}


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)

    # 1) Write the text documents.
    for name, content in DOCUMENTS.items():
        (DOCS / name).write_text(content, encoding="utf-8")

    # 2) Write the triples, with a header comment.
    lines = ["# subject\trelation\tobject"]
    for subject, relation, obj in TRIPLES:
        lines.append(f"{subject}\t{relation}\t{obj}")
    (BASE / "triples.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 3) Write the types: the small taxonomy of nodes.
    type_lines = ["# node\ttype"]
    for node, type_ in sorted(TYPES.items()):
        type_lines.append(f"{node}\t{type_}")
    (BASE / "types.tsv").write_text("\n".join(type_lines) + "\n", encoding="utf-8")

    print("Chapter 16 corpus generated in:", BASE)
    print(f"  - {len(DOCUMENTS)} documents   -> {DOCS}")
    print(f"  - {len(TRIPLES)} triples     -> corpus/triples.tsv")
    print(f"  - {len(TYPES)} node types  -> corpus/types.tsv")
    print("\nThe key point: every fact is written somewhere, but no complete chain")
    print("(P-17 -> P-21, or Mecafluid -> L-3) appears in any single document.")


if __name__ == "__main__":
    main()
