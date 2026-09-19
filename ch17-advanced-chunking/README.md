# ch17-advanced-chunking — Advanced Chunking: Beyond Fixed Chunking

Labs for Chapter 17 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 17, which returns to the raw material of RAG, the chunk, to make it an act of knowledge engineering. The thesis is sharp: an information can be present, and a bad cutting make it invisible. The six labs follow the rise of the chapter, from the problem toward the tool. You start by observing the evil: a fixed-size cut cuts "every 100 hours" in two, and the answer disappears (Lab 17-1). You then cut consciously: by following the structure of the document (Markdown, HTML) in Lab 17-2, then by cutting where the similarity between sentences drops in Lab 17-3. You tackle the lost context by two opposite paths, Late Chunking (on the vectors) and Contextual Retrieval (on the text), keeping in mind that neither is universally superior (Lab 17-4). You then entrust the boundary to an agent that decides according to the business logic rather than to the length (Lab 17-5). Finally, the semi-supervised chunking captures the expert's judgment at low cost and records it: the first stone of the domain calibration (Lab 17-6). The through-line reunites Julien (maintenance, the motor M-18 and the pump P-42) and Claire (HR, a rule and its exception). The labs rely on a real embedding model if it is available, and switch otherwise to a deterministic TF-IDF base; where a technique requires real dense vectors to fully reveal itself, the guide signals it honestly. No API key is required: the calls to an LLM (agent, contextualization) are replaced by deterministic and transparent stand-ins, with the mark, in the code, of the place where to plug a real model.

## Labs

1. **Lab 17-1 — Fixed chunking breaks the meaning: the Julien case**
2. **Lab 17-2 — Structural chunking: cutting according to the document plan**
3. **Lab 17-3 — Semantic chunking: cutting where the meaning changes**
4. **Lab 17-4 — Late Chunking versus Contextual Retrieval: who wins?**
5. **Lab 17-5 — The chunking agent: delegating the cutting to an LLM**
6. **Lab 17-6 — Semi-supervised chunking: the expert validates, the system learns**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab17-1_fixed_chunking_problem.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `chunkers.py`
- `contextual.py`
- `corpus.py`
- `embeddings.py`
- `interface.py`

## Dependencies

```
scikit-learn>=1.3.0    # TF-IDF similarity (deterministic offline fallback)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
