# ch21-query-transformation — Query Transformation

Labs for Chapter 21 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 21, which tackles a misunderstanding: the question and the document that answers it are not written in the same language. The user speaks the language of the problem ("it makes a weird noise"); the document, that of the solution ("vibratory signature of a bearing defect"). The raw question is thus a bad key, and the whole parry consists of transforming it before searching. The six labs follow the rise of the chapter, from the problem toward the tool. You first observe the mismatch: the good document exists, the retrieval works, but the question ranks it far (Lab 21-1). You then discover the most counterintuitive transformation, HyDE: inventing a false answer, because it already speaks the language of the real documents, and searching with it (Lab 21-2). You explore the more sober transformations: the decomposition, which cuts a composed question into sub-questions (Lab 21-3), and the conversational rewriting, which resolves the pronouns ("its," "it") by reinjecting the thread of the dialogue (Lab 21-4). You assemble everything in an adaptive router that chooses the good transformation according to the type of question (Lab 21-5). A bonus lab finally draws up a complete benchmark: no transformation is universally better, and the router dominates the single methods for a lower cost (Lab 21-6). The through-line follows Julien (maintenance), motor M-18, pumps A/B, pump P-42. Without an API key, the retrieval relies on a deterministic TF-IDF base (or sentence-transformers if it is present), and the transformations are simulated by rules and vocabulary templates: the pedagogical point of each appears clearly, offline and in a reproducible way.

## Labs

1. **Lab 21-1 — Julien asks the wrong question**
2. **Lab 21-2 — HyDE: searching for the answer rather than the question**
3. **Lab 21-3 — One question or three questions?**
4. **Lab 21-4 — The "it" trap**
5. **Lab 21-5 — Which tool to choose?**
6. **Lab 21-6 — Complete benchmark: which transformation wins? (bonus)**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab21-1_wrong_question.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `qtlib.py`

## Dependencies

```
numpy>=1.24.0          # vectors and metrics
scikit-learn>=1.3.0   # TF-IDF du retrieval en mode hors-ligne (repli)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
