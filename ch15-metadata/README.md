# ch15-metadata — Metadata: The Underestimated Lever

Labs for Chapter 15 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 15, devoted to the most underestimated lever of RAG: metadata. After learning to cut (chapters 12 and 13) and to preserve the context (chapter 14), you discover that an information can be perfectly retrieved and yet lead to a false decision, for lack of a validity label. The six labs form a progression from the shock toward the architect's maturity. You start from the emblematic case of two exact answers of which only one is valid, then you materialize the metaphor of the library without a date, you dismantle the trap of the best score, you build a trust policy, and you discover the other side of the coin: a filter can hide the truth. A bonus lab, "Sophie versus Julien," closes the chapter by showing that relevance is not absolute but relative to the context. The through-line reunites Sophie (regulatory) and Julien (technical). At this stage of the book, the labs rely on a real embedding model if it is available, and switch otherwise to a deterministic TF-IDF base, without an API key.

## Labs

1. **Lab 15-1 — Two exact answers, only one valid**
2. **Lab 15-2 — The library without a date**
3. **Lab 15-3 — When the best score is not the best document**
4. **Lab 15-4 — Building a trust policy**
5. **Lab 15-5 — The filter that hides the truth**
6. **Lab 15-6 — Sophie versus Julien**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab15-1_two_answers.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `corpus.py`
- `embeddings.py`
- `tokenizer.py`

## Dependencies

```
scikit-learn>=1.3.0    # TF-IDF search (fallback used by every lab)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
