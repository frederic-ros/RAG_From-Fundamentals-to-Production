# -*- coding: utf-8 -*-
"""
Lab 16-6 — Mini-GraphRAG: a sub-graph against flat chunks (Julien)

Learning objective
------------------
Assemble the pieces of the previous labs into a MINI-GraphRAG, and compare it,
on the SAME question, with a classic "flat" RAG. The central idea of GraphRAG:

    Instead of retrieving ISOLATED fragments of text, the system retrieves a
    SUB-GRAPH of linked facts, and supplies that to the model so it can reason
    over relations rather than over resemblances.

This lab builds two "contexts" for a multi-hop question:

  1. THE FLAT CONTEXT: the k best chunks by similarity, which is what a classic
     RAG would give the LLM. The links are scattered there, the connection
     missing.
  2. THE GRAPH CONTEXT: the relevant sub-graph, serialised as triples, plus the
     computed route. The complete chain is EXPLICIT there.

No LLM is called and no API key is needed: the two contexts are DISPLAYED side by
side, so the reader can SEE what each approach puts before the model. The lesson:
with the flat context the LLM has to guess the link; with the graph context it
only has to read it.

No API key. Run generate_corpus.py first.
"""

from __future__ import annotations

from typing import List, Tuple

import corpus
import embeddings
from graph import Graph, format_path


# ---------------------------------------------------------------------------
# 1. The flat RAG: the top-k chunks by similarity
# ---------------------------------------------------------------------------
def flat_context(question: str, k: int = 3) -> List[str]:
    docs = corpus.load_documents()
    names = list(docs.keys())
    texts = list(docs.values())
    engine = embeddings.SimilarityEngine(texts)
    excerpts = []
    for idx, score in engine.search_for(question, k=k):
        # A "chunk" is simulated by the last useful block of the document.
        excerpt = texts[idx].strip().split("\n\n")[-1].strip()
        excerpts.append(f"[{names[idx]} | score {score:.3f}] {excerpt}")
    return excerpts


# ---------------------------------------------------------------------------
# 2. GraphRAG: extract the relevant sub-graph
# ---------------------------------------------------------------------------
def entities_of_the_question(g: Graph, question: str) -> List[str]:
    """Naively spot the graph entities named in the question.

    In production (Part V) this step would fall to an entity extractor. Here a
    simple match on the name is enough to isolate the idea.
    """
    q = question.lower()
    return [n for n in g.nodes() if n.lower() in q]


def relevant_subgraph(g: Graph, start: str, chain_relation: str) -> List[Tuple[str, str, str]]:
    """Extract the triples that mark out the chain leaving `start`."""
    chain = g.chain(start, chain_relation)
    triples = []
    for i in range(len(chain) - 1):
        triples.append((chain[i], chain_relation, chain[i + 1]))
    return triples


def graph_context(g: Graph, question: str) -> Tuple[List[str], str]:
    """Build the graph context: the relevant triples plus the route."""
    entities = entities_of_the_question(g, question)
    triples: List[Tuple[str, str, str]] = []
    route = ""

    if "P-17" in entities:  # a question of succession
        triples = relevant_subgraph(g, "P-17", "superseded by")
        chain = g.chain("P-17", "superseded by")
        route = " -> ".join(chain)
    elif entities:  # a question of dependency: walk up towards the suppliers
        start = entities[0]
        for supplier in ("Mecafluid", "Voltis"):
            path = g.path_bfs(start, supplier)
            if path:
                route = format_path(path, start)
                current = start
                for relation, node in path:
                    triples.append((current, relation, node))
                    current = node
                break

    lines = [f"{s} --[{r}]--> {o}" for s, r, o in triples]
    return lines, route


def show_block(title: str, lines: List[str]) -> None:
    print(title)
    if not lines:
        print("    (empty)")
    for line in lines:
        print(f"    {line}")


def process(g: Graph, question: str) -> None:
    print("=" * 78)
    print(f"QUESTION: \"{question}\"")
    print("=" * 78)

    print("\n--- CONTEXT 1: FLAT RAG (the top-k chunks by similarity) " + "-" * 21)
    show_block("What the LLM would receive:", flat_context(question))
    print("  => The links are there, but scattered. The CONNECTION between them is")
    print("     not given: the model has to GUESS it — and often gets it wrong.")

    print("\n--- CONTEXT 2: GraphRAG (a sub-graph of linked facts) " + "-" * 23)
    triples, route = graph_context(g, question)
    show_block("The relevant sub-graph, as triples:", triples)
    if route:
        print(f"  The computed route: {route}")
    print("  => The complete chain is EXPLICIT. The model has only to read it.")


def main() -> None:
    if not corpus.corpus_ready():
        print("Corpus not found. Run this first: python generate_corpus.py")
        return

    g = corpus.load_graph()

    print("#" * 78)
    print("# Lab 16-6 — Mini-GraphRAG: a sub-graph against flat chunks")
    print("#" * 78 + "\n")
    print(f"Embedding mode: {embeddings.mode()}\n")

    process(g, "Which procedure supersedes the one that superseded P-17?")
    print()
    process(g, "Which supplier does pump P-42 depend on?")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- A flat RAG supplies FRAGMENTS; GraphRAG supplies RELATIONS.")
    print("- On a multi-hop question the flat context leaves a hole the model must fill")
    print("  by guesswork; the graph context fills it explicitly.")
    print("- GraphRAG does not REPLACE embeddings: it COMPLETES them. Semantic")
    print("  proximity finds the right entities, relational traversal chains the facts.")
    print("\nWHAT TO REMEMBER")
    print("  Retrieving a sub-graph of linked facts, rather than isolated fragments:")
    print("  that is the principle Part V will industrialise (Neo4j, Cypher, GraphRAG).")


if __name__ == "__main__":
    main()
