# ch16-graphs-intro — Structuring Knowledge: Taxonomies and Graphs

Labs for Chapter 16 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 16, which marks a milestone of the through-line: you stop enriching the fragments to begin enriching the knowledge itself. The labs have a single objective, to reveal the limits of a retrieval founded solely on the chunks. As long as the answer holds in a fragment, the semantic search works; as soon as you have to link several dispersed facts, it reaches its limit. The progression starts from the shock (all the documents are there, the answer remains invisible), discovers the taxonomy that organizes and the graph that links, experiments with the multi-hop questions and their resolution by traversal, measures the business contribution of the relations (the industrial domino effect), then assembles the whole into a mini-GraphRAG that opposes flat chunks and a subgraph of linked facts. A synthesis lab, "Sophie versus Julien," closes the chapter by showing that not all knowledge calls for the same structure: the taxonomy classes, the graph links. At this stage, no graph base (Neo4j, Cypher) is necessary, the relations are manipulated as simple Python structures, to isolate the fundamental idea: a relation is an information in its own right. These labs directly prepare the advanced chapters of Part V (GraphRAG, Neo4j). The through-line reunites Sophie (regulatory) and Julien (maintenance), on a concrete bottling line. The labs rely on a real embedding model if it is available, and switch otherwise to a deterministic TF-IDF base, without an API key, the pedagogical point holding in both cases.

## Labs

1. **Lab 16-1 — All the documents are there, the answer remains invisible**
2. **Lab 16-2 — Building your first taxonomy**
3. **Lab 16-3 — From classification to network: when the taxonomy no longer suffices**
4. **Lab 16-4 — Multi-hop questions: chaining the facts**
5. **Lab 16-5 — The domino effect: the hidden impact of relations**
6. **Lab 16-6 — Mini-GraphRAG: subgraph versus flat chunks**
7. **Lab 16-7 — Sophie versus Julien: organize or link?**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab16-1_invisible_answer.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `corpus.py`
- `embeddings.py`
- `graph.py`

## Dependencies

```
scikit-learn>=1.3.0    # TF-IDF similarity search (deterministic fallback)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
