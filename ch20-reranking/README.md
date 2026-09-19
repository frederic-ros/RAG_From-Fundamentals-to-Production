# ch20-reranking — Re-ranking: Retrieve Broad, Then Refine

Labs for Chapter 20 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 20, which transforms a good list of candidates into a good head of list. The previous chapters had won the recall, the good answer is, almost surely, somewhere in the pool, but "somewhere" is not "at the top," and the generation model reads only the first fragments. The six labs follow the rise of the chapter, from the problem toward the tool. You start from the finding: on an exact-reference query ("motor M-18"), the good fragment is relegated far by the initial retrieval, behind neighboring codes (M-17, M-19) that resemble it (Lab 20-1). You then oppose the two ways of judging the relevance: the bi-encoder, which encodes question and document separately (fast, coarse), and the cross-encoder, which reads the pair together (slow, fine) and makes the good fragment come up (Lab 20-2). You chain the two in the two-stage pipeline, retrieve wide, then refine, and you measure the purified head of list for a cost bounded to the pool (Lab 20-3). You then correct a residual flaw, the redundancy, by the MMR diversification and its $$ slider (Lab 20-4). You assemble everything on Julien's case, retrieval, re-ranking, MMR, to see the complete pipeline at work (Lab 20-5). A bonus lab finally measures the gain (MRR, nDCG) and its cost, because you prove a gain, you do not suppose it (Lab 20-6). A second bonus lab asks what sorting leaves untouched: once a fragment is chosen, must it travel whole? It scores sentences against the query and sweeps a token budget until the fact the question needs quietly disappears, a failure that stays plausible and easy to miss without measuring it (Lab 20-7). The through-line follows Julien and his motor M-18. The code detects real bi- and cross-encoders (sentence-transformers) if they are available, and switches otherwise to a deterministic TF-IDF fallback that faithfully reproduces the phenomenon, including, by a fold of the codes onto a family token, the blind spot of the dense on the exact references. No API key is required.

## Labs

1. **Lab 20-1 — The good answer is badly ranked**
2. **Lab 20-2 — Bi-encoder versus cross-encoder**
3. **Lab 20-3 — The two-stage pipeline**
4. **Lab 20-4 — Why the first ones all resemble each other (MMR)**
5. **Lab 20-5 — Julien looks for the best procedure**
6. **Lab 20-6 — Measuring the gain and its cost (MRR, nDCG) (bonus)**
7. **Lab 20-7 — Compressing the context: how much can you cut before the answer breaks? (bonus)**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab20-1_right_answer_badly_ranked.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `reranklib.py`

## Dependencies

```
numpy>=1.24.0          # vectors and calculations (MMR and metrics)
scikit-learn>=1.3.0   # TF-IDF du bi-encoder en mode hors-ligne (repli)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
