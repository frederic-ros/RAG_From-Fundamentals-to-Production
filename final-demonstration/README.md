# final-demonstration — the final demonstration

The closing demonstration: one corpus carried from a naive retrieval system to a governed one, tier by tier.

This guide accompanies the final demonstration of the book. Throughout the work, each technique was tested on an isolated case: a chunking that fails, a fragment that lies, a score that deceives. The super-lab does something else: it takes a single corpus, a single battery of questions, and measures a single figure, the proportion of questions the system allows you to answer correctly. Then it makes it rise, level after level, by plugging the techniques of the book back in the order they appeared. The naive one fails; the structuring repairs; the context and the validity repair further; the advanced retrieval, the governance, and the security complete it. No new technique is introduced: the thesis of the book, the performance of a RAG holds as much in the representation of its corpus as in the finesse of its search, stops here being an argument to become a curve that rises. Everything is deterministic, without an API key.

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python admission.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `admission.py`
- `embeddings.py`
- `harness.py`
- `tiers.py`
- `tokenizer.py`

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
