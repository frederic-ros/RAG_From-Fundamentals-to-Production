# ch07-ai-ready — The AI-Ready Document: Designing for Humans and Machines

Labs for Chapter 7 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 7 of the book. It answers a decisive question: how to spot a machine-hostile document, and how to correct it? The labs transform the five AI-ready principles into practice. You first rewrite by hand a hostile sheet of Julien's, you then measure the search gain obtained, you code a linter that automatically detects the hostile documents, you put the sparser into action to correct on the fly, then you quantify the return on investment of a document charter against the algorithmic escalation. The hostile / AI-ready document pair, synthetic and reproducible, serves as a through-line; the labs work without an API key, with optional engines and models.

## Labs

1. **Lab 7-1 — Manual overhaul of a hostile document**
2. **Lab 7-2 — Measuring the retrieval gain: before / after**
3. **Lab 7-3 — An automated AI-ready-score "linter"**
4. **Lab 7-4 — The sparser in action: automatic correction**
5. **Lab 7-5 — ROI dashboard: quantifying the document effort**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_sample_docs.py
python lab7-1_manual_rework.py
```

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
