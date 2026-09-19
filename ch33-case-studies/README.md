# ch33-case-studies — Case studies by domain: design matrices and architecture patterns

Labs for Chapter 33 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 33, the great synthesis of the book. You no longer code an isolated block: you assemble an architecture from a business specification and you justify each choice on the axes in tension, cost, quality, latency, security. The thesis: the good architecture is not the richest, it is the one that solves the specification at the best trade-off; you start from the need to work back toward the assembly, an inverse design matrix. The four labs unroll it. You first design a complete business RAG and you prove that a naive stack violates the constraints where a justified stack respects them (Lab 33-1). You then compare two architectures on a same specification to demonstrate that "richer" is not "better": the winner depends on the domain (Lab 33-2). You evolve an existing pipeline faced with a business change, measuring the regression without adaptation then the gain after targeted modifications (Lab 33-3). You finally defend the solution before an "IT department" with a scoring grid, confronting the jury's score with the objective score of a test bench (Lab 33-4). Three specifications structure the terrain, banking, aeronautics, e-commerce, carried by Claire, Julien, and Sophie. Particularity: these labs rely on a purely deterministic conceptual test bench, reproducible, without an API key or any third-party dependency. It is the final exam: passing from the script developer to the architect of trusted AI systems.

## Labs

1. **Lab 33-1 — Designing a business RAG**
2. **Lab 33-2 — Comparing two architectures**
3. **Lab 33-3 — Adapting the pipeline to a business change**
4. **Lab 33-4 — Architecture defense**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab33-1_design_a_business_rag.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `archikit.py`

## Dependencies

```
numpy>=1.24.0   # optional; not required by archikit.py
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
