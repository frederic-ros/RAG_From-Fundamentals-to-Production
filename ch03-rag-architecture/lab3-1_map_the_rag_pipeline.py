# -*- coding: utf-8 -*-
"""
Lab 3-1 — Mapping a RAG pipeline

Learning objective
------------------
This lab builds a textual map of a complete RAG pipeline.

The aim is not yet to code a high-performing RAG engine. It is to name the zones
of the system, and to associate with each of them the errors it can produce.

A RAG is not a single model:

    documents -> indexing -> index -> retrieval -> augmentation -> generation
"""

from typing import List, Dict


# =============================================================================
# 1. DEFINING THE STAGES OF THE PIPELINE
# =============================================================================

PIPELINE: List[Dict[str, object]] = [
    {
        "step": "Documents",
        "role": "The raw sources of knowledge: PDFs, web pages, notes, procedures.",
        "possible_errors": [
            "document missing",
            "document out of date",
            "document contradictory",
        ],
    },
    {
        "step": "Preparation",
        "role": "Clean, extract, cut and structure the documents.",
        "possible_errors": [
            "text badly extracted",
            "chunk too short",
            "chunk too long",
        ],
    },
    {
        "step": "Indexing",
        "role": "Store the passages in a queryable structure.",
        "possible_errors": [
            "wrong field indexed",
            "metadata lost",
            "index not updated",
        ],
    },
    {
        "step": "Retrieval",
        "role": "Find the passages useful to the question.",
        "possible_errors": [
            "the good document not retrieved",
            "passage too general",
            "misleading score",
        ],
    },
    {
        "step": "Augmentation",
        "role": "Build the context and the instructions sent to the model.",
        "possible_errors": [
            "context too noisy",
            "instruction ambiguous",
            "sources not separated",
        ],
    },
    {
        "step": "Generation",
        "role": "Write the final answer from the context.",
        "possible_errors": [
            "hallucination",
            "poor synthesis",
            "no caution",
        ],
    },
    {
        "step": "Answer",
        "role": "Return an answer the user can act on.",
        "possible_errors": [
            "no citation",
            "no confidence level",
            "answer not actionable",
        ],
    },
]


# =============================================================================
# 2. DISPLAYING THE MAP
# =============================================================================

def show_pipeline_map() -> None:
    """Print a textual map of the pipeline."""
    print("=" * 78)
    print("MAP OF THE RAG PIPELINE")
    print("=" * 78)

    for i, item in enumerate(PIPELINE, start=1):
        print(f"\n{i}. {item['step'].upper()}")
        print(f"   Role: {item['role']}")
        print("   Possible errors:")
        for error in item["possible_errors"]:
            print(f"   - {error}")


def show_compact_flow() -> None:
    """Print the chain as a row of arrows."""
    steps = [item["step"] for item in PIPELINE]
    print("\n" + "=" * 78)
    print("THE COMPACT VIEW")
    print("=" * 78)
    print(" -> ".join(steps))


# =============================================================================
# 3. THE MAIN PROGRAM
# =============================================================================

def main() -> None:
    show_pipeline_map()
    show_compact_flow()

    print("\nWHAT TO REMEMBER")
    print("- A bad answer can come from several zones of the pipeline.")
    print("- Diagnosing a RAG means knowing where to look.")
    print("- The map of the pipeline is the compass for the chapters that follow.")


if __name__ == "__main__":
    main()
