# ch01-lexical-search — Searching Without Understanding

Labs for Chapter 1 of *RAG — From Fundamentals to Production*.

This chapter gathers the labs associated with chapter 1 of the book. There, you build, with your own hands and without a language model, the lexical-search block: TF-IDF vectorization, cosine similarity, comparison with BM25, then an elementary RAG. The last lab — "the test that hurts" — exposes the limit of any lexical search and motivates the passage to embeddings (chapter 4 of the book).

## Labs

1. **Lab 1-1 — Lexical search with TF-IDF**
2. **Lab 1-2 — TF-IDF versus BM25**
3. **Lab 1-3 — An elementary RAG without an LLM**
4. **Lab 1-4 — Rule-based lexical chatbot**
5. **Lab 1-5 — The test that hurts**

## Running them

```bash
python lab1-1_tfidf_cosine_topk.py
```

## Dependencies

```
numpy
scikit-learn
rank-bm25
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
