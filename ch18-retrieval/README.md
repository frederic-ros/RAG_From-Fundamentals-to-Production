# ch18-retrieval — Retrieval Techniques: Hybrid Search

Labs for Chapter 18 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 18, which opens the part devoted to advanced retrieval: no longer preparing the data, but searching better in it. The five labs follow the rise of the chapter, from the problem toward the tool. You start from the blind spot of dense search, its near-blindness to exact codes and references, where "E-204" and "E-205" merge (Lab 18-1). You discover the other searcher, the lexical BM25 search, which never misses an exact reference but ignores the synonyms: forces almost exactly complementary (Lab 18-2). You understand why adding the scores of the two methods is absurd, kilometers and degrees, and how the reciprocal rank fusion (RRF) circumvents the problem by keeping only the order (Lab 18-3). You then assemble the hybrid search and you measure, on a set of queries mixing codes and intentions, that it catches up the blind spots of each method (Lab 18-4). Finally, you pose two ideas that carry all the rest: retrieve wide then refine (the reranking, sketched here, developed in chapter 20) and the diversity as a condition of the hybrid, fusing two similar searchers brings nothing (Lab 18-5). The through-line follows Julien, in maintenance, and his error code E-204. BM25 is implemented by hand, in pure Python, to make the formula transparent; the dense search relies on a real embedding model if it is available, and switches otherwise to a TF-IDF base. Where a phenomenon (the blind spot on the codes) requires real dense vectors to appear natively, the fallback simulates it faithfully and the guide signals it honestly. No API key is required.

## Labs

1. **Lab 18-1 — The blind spot of dense search: exact codes**
2. **Lab 18-2 — BM25, the literal searcher: symmetrical strengths and limits**
3. **Lab 18-3 — Why you cannot add the scores: rank fusion (RRF)**
4. **Lab 18-4 — Hybrid search: reconciling the two searchers**
5. **Lab 18-5 — Retrieve wide then refine, and the diversity condition**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab18-1_dense_blind_spot.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `bm25.py`
- `corpus.py`
- `embeddings.py`
- `rrf.py`

## Dependencies

```
scikit-learn>=1.3.0    # dense-search fallback (deterministic offline TF-IDF)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
