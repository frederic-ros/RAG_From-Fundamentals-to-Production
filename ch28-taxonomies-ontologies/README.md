# ch28-taxonomies-ontologies — Taxonomies, ontologies and business graphs: injecting business knowledge into retrieval

Labs for Chapter 28 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 28, which closes Part V by introducing the semantic layer: no longer structuring the content of the documents (chapters 26-27), but the knowledge of the domain itself. The seven labs unroll the trinity taxonomy / ontology / business graph on a single through-line, industrial maintenance, in the continuity of Julien and Sophie. You start from the most immediate gain: query expansion by a taxonomy, which reconciles the vocabulary of the technician ("cavitation") and that of the documents ("hydrodynamic erosion"), making the business recall come up from about 40 % to 73 % (Lab 28-1). You then build and validate an ontology, this meta-model that knows how to forbid (Lab 28-2), and you use it to constrain the extraction of triples (Lab 28-3) then structure a graph on the fly on the only useful fragments, without a global index (Lab 28-4, RAS). The fifth lab measures the precision gap between blind and guided GraphRAG (Lab 28-5), the sixth assembles the complete layer behind a single pipeline (Lab 28-6), and the last poses the final lock: the validation of the absolute business rules, the axioms (Lab 28-7). Without an API key: deterministic TF-IDF retrieval (or sentence-transformers), mapping and extraction by templates (or a local LLM via Ollama, for example Mistral), the thesis of the chapter staying visible, offline and reproducible.

## Labs

1. **Lab 28-1 — The taxonomic guardrail: query expansion**
2. **Lab 28-2 — Building and validating a business ontology**
3. **Lab 28-3 — Schema-constrained extraction (ontology-driven GraphRAG)**
4. **Lab 28-4 — RAS: Retrieval-And-Structuring (graph on the fly)**
5. **Lab 28-5 — Blind GraphRAG vs guided GraphRAG**
6. **Lab 28-6 — Integrating the semantic layer (synthesis)**
7. **Lab 28-7 — Validation of the absolute business rules (axioms)**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab28-1_taxonomic_guardrail.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `businesskit.py`

## Dependencies

```
numpy>=1.24.0          # vectors and metrics
scikit-learn>=1.3.0    # TF-IDF (mode hors-ligne)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
