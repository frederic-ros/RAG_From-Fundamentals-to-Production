# ch02-rag-pipeline — Introduction to RAG

Labs for Chapter 2 of *RAG — From Fundamentals to Production*.

This chapter gathers the labs associated with chapter 2 of the book. There, you rebuild the RAG pipeline as a simple chain: a question, documents, an augmentation step, then a generation. The first three labs isolate the fundamental blocks; the last two open toward the real problems of production: hallucinations, prompt injection, and multi-step reasoning.

## Labs

1. **Lab 2-1 — Assembling a first conceptual RAG: the anatomy**
2. **Lab 2-2 — Building an augmented prompt from documents**
3. **Lab 2-3 — Direct answer versus grounded answer**
4. **Lab 2-4 — The hallucination detective: guardrails and injected prompt**
5. **Lab 2-5 — From linear RAG to agentic RAG**

## Running them

```bash
python lab2-1_rag_anatomy.py
```

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
