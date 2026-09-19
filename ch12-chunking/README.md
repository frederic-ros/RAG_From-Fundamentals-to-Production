# ch12-chunking — Chunking Strategies

Labs for Chapter 12 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 12, which opens the part devoted to cutting, metadata, and structuring. Cutting is not a preprocessing setting: it is a design decision that determines what the system will be able to find. The six labs follow the order of the chapter — the problem before the algorithm. You first discover that an information perfectly present can become unfindable because of a badly placed cut. You then confront the regulatory case, where cutting a clause in two produces a legally false answer. You compare the strategies on a test bench, you understand why the recursive cutting has become the good default, you put to the test the cost of the semantic cutting, and you finally dismantle the myth according to which a large context window would exempt you from cutting well. All the labs measure the size in tokens, via a shared module that uses tiktoken if it is available and a deterministic fallback otherwise, without an API key.

## Labs

1. **Lab 12-1 — The information is there, but unfindable**
2. **Lab 12-2 — The clause cut in two**
3. **Lab 12-3 — Comparing the chunking strategies**
4. **Lab 12-4 — Why recursive cutting became the standard**
5. **Lab 12-5 — Is semantic chunking really worth its cost?**
6. **Lab 12-6 — The large context window does not save a bad chunking**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab12-1_unfindable_information.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `tokenizer.py`

## Dependencies

```
scikit-learn>=1.3.0    # TF-IDF search and semantic splitting (Labs 12-3 and 12-5)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
