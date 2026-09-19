# -*- coding: utf-8 -*-
"""
Lab 16-5 — The domino effect: the hidden impact of relations (Julien)

Learning objective
------------------
Simulate the STOPPAGE of a supplier and MEASURE every indirect impact along the
industrial chain. This is the most concrete business value of the graph: risk
management.

    "Which equipment will be impacted if the supplier Mecafluid stops
    production?"

The answer is written in no document: it is CALCULATED by walking back the
relations. This lab:

  1. computes the tree of impacted dependencies (the domino effect);
  2. traces the critical path up to the production line;
  3. shows that the MODELLING choice — which relations "count" — changes the
     answer, a key lesson of the chapter;
  4. sets the result against a classic retrieval, blind to those links.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

import corpus
import embeddings
from graph import format_path

# The relations that express a PHYSICAL DEPENDENCY, as opposed to a documentary
# succession. This subset is what defines the "material" domino effect.
DEPENDENCIES = {"uses", "depends on", "powered by", "supplied by"}


def domino_effect(g, source: str) -> None:
    print("=" * 78)
    print(f"STEP 1 — The domino effect: \"if {source} stops, who is impacted?\"")
    print("=" * 78)
    impacted = g.impacted_by(source, relations=DEPENDENCIES)
    if not impacted:
        print(f"  No equipment depends on {source}.")
        return
    print("  Components, equipment and installations impacted, by depth:")
    flat = []
    for node, depth in impacted:
        flat.append(node)
        indent = "    " + "   " * (depth - 1)
        print(f"{indent}\\_ {node}  ({g.types.get(node,'?')}, hop {depth})")
    print(f"\n  The flat list of the impacted: {flat}")


def critical_path(g, source: str, target: str) -> None:
    print("\n" + "=" * 78)
    print(f"STEP 2 — The critical path: from {source} up to {target}")
    print("=" * 78)
    # The path is sought in the direction of the dependencies: target -> source.
    path = g.path_bfs(target, source)
    if path is not None:
        print("  " + format_path(path, target))
        print(f"\n  => A stoppage at {source} reaches {target} in {len(path)} hops.")
        print(f"     The business consequence: production on {target} is threatened.")
    else:
        print("  No critical path.")


def effect_of_the_model(g, source: str) -> None:
    print("\n" + "=" * 78)
    print("STEP 3 — The modelling decides the answer")
    print("=" * 78)
    strict = g.impacted_by(source, relations=DEPENDENCIES)
    broad = g.impacted_by(source)  # every relation, without distinction
    print(f"  Following ONLY the physical dependencies {sorted(DEPENDENCIES)}:")
    print(f"    {[n for n, _ in strict]}")
    print("  Following EVERY relation, including \"adjusts\" and \"supersedes\":")
    print(f"    {[n for n, _ in broad]}")
    print("\n  Both answers are defensible — and different. The way you MODEL the")
    print("  graph, which relations count as a \"dependency\", decides directly what")
    print("  is judged \"impacted\". The graph does not spare you the thinking: it")
    print("  makes that choice EXPLICIT, and arguable.")


def retrieval_contrast(source: str) -> None:
    print("\n" + "=" * 78)
    print("STEP 4 — Why a classic retrieval sees NONE of this")
    print("=" * 78)
    docs = corpus.load_documents()
    names = list(docs.keys())
    texts = list(docs.values())
    engine = embeddings.SimilarityEngine(texts)

    question = f"Which equipment is impacted if {source} stops production?"
    print(f"Embedding mode: {embeddings.mode()}")
    print(f"Question: \"{question}\"\n")
    for rank, (idx, score) in enumerate(engine.search_for(question, k=3), 1):
        print(f"  {rank}. {names[idx]:<26} (score {score:.3f})")
    print(f"\n  The search brings back the {source} sheet and some equipment sheets,")
    print("  all relevant — but NONE lists the chain of impact. The information \"the")
    print("  failure reaches L-3\" is written nowhere: it is DISTRIBUTED across the")
    print("  links, invisible to a search by resemblance.")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    g = corpus.load_graph()
    source = "Mecafluid"

    print("#" * 78)
    print("# Lab 16-5 — The domino effect: the hidden impact of relations")
    print("#" * 78 + "\n")

    domino_effect(g, source)
    critical_path(g, source, "L-3")
    effect_of_the_model(g, source)
    retrieval_contrast(source)

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- The business value of the graph is concrete: anticipating a chain risk.")
    print("- The answer is not SEARCHED FOR, it is TRAVERSED — computed over the links.")
    print("- This information is invisible to a retrieval: no document carries it.")
    print("\nWHAT TO REMEMBER")
    print("  Where the questions are genuinely relational — dependencies, risks — the")
    print("  graph makes computable what no fragment contains.")


if __name__ == "__main__":
    main()
