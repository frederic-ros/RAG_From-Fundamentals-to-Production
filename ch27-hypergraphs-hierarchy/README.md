# ch27-hypergraphs-hierarchy — Beyond the Flat Graph: Hypergraphs & Hierarchical Navigation

Labs for Chapter 27 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 27, which goes beyond the two blind spots of the flat graph: the thematic blind spot (fragments that speak of the same subject without sharing entities) and the hierarchical blind spot (the natural tree structure of a corpus, that the graph crushes). The seven labs unroll the answer of the chapter. You start from the finding: three procedures participate in the theme "business continuity" without being linked two by two, the flat graph creates no edge, the thematic hyperedge reunites them (Lab 27-1). You then build the hypergraph automatically by clustering, measuring that the difficult part is not the hypergraph but the discovery of the good themes (Lab 27-2). You switch to the hierarchy: a multi-level index of the documentation of a turbine, where the question determines the floor where to search (Lab 27-3); then RAPTOR, which summarizes recursively to reduce the search space (Lab 27-4). The fifth lab assembles the four representations (vector, graph, hypergraph, hierarchy) behind a multi-resolution router, evaluated on fifty annotated questions (Lab 27-5). The last two take the step back of the practitioner: an ablation study that reveals which layers are critical and which are redundant (Lab 27-6), and a cost optimization that looks for the balance point between quality and budget (Lab 27-7). The through-lines follow the quality documentation of a factory (Sophie) and the documentation of a gas turbine (Julien). Without an API key: the retrieval relies on a deterministic TF-IDF base (or sentence-transformers), the summaries on an extractive mode (or a local LLM via Ollama), the clustering on k-means (or HDBSCAN if it is present), the thesis of the chapter staying visible, offline and in a reproducible way.

## Labs

1. **Lab 27-1 — When the flat graph fails: the thematic blind spot**
2. **Lab 27-2 — Automatically building hypergraphs**
3. **Lab 27-3 — TreeRAG: finding the good level in the hierarchy**
4. **Lab 27-4 — RAPTOR: summarizing before searching**
5. **Lab 27-5 — Designing a multi-resolution engine**
6. **Lab 27-6 — Ablation study: which representation brings what?**
7. **Lab 27-7 — Cost optimization: finding the good balance**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab27-1_graph_vs_hypergraph.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `multikit.py`

## Dependencies

```
numpy>=1.24.0          # vectors and metrics
scikit-learn>=1.3.0   # TF-IDF, k-means and metrics (offline mode)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
