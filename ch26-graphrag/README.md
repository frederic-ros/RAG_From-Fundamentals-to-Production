# ch26-graphrag — GraphRAG: Implementation

Labs for Chapter 26 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 26, which implements what chapter 16 had announced: passing from the document to the knowledge network. The thesis holds in one sentence, and the five labs unroll it: the vector retrieval finds documents, the graph finds paths, and the good system routes each question toward the suited engine. You start from the failure finding, a vector RAG answers perfectly "what is the pressure of the P-42?" but stumbles on "what does the line fed by the P-42 manufacture?", because no document contains the complete chain P-42 $$ E-7 $$ L-3 $$ product X (Lab 26-1). You then build the graph automatically, and above all you measure the quality of the extraction against a ground truth, because the difficult part is not the graph, it is the correct extraction of the relations (Lab 26-2). Comes the question of the interrogation strategy: local search (neighborhood) for the targeted questions, global search (community summaries) for the aggregation, each excellent for its type, mediocre for the other (Lab 26-3). You then assemble the winning pattern, VectorCypher: the vector finds the entry point, the graph goes up the chain to the supplier (Lab 26-4). The last lab is the synthesis: a router that, on twenty-five annotated questions, sends each to the good engine and quantifies the gain, the real GraphRAG is not "a graph," it is a hybrid system that chooses (Lab 26-5). The through-line follows a concrete industrial site (Julien, maintenance; Sophie, architecture). Without an API key: the retrieval relies on a deterministic TF-IDF base (or sentence-transformers if it is present), the extraction and the routing on deterministic rules (or a local LLM via Ollama if it runs), the thesis of the chapter staying visible, offline and in a reproducible way.

## Labs

1. **Lab 26-1 — When the vector no longer suffices**
2. **Lab 26-2 — Automatically building your first graph**
3. **Lab 26-3 — Local vs Global: which search strategy?**
4. **Lab 26-4 — VectorCypher: the best of both worlds**
5. **Lab 26-5 — Designing a hybrid GraphRAG for a real industrial case**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab26-1_vector_limits.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `graphkit.py`

## Dependencies

```
numpy>=1.24.0          # vectors and metrics
scikit-learn>=1.3.0   # TF-IDF du retrieval en mode hors-ligne (repli)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
