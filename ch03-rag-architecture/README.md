# ch03-rag-architecture — Detailed Architecture of a RAG System

Labs for Chapter 3 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 3 of the book. The objective is not yet to optimize each technical block, but to build a stable mental map of the complete system. The labs help distinguish indexing, retrieval, augmentation, generation, and domain calibration, then to diagnose the possible errors in the chain.

## Labs

1. **Lab 3-1 — Mapping a RAG pipeline**
2. **Lab 3-2 — Diagnosis of bad answers**
3. **Lab 3-3 — Adding a "domain calibration" box**
4. **Lab 3-4 — Before the question / at the moment of the question**
5. **Lab 3-5 — Tracing a RAG execution end to end**

## Running them

```bash
python lab3-1_map_the_rag_pipeline.py
```

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
