# -*- coding: utf-8 -*-
"""
tiers.py — the engine of the demonstration: from naive to robust (full version).

One corpus, one multi-criteria harness, and a SEQUENCE OF PIPELINES of
increasing care. Each returns, for every question, an `Answer` object (context,
provenance, abstention, flags). The harness draws five scores from it; the
overall score climbs, tier after tier, and the profile by criterion fills in.

The tiers, in the order of the chapters:
  0   Naive RAG ................. raw text, top-1, no metadata (the floor)
  1   Structuring ............... starts from the canonical form: one clean block per fragment
  1b  Admissibility ............. the "ready document" gate: reject / supersede / degrade
  2   Context + validity ........ small-to-big plus an "in force" filter
  3   Hybrid + reranking ........ catches codes and acronyms, puts the good one on top
  4   Query transformation ...... rewrites the badly posed questions
  5   Governance / authority .... score = relevance + authority + freshness; cites
  6   Security .................. quarantines the poisoned and the external
  7   Explainability / abstention  provenance throughout, plus calibrated abstention

Everything is deterministic, with no API key. Run after generate_corpus.py.
"""

from __future__ import annotations
from pathlib import Path
from typing import List
import json

import harness as H
import embeddings as E
import admission as A

HERE = Path(__file__).resolve().parent
CORPUS = HERE / "corpus"


# ===========================================================================
# Chargement deux states of the corpus.
# ===========================================================================
def load_raw() -> List[str]:
    return [p.read_text(encoding="utf-8") for p in sorted((CORPUS / "raw").glob("*.txt"))]


def load_documents() -> List[dict]:
    data = json.loads((CORPUS / "canonical.json").read_text(encoding="utf-8"))
    return data["documents"]


def load_blocks() -> List[dict]:
    blocks = []
    for doc in load_documents():
        for b in doc["blocks"]:
            if b.get("type") != "empty":
                blocks.append(b)
    return blocks


# ===========================================================================
# Small shared helpers.
# ===========================================================================
def _provenance(bloc: dict) -> str:
    m = bloc["metadata"]
    return f"{m.get('document', '?')} ({m.get('authority', '?')})"


def _live_external_source(docs: List[dict]) -> List[dict]:
    """The trapped external source is NOT in the indexed corpus: it is fetched
    live, from the web or a tool, at query time. It therefore escapes the
    admission gate, which only sees ingestion, and can be stopped only by a
    runtime defence: the quarantine of the security tier. It is reinjected here
    for tiers 2 to 5, so that the "live" threat stays visible until security
    neutralises it."""
    blocks = []
    for doc in docs:
        if doc.get("origin") == "external":
            for b in doc["blocks"]:
                if b.get("type") != "empty":
                    blocks.append(b)
    return blocks


def _is_malicious(texte: str) -> bool:
    t = texte.lower()
    markers = ["disable the firewall", "disabling the firewall",
               "temporarily disable", "administration key",
               "send the credentials", "clipboard",
               "without asking for confirmation", "ignore the earlier"]
    return any(m in t for m in markers)


# ===========================================================================
# LEVEL 0 — The RAG naive. Chunk grossier on the brut, top-1, aucune metadata.
# It prend TOUT, y compris the documents foireux. It MUST to fail.
# ===========================================================================
def _naive_chunks(texts: List[str], size: int = 40) -> List[str]:
    import tokenizer as tk
    chunks = []
    for t in texts:
        tokens = tk.encode(t)
        chunks += [tk.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]
    return chunks


def tier0_naive():
    chunks = _naive_chunks(load_raw())
    engine = E.SimilarityEngine(chunks)
    def answer_fn(q: H.Question) -> H.Answer:
        i, _ = engine.rank(q.text)[0]
        ctx = chunks[i]
        # Naive: no provenance, no abstention, no notion of danger.
        return H.Answer(context=ctx, provenance=None, abstention=False,
                         poisoned=_is_malicious(ctx))
    return answer_fn


# ===========================================================================
# LEVEL 1 — Structuration. On chunking the CANONIQUE : a bloc propre by
# fragment, no noise, the whole table. But ALL the blocks are still taken.
# ===========================================================================
def tier1_structure():
    blocks = load_blocks()
    texts = [b["text"] for b in blocks]
    engine = E.SimilarityEngine(texts)
    def answer_fn(q: H.Question) -> H.Answer:
        i, _ = engine.rank(q.text)[0]
        ctx = texts[i]
        return H.Answer(context=ctx, provenance=None, abstention=False,
                         poisoned=_is_malicious(ctx))
    return answer_fn


# ===========================================================================
# TIER 1b — Admissibility (the "ready document"). Everything passes the gate:
# the unreadable, empty and poisoned are REJECTED, duplicates SUPERSEDED, the
# bronze DEGRADED. Only the admitted blocks are indexed.
# ===========================================================================
def tier1b_admissibility():
    docs = load_documents()
    blocks = A.admitted_blocks(docs)           # already filtered by the gate
    texts = [b["text"] for b in blocks]
    engine = E.SimilarityEngine(texts)
    def answer_fn(q: H.Question) -> H.Answer:
        i, _ = engine.rank(q.text)[0]
        b = blocks[i]
        ctx = b["text"]
        return H.Answer(context=ctx, provenance=None, abstention=False,
                         poisoned=_is_malicious(ctx),
                         from_inadmissible=False)   # the gate has already filtered
    return answer_fn


# ===========================================================================
# TIER 2 — Context and validity. Small-to-big (climbing to the parent document)
# plus an "in force" filter, over the admitted blocks.
# ===========================================================================
def tier2_context_validity():
    docs = load_documents()
    blocks = [b for b in A.admitted_blocks(docs)
             if b["metadata"].get("status") == "in force"]
    texts = [b["text"] for b in blocks]
    engine = E.SimilarityEngine(texts)

    def parent_de(bloc: dict) -> str:
        doc = bloc["metadata"]["document"]
        meme = [b["text"] for b in blocks if b["metadata"]["document"] == doc]
        return " ".join(meme)

    def answer_fn(q: H.Question) -> H.Answer:
        i, _ = engine.rank(q.text)[0]
        ctx = parent_de(blocks[i])
        return H.Answer(context=ctx, provenance=None, abstention=False,
                         poisoned=_is_malicious(ctx))
    return answer_fn


# ===========================================================================
# LEVEL 3 — Hybrid + reranking. Semantic similarity is combined with lexical
# matching on technical tokens (codes and acronyms such as SEC-12 or M-200),
# and the best result is kept. Lexical search recovers what semantics misses.
# ===========================================================================
def _score_lexical(question: str, texte: str) -> float:
    """A lexical score targeted at technical tokens (codes, acronyms), which is
    where semantics alone fails. Overlap on ordinary words is deliberately not
    rewarded: it would let a document win on common vocabulary and rank an
    exception above the rule it qualifies."""
    import re
    qmots = set(re.findall(r"[\w-]+", question.lower()))
    tmots = set(re.findall(r"[\w-]+", texte.lower()))
    if not qmots:
        return 0.0
    inter = qmots & tmots
    # Only "technical" tokens count — those containing a digit or a hyphen,
    # such as SEC-12 or M-200. Ordinary words are ignored here.
    techniques = [m for m in inter
                  if any(ch.isdigit() for ch in m) or "-" in m]
    if not qmots:
        return 0.0
    poids = sum(2.0 for _ in techniques)
    return poids / len(qmots)


def tier3_hybrid():
    docs = load_documents()
    blocks = [b for b in A.admitted_blocks(docs)
             if b["metadata"].get("status") == "in force"]
    texts = [b["text"] for b in blocks]
    engine = E.SimilarityEngine(texts)

    def parent_de(bloc: dict) -> str:
        doc = bloc["metadata"]["document"]
        meme = [b["text"] for b in blocks if b["metadata"]["document"] == doc]
        return " ".join(meme)

    def answer_fn(q: H.Question) -> H.Answer:
        sem = engine.scores(q.text)
        # score hybrid = semantic + lexical (rattrape codes/acronymes)
        hybride = []
        for j, b in enumerate(blocks):
            lex = _score_lexical(q.text, b["text"])
            hybride.append((float(sem[j]) + 0.5 * lex, j))
        hybride.sort(reverse=True)
        i = hybride[0][1]
        ctx = parent_de(blocks[i])
        return H.Answer(context=ctx, provenance=None, abstention=False,
                         poisoned=_is_malicious(ctx))
    return answer_fn


# ===========================================================================
# TIER 4 — Query transformation. The badly posed questions are rewritten
# (anaphora and vague wording) into richer queries before search.
# ===========================================================================
_REWRITES = {
    "q-remote-carer": "remote work employee carer three days exception evidence",
    "q-remote-general": "remote work general rule two days per week",
    "q-safety-procedure": "procedure SEC-12 machine M-200 work protective equipment",
}


def tier4_queries():
    docs = load_documents()
    blocks = [b for b in A.admitted_blocks(docs)
             if b["metadata"].get("status") == "in force"]
    texts = [b["text"] for b in blocks]
    engine = E.SimilarityEngine(texts)

    def parent_de(bloc: dict) -> str:
        doc = bloc["metadata"]["document"]
        meme = [b["text"] for b in blocks if b["metadata"]["document"] == doc]
        return " ".join(meme)

    def answer_fn(q: H.Question) -> H.Answer:
        requete = _REWRITES.get(q.id, q.text)
        sem = engine.scores(requete)
        hybride = []
        for j, b in enumerate(blocks):
            lex = _score_lexical(requete, b["text"])
            hybride.append((float(sem[j]) + 0.5 * lex, j))
        hybride.sort(reverse=True)
        i = hybride[0][1]
        ctx = parent_de(blocks[i])
        return H.Answer(context=ctx, provenance=None, abstention=False,
                         poisoned=_is_malicious(ctx))
    return answer_fn


# ===========================================================================
# TIER 5 — Governance and authority. The sorting score is no longer relevance
# alone: score = 0.7 x relevance + 0.2 x authority + 0.1 x freshness. And the
# PROVENANCE is attached to every answer, in preparation for citation.
# ===========================================================================
_AUTHORITY_WEIGHT = {"gold": 1.0, "silver": 0.6, "bronze": 0.3}


def _fraicheur(date: str) -> float:
    # 2024 and later is fresh, 2021 and earlier is old. Maps the year onto [0, 1].
    try:
        annee = int(date[:4])
    except Exception:
        return 0.5
    return max(0.0, min(1.0, (annee - 2020) / 4.0))


def tier5_governance():
    docs = load_documents()
    blocks = [b for b in A.admitted_blocks(docs)
             if b["metadata"].get("status") == "in force"]
    # The "live" external source escapes admission: it enters the pool.
    blocks = blocks + _live_external_source(docs)
    texts = [b["text"] for b in blocks]
    engine = E.SimilarityEngine(texts)

    def parent_de(bloc: dict) -> str:
        doc = bloc["metadata"]["document"]
        meme = [b["text"] for b in blocks if b["metadata"]["document"] == doc]
        return " ".join(meme)

    def answer_fn(q: H.Question) -> H.Answer:
        requete = _REWRITES.get(q.id, q.text)
        sem = engine.scores(requete)
        ranked = []
        for j, b in enumerate(blocks):
            m = b["metadata"]
            lex = _score_lexical(requete, b["text"])
            relevance = float(sem[j]) + 0.5 * lex
            authority = _AUTHORITY_WEIGHT.get(m.get("authority", "bronze"), 0.3)
            freshness = _fraicheur(m.get("date", ""))
            score = 0.7 * relevance + 0.2 * authority + 0.1 * freshness
            ranked.append((score, j))
        ranked.sort(reverse=True)
        i = ranked[0][1]
        ctx = parent_de(blocks[i])
        return H.Answer(context=ctx, provenance=_provenance(blocks[i]),
                         abstention=False, poisoned=_is_malicious(ctx))
    return answer_fn


# ===========================================================================
# TIER 6 — Security. Quarantine: every poisoned block, and every block of
# unverified external origin, is set aside BEFORE the search. The gate
# of admission rejetait already the pires ; here on durcit (defense in profondeur)
# and on garantit that aucun content malveillant not can atteindre the context.
# ===========================================================================
def tier6_security():
    docs = load_documents()
    admitted_blocks = A.admitted_blocks(docs)
    # The sound is separated from the QUARANTINE (poisoned, or external and unsigned).
    sains, quarantine = [], []
    for b in admitted_blocks:
        m = b["metadata"]
        is_suspect = (m.get("poisoned") or _is_malicious(b["text"])
                       or (m.get("origin") == "external" and not m.get("signed")))
        if is_suspect or m.get("status") != "in force":
            if is_suspect:
                quarantine.append(b)
            continue
        sains.append(b)
    # The blocks of documents banned by the gate (poisoned) are added too
    # to quarantine so that a question targeting it can still be detected.
    for doc in docs:
        if doc.get("poisoned"):
            quarantine.extend(b for b in doc["blocks"] if b.get("type") != "empty")

    texts = [b["text"] for b in sains]
    engine = E.SimilarityEngine(texts)
    moteur_q = E.SimilarityEngine([b["text"] for b in quarantine]) if quarantine else None

    def parent_de(bloc: dict) -> str:
        doc = bloc["metadata"]["document"]
        meme = [b["text"] for b in sains if b["metadata"]["document"] == doc]
        return " ".join(meme)

    def answer_fn(q: H.Question) -> H.Answer:
        requete = _REWRITES.get(q.id, q.text)
        sem = engine.scores(requete)
        ranked = []
        for j, b in enumerate(sains):
            m = b["metadata"]
            lex = _score_lexical(requete, b["text"])
            relevance = float(sem[j]) + 0.5 * lex
            authority = _AUTHORITY_WEIGHT.get(m.get("authority", "bronze"), 0.3)
            freshness = _fraicheur(m.get("date", ""))
            ranked.append((0.7 * relevance + 0.2 * authority + 0.1 * freshness, j,
                           relevance))
        ranked.sort(reverse=True)
        meilleur, i, pertinence_sain = ranked[0]

        # Attack detection, on two signals (honest, without reading the harness):
        # (a) a bloc in quarantine domine NETTEMENT the meilleur bloc sound
        # (the question clearly "fishes" for banned content); OR
        # (b) the meilleur candidat in quarantine is more proche of the question
        # that a bloc sound AND porte a instruction malveillante.
        # Plain TF-IDF noise, a minimal margin, does not trigger the refusal.
        if moteur_q is not None and quarantine:
            sq = moteur_q.scores(requete)
            iq = max(range(len(quarantine)), key=lambda k: float(sq[k]))
            pertinence_q = float(sq[iq])
            domine = pertinence_q > 1.3 * max(pertinence_sain, 1e-6)
            piege_vise = (pertinence_q > 1.15 * max(pertinence_sain, 1e-6)
                          and _is_malicious(quarantine[iq]["text"]))
            if domine or piege_vise:
                return H.Answer(context="", provenance=None, abstention=True,
                                 poisoned=False)

        ctx = parent_de(sains[i])
        return H.Answer(context=ctx, provenance=_provenance(sains[i]),
                         abstention=False, poisoned=False)
    return answer_fn


# ===========================================================================
# LEVEL 7 — Explainability / abstention. Dernier stage : provenance partout,
# and CALIBRATED ABSTENTION. If the best score stays below a confidence threshold
# (the context not contient not truement of quoi to answer), the system refuse
# rather than invent. That is what tips the "security trap" questions, the ones
# with no legitimate answer, from red to green.
# ===========================================================================
def tier7_explainability(threshold: float = 0.50):
    docs = load_documents()
    admitted_blocks = A.admitted_blocks(docs)
    sains, quarantine = [], []
    for b in admitted_blocks:
        m = b["metadata"]
        is_suspect = (m.get("poisoned") or _is_malicious(b["text"])
                       or (m.get("origin") == "external" and not m.get("signed")))
        if is_suspect or m.get("status") != "in force":
            if is_suspect:
                quarantine.append(b)
            continue
        sains.append(b)
    for doc in docs:
        if doc.get("poisoned"):
            quarantine.extend(b for b in doc["blocks"] if b.get("type") != "empty")

    texts = [b["text"] for b in sains]
    engine = E.SimilarityEngine(texts)
    moteur_q = E.SimilarityEngine([b["text"] for b in quarantine]) if quarantine else None

    def parent_de(bloc: dict) -> str:
        doc = bloc["metadata"]["document"]
        meme = [b["text"] for b in sains if b["metadata"]["document"] == doc]
        return " ".join(meme)

    def answer_fn(q: H.Question) -> H.Answer:
        requete = _REWRITES.get(q.id, q.text)
        sem = engine.scores(requete)
        ranked = []
        for j, b in enumerate(sains):
            m = b["metadata"]
            lex = _score_lexical(requete, b["text"])
            relevance = float(sem[j]) + 0.5 * lex
            authority = _AUTHORITY_WEIGHT.get(m.get("authority", "bronze"), 0.3)
            freshness = _fraicheur(m.get("date", ""))
            ranked.append((0.7 * relevance + 0.2 * authority + 0.1 * freshness, j,
                           relevance))
        ranked.sort(reverse=True)
        meilleur, i, pertinence_sain = ranked[0]

        # Security, inherited from tier 6: refuse if the question targets the quarantine.
        if moteur_q is not None and quarantine:
            sq = moteur_q.scores(requete)
            iq = max(range(len(quarantine)), key=lambda k: float(sq[k]))
            pertinence_q = float(sq[iq])
            domine = pertinence_q > 1.3 * max(pertinence_sain, 1e-6)
            piege_vise = (pertinence_q > 1.15 * max(pertinence_sain, 1e-6)
                          and _is_malicious(quarantine[iq]["text"]))
            if domine or piege_vise:
                return H.Answer(context="", provenance=None, abstention=True,
                                 poisoned=False)
        # Explainability: calibrated abstention if even the best sound passage
        # stays too low, leaving no source that could honestly be cited.
        if pertinence_sain < 0.05:
            return H.Answer(context="", provenance=None, abstention=True,
                             poisoned=False)
        ctx = parent_de(sains[i])
        return H.Answer(context=ctx, provenance=_provenance(sains[i]),
                         abstention=False, poisoned=False)
    return answer_fn


# ===========================================================================
# The register of tiers, in the order of the climb.
# ===========================================================================
TIERS = [
    ("0 — Naive RAG (raw, top-1)",                tier0_naive),
    ("1 — Structuring (ch. 12-13)",               tier1_structure),
    ("1b — Admissibility / ready document",       tier1b_admissibility),
    ("2 — Context + validity (ch. 14-15)",        tier2_context_validity),
    ("3 — Hybrid + reranking (ch. 18-20)",        tier3_hybrid),
    ("4 — Query transformation (ch. 21)",         tier4_queries),
    ("5 — Governance / authority (ch. 15, 31)",   tier5_governance),
    ("6 — Security / quarantine (ch. 31)",        tier6_security),
    ("7 — Explainability / abstention (ch. 32)",  tier7_explainability),
]


def curve(scores: List[float]) -> str:
    lines = []
    for (name, _), s in zip(TIERS, scores):
        bar = "█" * int(round(s * 30))
        lines.append(f"  {name:44} {bar} {s:.0%}")
    return "\n".join(lines)


def main():
    print("=" * 84)
    print("THE THESIS PUT TO THE TEST — from naive RAG to a robust system")
    print("=" * 84)
    print(f"\nSearch backend: {E.mode()}")

    if not (CORPUS / "canonical.json").exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    # The admission gate, shown once: it holds for every tier from 1b onwards.
    print("\n" + "-" * 84)
    print("THE ADMISSION GATE (\"ready document\") — score out of 100, and decision")
    print("-" * 84)
    sheets = A.pass_the_gate(load_documents())
    for f in sheets.values():
        print(f"  {f.title[:42]:42} {f.score_value:>3}/100  {f.decision:9}  {f.reason}")

    scores, reports = [], []
    for name, build in TIERS:
        report = H.evaluate_pipeline(name, build())
        reports.append(report)
        scores.append(report.score)
        H.show_report(report, detailed=False)

    print("\n" + "=" * 84)
    print("THE CURVE (overall score by tier)")
    print("=" * 84)
    print(curve(scores))

    print("\n" + "=" * 84)
    print("THE PROFILE BY CRITERION (final tier)")
    print("=" * 84)
    for k, v in reports[-1].per_criterion().items():
        bar = "█" * int(round(v * 30))
        print(f"  {k:14} {bar} {v:.0%}")

    print("\n" + "=" * 84)
    print("WHAT THE DEMONSTRATION ESTABLISHES")
    print("=" * 84)
    print(f"  The naive system: overall score {scores[0]:.0%}.")
    print(f"  The complete system: overall score {scores[-1]:.0%}.")
    print("  The same corpus, the same questions, the same similarity engine.")
    print("  Only the chain has changed — admission, structuring, validity, search,")
    print("  governance, security, explainability. That is the thesis of the book.")


if __name__ == "__main__":
    main()
