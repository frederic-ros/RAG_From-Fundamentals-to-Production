# ch23-retrieval-as-tool — Retrieval Becomes a Tool Call

Labs for Chapter 23 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 23, which operates the most structuring reversal of the book: the search is no longer a fixed step executed before the generation, it becomes a tool that the model calls, in a loop, when it needs it, plan, retrieve, reflect, start again, with an "enough?" judgment borne on its own result. The five labs give body to this switch. You first build the ReAct loop, thought, action, observation, by exposing the search as a tool, with a "brain" that decides to relaunch or answer; this brain is a rule-function, and it is all the interest: the loop already works, and the day a real LLM replaces it, its structure does not change (Lab 23-1). You then standardize the call with a minimal MCP server: a client discovers then invokes the tool without knowing its implementation, and you change the search backend without touching the client (Lab 23-2). You then place the systems on the predefined / agentic slider, by opposing the multi-query to Self-RAG (Lab 23-3). You confront the counterpart of the loop: without a safeguard, it would turn endlessly on a question without an answer, hence the iteration budget and the stopping condition, up to the honest admission "unfindable" (Lab 23-4). You finish on the instability: autonomy introduces variance, which you measure then reduce (Lab 23-5). The through-line follows Julien (maintenance, pumps P-12 / P-42 / P-88, motor M-18). Two levels of realism, without an API key: the retrieval relies on a deterministic TF-IDF base (or sentence-transformers if it is present), and the brain of the loop runs on a real local LLM (Ollama) if it is available, otherwise on a deterministic rule-function, the loop, itself, staying strictly the same.

## Labs

1. **Lab 23-1 — Retrieval exposed as a tool: the ReAct loop**
2. **Lab 23-2 — MCP: exposing your retrieval as a standard tool**
3. **Lab 23-3 — Predefined versus agentic reasoning**
4. **Lab 23-4 — The counterpart: iteration budget and stopping condition**
5. **Lab 23-5 — The instability of the agent: measuring then reducing the variance**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab23-1_react_loop.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `agentlib.py`

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
