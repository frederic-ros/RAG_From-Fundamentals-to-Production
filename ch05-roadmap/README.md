# ch05-roadmap — Build Before You Search: The Enterprise Roadmap

Labs for Chapter 5 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 5 of the book. It marks a change of gaze: you pass from a technological vision of RAG to a project vision. A RAG is always the same technical system; it is the business context that changes everything. The labs follow three through-line cases — a local authority, an industrial SME, and a multi-client HR firm — to transform a fuzzy need into a framed project, qualify the document heritage, build a realistic roadmap, measure before optimizing, then prepare the passage to production. The HR-firm case adds a requirement the others do not have: the strict partitioning of the data between clients. Each provided tool checks the deliverable rather than producing it in your place. No lab requires an API key or an external dependency.

## Labs

1. **Lab 5-1 — Framing a RAG project on one page**
2. **Lab 5-2 — Mapping the document heritage**
3. **Lab 5-3 — Building a 90-day roadmap**
4. **Lab 5-4 — Creating a business evaluation set**
5. **Lab 5-5 — Preparing the passage to production**

## Running them

```bash
python lab5-1_scope_the_rag_project.py
```

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
