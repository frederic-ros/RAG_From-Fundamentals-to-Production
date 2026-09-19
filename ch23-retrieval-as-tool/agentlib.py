# -*- coding: utf-8 -*-
"""
agentlib.py — the shared building blocks of Chapter 23 (retrieval becomes a tool).

The chapter performs a reversal: search is no longer a fixed STEP run before the
generation, it is a TOOL the model calls, in a LOOP, when it needs to. Plan ->
retrieve -> think -> retrieve again, with a judgement of "enough?" passed on its
own result. That is the ReAct loop: Thought, Action, Observation.

This module supplies, transparently:

  - Search      : the retrieval engine of the previous part (TF-IDF by default,
                  or sentence-transformers if present);
  - SearchTool  : the search EXPOSED AS A TOOL — name, description, schema, call
                  log. The central object of the chapter;
  - THE BRAIN   : the function that decides, at each turn, whether to search
                  again or to answer. Ollama (a real local LLM) if present,
                  otherwise a deterministic rule function — the loop itself does
                  not change;
  - react_loop(): the loop "plan -> retrieve -> judge -> relaunch", bounded by an
                  iteration budget and a stopping condition;
  - multi_query(): the SCRIPTED loop, with reformulations decided in advance;
  - self_rag()  : the REFLEXIVE loop, where the model judges its own answer;
  - a minimal in-process MCP SERVER: a declarative tool registry, to make the
    "standard socket" of tool calling concrete;
  - METRICS: mrr(), recall_at_k(), rank_of(), coverage().

As close to real usage as possible
----------------------------------
As in Chapter 22, two levels of realism, and never an API key:

  * RETRIEVAL: sentence-transformers if present, otherwise deterministic TF-IDF;
  * THE BRAIN: Ollama (a local model, llama3.2 for instance) if present — the
    model really PLANS and JUDGES — otherwise a deterministic rule function.

The teaching thesis of the labs: "the day an LLM replaces the rule, the loop does
not change". It is demonstrated by keeping exactly the same loop, whether the
rule or Ollama is plugged in.

A NOTE ON THE ACTION KEYWORD. The LLM brain is asked to answer either "STOP" or
"SEARCH: <query>", and the parser below looks for that same word. The two must
stay in step: translate the prompt without the regex, or the reverse, and the
brain falls back to the rule on every turn — silently, since a fallback is
provided.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# Optional detection of the engines (embeddings plus a local LLM)
# ===========================================================================
_ST_MODEL = None
_MODE = None


def mode_retrieval() -> str:
    global _ST_MODEL, _MODE
    if _MODE is not None:
        return _MODE
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2")
        m.encode(["test"])
        _ST_MODEL, _MODE = m, "sentence-transformers"
    except Exception:
        _MODE = "tfidf"
    return _MODE


_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
_OLLAMA_OK: Optional[bool] = None


def ollama_available() -> bool:
    global _OLLAMA_OK
    if _OLLAMA_OK is not None:
        return _OLLAMA_OK
    try:
        import ollama  # noqa: F401
        ollama.chat(model=_OLLAMA_MODEL,
                    messages=[{"role": "user", "content": "ping"}],
                    options={"num_predict": 1, "temperature": 0.0})
        _OLLAMA_OK = True
    except Exception:
        _OLLAMA_OK = False
    return _OLLAMA_OK


def mode_brain() -> str:
    """The mode of the loop's "brain": 'ollama' (a real LLM) or 'rule'."""
    return "ollama" if ollama_available() else "rule"


def _llm(prompt: str, *, temperature: float = 0.0, num_predict: int = 128) -> str:
    import ollama
    r = ollama.chat(model=_OLLAMA_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": temperature, "num_predict": num_predict})
    return r["message"]["content"].strip()


# ===========================================================================
# The search engine (retrieval) — identical to the previous part
# ===========================================================================
class Search:
    def __init__(self, corpus: Sequence[str]) -> None:
        self.corpus = list(corpus)
        self.mode = mode_retrieval()
        if self.mode == "sentence-transformers":
            self._vecs = _ST_MODEL.encode(self.corpus, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                        token_pattern=r"(?u)\b\w+\b")
            self._mat = self._vec.fit_transform(self.corpus)

    def scores(self, query: str) -> np.ndarray:
        if self.mode == "sentence-transformers":
            q = _ST_MODEL.encode([query], normalize_embeddings=True)[0]
            return self._vecs @ q
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([query])
        return cosine_similarity(q, self._mat)[0]

    def rank(self, query: str, k: Optional[int] = None,
             noise: float = 0.0, seed: Optional[int] = None
             ) -> List[Tuple[int, float]]:
        s = self.scores(query).astype(float)
        if noise > 0.0:
            rng = np.random.default_rng(seed)
            s = s + rng.normal(0.0, noise, size=s.shape)
        ordre = np.argsort(-s)
        res = [(int(i), float(s[i])) for i in ordre]
        return res[:k] if k else res


# ===========================================================================
# THE TOOL: search exposed as a callable tool
# ===========================================================================
@dataclass
class SearchTool:
    """The search, exposed as a TOOL — the central object of the chapter.

    A tool is: a name, a description, a schema of parameters (what a model reads
    to know when and how to call it), and a function. Every call is logged: that
    log is the TRACE the labs display — which key was used at each turn.
    """
    search: Search
    fragments: List[dict]
    name: str = "document_search"
    description: str = ("Searches the technical corpus and returns the most "
                        "relevant excerpts. Parameter: 'query' (str).")
    schema: Dict = field(default_factory=lambda: {
        "type": "object",
        "properties": {"query": {"type": "string",
                                 "description": "The search query."}},
        "required": ["query"],
    })
    log: List[dict] = field(default_factory=list)

    def call(self, query: str, k: int = 3) -> List[dict]:
        """Invoke the tool: return the top-k fragments, and log the call."""
        order = self.search.rank(query, k=k)
        results = [{"id": self.fragments[i]["id"],
                    "subject": self.fragments[i]["subject"],
                    "text": self.fragments[i]["text"],
                    "score": round(s, 3)} for i, s in order]
        self.log.append({"query": query,
                         "results": [r["subject"] for r in results]})
        return results

    def reset(self) -> None:
        self.log.clear()


# ===========================================================================
# THE BRAIN — decides, at each turn, whether to relaunch or to answer
# ===========================================================================
# The brain receives the question, the list of expected facets, and the context
# gathered so far. It returns a DECISION: either ("STOP", None) or
# ("SEARCH", query). Two interchangeable implementations, rule or LLM, for the
# same loop.

def _tokens(t: str) -> List[str]:
    return re.findall(r"\w+", t.lower())


def rule_brain(question: str, facets: Sequence[str],
               context: Sequence[dict]) -> Tuple[str, Optional[str]]:
    """A deterministic brain: are all the facets covered? If not, target the gap.

    This is the labs' "rule function": a brain with no LLM, and it is enough to
    drive the ReAct loop. The day an LLM replaces it, the loop does not change.

    The coverage test is a substring match on equipment CODES ("P-42"), which is
    why it survives translation untouched. Only the query it formulates is
    language-bound.
    """
    ctx_text = " ".join(c["text"] for c in context).lower()
    missing = [v for v in facets if v.lower() not in ctx_text]
    if not missing:
        return ("STOP", None)
    target = missing[0]
    # Formulate a query aimed at the missing facet.
    if re.match(r"p-?\d+", target.lower()):
        return ("SEARCH", f"emergency stop pump {target}")
    return ("SEARCH", f"{question.split()[0]} {target}")


def llm_brain(question: str, facets: Sequence[str],
              context: Sequence[dict]) -> Tuple[str, Optional[str]]:
    """The LLM brain (Ollama): the model judges coverage and formulates the next key.

    The same signature as `rule_brain`: the loop cannot tell the difference.

    THE ACTION KEYWORD "SEARCH:" APPEARS IN BOTH the prompt and the regex below.
    Change one without the other and this function silently falls back to the
    rule brain on every turn: the loop still runs, the output still looks right,
    but the LLM is never actually used.
    """
    ctx = "\n".join(f"- {c['text']}" for c in context) or "(empty)"
    prompt = (
        "You are driving a document search loop. Here is the question, the "
        "subjects to cover, and the context gathered so far.\n\n"
        f"Question: {question}\n"
        f"Subjects to cover: {', '.join(facets)}\n"
        f"Context gathered:\n{ctx}\n\n"
        "If ALL the subjects are covered by the context, answer STRICTLY: STOP\n"
        "Otherwise, answer STRICTLY with a search query aimed at ONE missing "
        "subject, in the form: SEARCH: <query>\n"
    )
    verdict = _llm(prompt, temperature=0.0, num_predict=40)
    if verdict.strip().upper().startswith("STOP"):
        return ("STOP", None)
    m = re.search(r"SEARCH\s*:\s*(.+)", verdict, re.IGNORECASE)
    if m:
        return ("SEARCH", m.group(1).strip())
    # A cautious fallback if the model deviates from the format.
    return rule_brain(question, facets, context)


def active_brain() -> Callable:
    """Return the brain to use: the LLM if available, otherwise the rule."""
    return llm_brain if ollama_available() else rule_brain


# ===========================================================================
# THE ReAct LOOP — plan, retrieve, judge, relaunch, and bounded
# ===========================================================================
def react_loop(question: str, facets: Sequence[str], tool: SearchTool,
               budget: int = 4, brain: Optional[Callable] = None, k: int = 3
               ) -> dict:
    """The "Thought / Action / Observation" loop, bounded by an iteration budget.

    At each turn: the brain formulates a THOUGHT and a decision, the tool is
    ACTIONED (the observation), the result accumulates, and judgement is passed.
    The loop exits as soon as the brain says STOP (the stopping condition) or the
    budget is exhausted.

    Returns a dict: the trace of the turns, the final context, the reason for
    exiting, and the cost.
    """
    brain = brain or active_brain()
    tool.reset()
    context: List[dict] = []
    seen = set()
    trace: List[dict] = []
    query = question          # the first turn: the whole question
    thought = "first search on the whole question"

    for turn in range(1, budget + 1):
        # ACTION plus OBSERVATION
        obs = tool.call(query, k=k)
        fresh = next((r for r in obs if r["subject"] not in seen), obs[0])
        if fresh["subject"] not in seen:
            context.append(fresh)
            seen.add(fresh["subject"])
        # JUDGEMENT: the brain decides what follows
        decision, next_query = brain(question, facets, context)
        trace.append({"turn": turn, "thought": thought, "query": query,
                      "observation": fresh["subject"], "decision": decision,
                      "next": next_query})
        if decision == "STOP":
            return {"trace": trace, "context": context,
                    "exit": "stopping condition", "cost": turn}
        query = next_query
        thought = f"a subject is missing — target \"{next_query}\""

    return {"trace": trace, "context": context, "exit": "budget exhausted",
            "cost": budget}


# ===========================================================================
# THE SCRIPTED LOOP — multi-query (reformulations decided in advance)
# ===========================================================================
def multi_query(question: str, facets: Sequence[str], tool: SearchTool,
                k: int = 3, n_reformulations: int = 3) -> dict:
    """PREDEFINED reasoning: a FIXED NUMBER of reformulations is generated in
    advance, all of them are run, and the results merged.

    The number of searches is FIXED beforehand — `n_reformulations`, or one per
    facet if the question is explicitly multi-facet. None depends on the result
    of the previous one; no judgement is passed between turns. This is the
    assumed "waste" of the predefined approach: it pays the same price whether
    the question is simple or complex.
    """
    tool.reset()
    if len(facets) > 1:
        # An explicitly multi-facet question: one targeted reformulation per facet.
        queries = [f"emergency stop pump {v}" if re.match(r"p-?\d+", v.lower())
                   else f"{question.split()[0]} {v}" for v in facets]
    else:
        # A simple question: N reformulations are generated anyway, blind.
        base = question.rstrip(" ?.")
        queries = [question,
                   f"procedure {base}",
                   f"detailed steps: {base}"][:n_reformulations]
    context, seen = [], set()
    for r in queries:
        for res in tool.call(r, k=k):
            if res["subject"] not in seen:
                context.append(res)
                seen.add(res["subject"])
                break
    return {"queries": queries, "context": context, "cost": len(queries)}


# ===========================================================================
# THE REFLEXIVE LOOP — Self-RAG (the model judges its own answer)
# ===========================================================================
def self_rag(question: str, facets: Sequence[str], tool: SearchTool,
             budget: int = 4, brain: Optional[Callable] = None, k: int = 3) -> dict:
    """Reflexive RAG: structurally this IS `react_loop` — the decision to relaunch
    belongs to the BRAIN, which judges coverage, not to a script.

    It is distinguished from multi_query for the sake of the argument, but the
    mechanism is indeed the judged loop.
    """
    res = react_loop(question, facets, tool, budget=budget, brain=brain, k=k)
    res["regime"] = "reflexive (the model decides)"
    return res


# ===========================================================================
# A minimal in-process MCP SERVER — the "standard socket"
# ===========================================================================
class MCPServer:
    """A declarative tool registry, minimal and in-process, in the manner of MCP.

    MCP does not replace RAG: it STANDARDISES the call. The server exposes the
    tools (name, description, schema); a client DISCOVERS them (list_tools) and
    INVOKES them (call_tool) without knowing their implementation. This is the
    "principle" version: no network, no transport — just the declarative surface
    and the decoupling.
    """

    def __init__(self, name: str = "retrieval-server") -> None:
        self.name = name
        self._tools: Dict[str, dict] = {}
        self.log: List[dict] = []

    def register(self, name: str, description: str, schema: dict,
                 function: Callable) -> None:
        self._tools[name] = {"name": name, "description": description,
                             "schema": schema, "function": function}

    def list_tools(self) -> List[dict]:
        """Discovery: what a client sees, without the functions."""
        return [{"name": o["name"], "description": o["description"],
                 "schema": o["schema"]} for o in self._tools.values()]

    def call_tool(self, name: str, arguments: dict):
        """Invocation: the client calls by NAME, knowing no implementation."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        self.log.append({"tool": name, "arguments": arguments})
        return self._tools[name]["function"](**arguments)


# ===========================================================================
# Metrics and helpers
# ===========================================================================
def coverage(context: Sequence[dict], facets: Sequence[str]) -> Tuple[float, List[str]]:
    """The share of the expected facets present in the context gathered."""
    text = " ".join(c["text"] for c in context).lower()
    missing = [v for v in facets if v.lower() not in text]
    return ((len(facets) - len(missing)) / max(1, len(facets)), missing)


def rank_of(ranking: Sequence[int], doc: int) -> Optional[int]:
    for r, d in enumerate(ranking, start=1):
        if d == doc:
            return r
    return None
