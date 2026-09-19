# ch24-selfrag-crag-adaptive — Self-RAG, CRAG and Adaptive-RAG: the RAG that corrects and adapts

Labs for Chapter 24 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 24, which teaches the RAG three new gestures: to judge itself, to exit its corpus when it doubts, and to engage a costly loop only where it counts. The five labs follow this rise. You start with Self-RAG (Lab 24-1), which equips the system with "reflection tokens" (ISREL, ISSUP, ISUSE) and a confidence score: on a well-documented failure it assumes, on a rare failure it admits its uncertainty rather than hallucinating. You pass to CRAG (Lab 24-2), whose three-verdict grader (confident, ambiguous, not confident) triggers a web fallback, simulated and deterministic, when the corpus is lacunary: the honest answer to the "missing content" flaw of chapter 22. A cost lab (Lab 24-3) puts the three architectures side by side: the loop improves the quality, but is never free. Comes the router of Adaptive-RAG (Lab 24-4), which sorts the questions between direct answer, single pass, and complete loop, you pay the depth only if the question requires it. The last lab (Lab 24-5) assembles everything into an orchestrator that chooses, for each question, the right strategy. The through-lines follow Julien (maintenance), Claire (HR), and Sophie (architecture). Without an API key: the retrieval relies on a deterministic TF-IDF base (or sentence-transformers if it is present), and the judgments, reflection tokens, grader, router, are rendered by a real local LLM (Ollama) if it runs, otherwise by deterministic rules. The pedagogical point of each architecture appears clearly, offline and in a reproducible way.

## Labs

1. **Lab 24-1 — Self-RAG: learning to say "I am not sure"**
2. **Lab 24-2 — CRAG: when the documentary base no longer suffices**
3. **Lab 24-3 — The cost of the loop: when to relaunch?**
4. **Lab 24-4 — Adaptive-RAG: choosing the right depth**
5. **Lab 24-5 — Building a complete Adaptive-RAG**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab24-1_self_rag.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `cragkit.py`

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
