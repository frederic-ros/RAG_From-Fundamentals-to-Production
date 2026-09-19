# ch29-evaluation — Evaluation: proving a RAG does not hallucinate

Labs for Chapter 29 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 29, which transforms the evaluation from an impression ("it looks good") into a localizable diagnosis. The seven labs build, block by block, the practitioner's toolkit. You start with the complete triad, recall@k, MRR, nDCG on the retrieval side, fidelity and relevance on the generation side, and you learn to read it to localize a failure: a null context recall points to the retrieval, a low fidelity points to the generation (Lab 29-1). You make the thermometer, a golden set, and you show why its expert validation is non-negotiable (Lab 29-2). You install an LLM judge by measuring its biases, self-preference, position, and the practices that attenuate them (Lab 29-3). You distinguish the offline evaluation from the online observability by tracking the silent drift, this failure where the technical metrics stay green while the user disengages (Lab 29-4). You set the coverage / reliability arbitration by the abstention rate (Lab 29-5), you measure the rising indicators, attribution and citation (Lab 29-6), and you close with a benchmark that makes the arbitration explicit (Lab 29-7). The through-line remains the maintenance documentation, in the continuity of Julien and Sophie. Without an API key: deterministic TF-IDF retrieval (or sentence-transformers), judge by fact overlap (or a local LLM via Ollama, for example Mistral), extractive generation (or grounded by the LLM).

## Labs

1. **Lab 29-1 — The triad: recall@k, MRR, nDCG, fidelity, context recall**
2. **Lab 29-2 — Making the golden set: synthetic + expert validation**
3. **Lab 29-3 — LLM-as-a-Judge: judging at scale and measuring its biases**
4. **Lab 29-4 — Online observability and silent drift**
5. **Lab 29-5 — The coverage / reliability arbitration (abstention rate)**
6. **Lab 29-6 — Rising indicators: attribution and citation**
7. **Lab 29-7 — Complete benchmark: comparing configurations**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab29-1_triad_pipeline.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `evalkit.py`

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
