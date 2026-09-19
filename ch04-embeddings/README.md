# ch04-embeddings — Mapping Meaning: From Words to Vectors

Labs for Chapter 4 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 4 of the book. The objective is no longer to search for words, but to search for meaning. The labs make this passage tangible: you see the lexical engine fail where the semantic engine succeeds, you compute the cosine similarity by hand, you draw a map of meaning in 2D, you fuse the lexical ranking and the semantic ranking, and you finally discover the decisive limit of the semantic alone: close does not mean reliable. All the labs run without an API key or a model download, thanks to deterministic pedagogical embeddings.

## Labs

1. **Lab 4-1 — TF-IDF vs embeddings (the synonym case)**
2. **Lab 4-2 — Cosine similarity under the hood**
3. **Lab 4-3 — The map of meaning in 2D (PCA projection)**
4. **Lab 4-4 — Hybrid search with RRF**
5. **Lab 4-5 — Close does not mean reliable**

## Running them

```bash
python lab4-1_tfidf_vs_embeddings_synonyms.py
```

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
