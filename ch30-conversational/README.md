# ch30-conversational — Conversational RAG: understanding the question in its context

Labs for Chapter 30 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 30, which moves the RAG from a static system, one question, one answer, to a robust conversational system. The whole difficulty holds in one idea: a human conversation is not a good search query. "And him?", "and for the trainees?" are limpid between humans and perfectly opaque for an index. The five labs unroll the answer. You start from the diagnosis: the anaphora and the ellipses make the vector retrieval collapse, not by weakness of the embedding model, but because the sent query has lost its anchoring (Lab 30-1). You then code the central block, an autonomous reformulator that reconstructs the intention from the history, "Who supplies it?" becomes "Who is the supplier of the valve V-7?" (Lab 30-2). You then compare five memory strategies on cost and robustness, discovering that memory and retrieval are two distinct problems (Lab 30-3). You avoid searching at each turn thanks to a conversational router that distinguishes chitchat, follow-up, and new search (Lab 30-4). Finally, you reach the optimal solution for a structured domain: the semantic state memory, which resolves the late anaphora of a long conversation for a fraction of the cost of the raw history (Lab 30-5). The through-line follows Karim, maintenance technician, and Julien, architect. Without an API key: deterministic TF-IDF retrieval (or sentence-transformers), reformulation, routing and state by deterministic rules (or a local LLM via Ollama, for example Mistral), the thesis of the chapter staying visible, offline and reproducible.

## Labs

1. **Lab 30-1 — Anaphora and ellipses: the challenge of the multi-turn**
2. **Lab 30-2 — Contextual autonomous reformulator**
3. **Lab 30-3 — Memory strategies: window vs summary vs state**
4. **Lab 30-4 — Conversational router: not searching at each turn**
5. **Lab 30-5 — Long conversation with semantic state memory**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab30-1_anaphora_ellipses.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `chatkit.py`

## Dependencies

```
numpy>=1.24.0          # vectors and metrics
scikit-learn>=1.3.0    # TF-IDF (mode hors-ligne)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
