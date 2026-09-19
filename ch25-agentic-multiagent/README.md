# ch25-agentic-multiagent — Agentic RAG & Multi-Agent RAG

Labs for Chapter 25 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 25, which moves the RAG from the pipeline to the agent: a system that decides itself when to search, which tools to call, when to delegate, and when to stop. The five labs keep the same corpus and the same tools so that only the thing that counts changes: the place of the decision. You first oppose a workflow (fixed sequence) to an agent (which decides at execution whether to search), same tool, same corpus, different cost (Lab 25-1). You then build the investigator agent, which decomposes a question in cascade (the pump P-42 feeds the exchanger E-7, on which the line L-3 depends) and conducts several searches for a single question (Lab 25-2). Comes the memory, treated as a block in its own right: short-term memory that resolves "and for the P-42?" by keeping the thread, and long-term memory that persists between sessions in a JSON file (Lab 25-3). The fourth lab erects a multi-agent council, Julien, Claire, Sophie, orchestrated according to the four production roles (Planner, Executor, Critic, Supervisor), where the Critic rejects the unreliable contributions and where no agent calls another directly (Lab 25-4). The last assembles everything into an autonomous industrial assistant, with an execution graph, a global budget, and safeguards (Lab 25-5). The through-lines follow Julien (maintenance), Claire (HR), and Sophie (architecture). Without an API key: the retrieval relies on a deterministic TF-IDF base (or sentence-transformers if it is present), and the brain of the agents on a local LLM (Ollama) if it runs, otherwise on deterministic rules, the thesis of the chapter staying visible, offline and in a reproducible way.

## Labs

1. **Lab 25-1 — From the workflow to the agent: "Who makes the decision?"**
2. **Lab 25-2 — The investigator agent: one question, several searches**
3. **Lab 25-3 — Short-term and long-term memory: the agent that remembers**
4. **Lab 25-4 — Multi-agent: the Council of Guardians**
5. **Lab 25-5 — Building a complete agentic system**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab25-1_workflow_vs_agent.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `agentkit.py`

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
