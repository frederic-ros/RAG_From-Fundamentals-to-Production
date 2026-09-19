# ch32-ux-explainability — The user experience of a RAG: explainability as a feature

Labs for Chapter 32 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 32, which treats the ergonomics of a RAG not as a veneer, but as a trust-engineering block. The thesis: the ergonomics of a trust system does not hide the probabilistic complexity of the model, it makes the human verification instantaneous. The four labs unroll it. You first link each claim to its clickable proof: citations anchored through the text, narrative provenance at the head of the answer, persistent anchors that survive the reindexings (Lab 32-1). You then stage the doubt rather than masking it: confidence states (high, low, abstention) translated into clear language, never into a misleading percentage, then calibrated so that what the system dares to affirm is effectively reliable (Lab 32-2). You transform the wait time into active verification time thanks to streaming and split-screen, where the sources display as soon as the reranking ends (Lab 32-3). You finally close the improvement loop by capturing the implicit feedback of the behavior, long reading, copy-paste, reformulation, without asking anything of the user (Lab 32-4). The through-line follows Karim, who facing a broken-down machine does not read an answer but verifies it, with the eyes of Céline and Isabelle on the trust journey. Particularity: the UX is proved by measures, not by screenshots; the mechanics are therefore reproducible Python simulations, doubled by standalone HTML demos. Without an API key (deterministic TF-IDF, or sentence-transformers as an option).

## Labs

1. **Lab 32-1 — Interactive citations and narrative provenance**
2. **Lab 32-2 — Uncertainty management and calibrated confidence**
3. **Lab 32-3 — Perceived latency: streaming and split-screen**
4. **Lab 32-4 — Implicit feedback and behavioral analysis**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab32-1_citations_provenance.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `uxkit.py`

## Dependencies

```
numpy>=1.24.0          # vectors, metrics and calibration (ECE)
scikit-learn>=1.3.0    # TF-IDF (mode hors-ligne)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
