# ch14-hierarchy — Document Hierarchy & Parent-Child

Labs for Chapter 14 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 14, doubtless the most important of the structuring part. Chapter 12 asked how to cut, chapter 13 on what to cut; chapter 14 confronts the problem that remains once the two are resolved: a fragment can be perfectly exact and yet produce a bad answer. The problem is no longer the cutting, it is the loss of the context that gave the fragment its meaning. The five labs are thus built around this paradox, and you first create the shock before any technique. You show an exact fragment that answers wrong, then you make it go up toward its context, you draw from it the Parent-Child architecture, you assemble and measure the Small-to-Big pipeline, and you conclude, in a bonus lab, on what the disappearance of the hierarchy costs. The through-line is carried by Claire and her remote-work agreement, by Sophie and her regulations: an article, an exception, or a clause only have meaning because they belong to a hierarchy. No generative model is required; you measure the quality of the provided context, without an API key.

## Labs

1. **Lab 14-1 — The exact fragment that answers wrong**
2. **Lab 14-2 — Finding the lost context**
3. **Lab 14-3 — Parent-Child: search small, answer big**
4. **Lab 14-4 — Small-to-Big in practice**
5. **Lab 14-5 — When the hierarchy disappears**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab14-1_exact_fragment_false_answer.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `tokenizer.py`
- `tree.py`

## Dependencies

```
scikit-learn>=1.3.0    # TF-IDF search over child fragments (all labs)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
