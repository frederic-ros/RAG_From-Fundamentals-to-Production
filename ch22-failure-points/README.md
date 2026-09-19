# ch22-failure-points — The Points of Failure

Labs for Chapter 22 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 22, which does not build but diagnoses: it draws the map of the ways a RAG fails, filed in three moments, before the question (ingestion, cutting, representation), during the search (intention, ranking, bias, consolidation) and at the answer (unexploited context, redundancy, format, incompleteness, misleading assurance, instability). Its thesis: four of the seven "historical" failures are retrieval failures, visible without any LLM. The four labs make this map tangible. You start by provoking the seven failures one by one, by actuating one sabotage lever at a time, to see each symptom with your own eyes (Lab 22-1). You then pass from the symptom to the measure, by building a mini-RAGAS that associates each family of failures with its metric, recall, nDCG, context precision, fidelity (Lab 22-2). You then learn to diagnose: faced with a real bad answer, you go up the chain and designate the link that gave way, rather than "repairing the RAG" blindly (Lab 22-3). You finish on the common root of the most serious failures, a system that does not reread itself, by opposing a single pass to a loop, which opens the door to the next chapter (Lab 22-4). The through-line follows Julien (maintenance, pumps P-12 / P-42 / P-88, motor M-18) and Claire (HR, remote work, bonuses). Two levels of realism cohabit, without an API key: the retrieval relies on a deterministic TF-IDF base (or sentence-transformers if it is present), and the generation as well as the RAGAS-style judge run on a real local LLM (Ollama) if it is available, otherwise on a deterministic fallback, the pedagogical point of each failure staying visible offline and reproducible.

## Labs

1. **Lab 22-1 — The seven failure points, by controlled sabotage**
2. **Lab 22-2 — Measuring the failures: a mini-RAGAS**
3. **Lab 22-3 — Diagnosis: faced with a bad answer, who gave way?**
4. **Lab 22-4 — The common root: single pass versus loop**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab22-1_sabotage.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `ragdiag.py`

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
