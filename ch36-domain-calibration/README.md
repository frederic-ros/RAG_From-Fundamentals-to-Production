# ch36-domain-calibration — Automatable annotations

Labs for Chapter 36 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 36, which closes the book on its thesis: the performance of an industrial RAG holds as much in the business representation of its corpus as in the finesse of its search. Where chapters 34 and 35 posed the paradox then defined the business calibration, this last lab implements it end to end and, above all, measures its gain. A single lab, but decomposed into five visible steps, deduce the calibration without a model, propose it then validate it, build the weighted score, rank, measure, so that each cog is observable. You compare a purely semantic retrieval to a retrieval weighted by the calibration, on questions where the good document is not the most similar: the FAQ against the agreement in force, the repealed procedure against the valid version. The demonstration is not made by an argument but by a score that rises, the recall@1 passes from about a third to the totality. The through-line follows Claire (HR) and Julien (maintenance). Without an API key: deterministic TF-IDF retrieval (or sentence-transformers), rule-based pre-annotation (or a local LLM via Ollama, for example Mistral).

## Labs

1. **Lab 36-1 — Calibrate a corpus, then measure the gain**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab36-1_calibrate_and_measure.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `calibkit.py`

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
