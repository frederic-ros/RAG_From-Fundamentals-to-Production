# -*- coding: utf-8 -*-
"""
cragkit.py — the shared building blocks of Chapter 24.

The chapter teaches a system three things: to doubt its own answer (Self-RAG), to
go and look elsewhere when it doubts (CRAG), and to spend a loop only where it
counts (Adaptive-RAG).

This module supplies:

  - reflection_tokens: the "reflection tokens" of Self-RAG (ISREL / ISSUP /
    ISUSE), plus an aggregated confidence score;
  - grader: the relevance grader of CRAG, which decides confident / ambiguous /
    not confident;
  - web_search: a SIMULATED, deterministic web fallback — a second source,
    treated as such;
  - routeur: the complexity router of Adaptive-RAG, with three paths (direct /
    single pass / iterative loop), in rule mode or LLM mode;
  - a call counter, so the cost of each architecture can be put in figures.

As close to real usage as possible
----------------------------------
The same hybrid approach as the earlier chapters, extended to JUDGEMENT and to
ROUTING: Ollama if a local model answers, otherwise deterministic rules.

The teaching point of each architecture comes out clearly OFFLINE; as soon as
Ollama is available, the real model does the judging.

A WARNING ON THE WORD LISTS. Three of them are mechanisms, not decoration: the
stop words (which feed the router's complexity count), the analysis markers and
the business entity markers. All three are matched against the text of the
questions and must stay in step with generate_corpus.py. Lab 24-4 prints the
routing decision against the expectation for all nine questions: run it after any
edit.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# Detection optionnelle moteurs (embeddings + LLM local)
# ===========================================================================
_ST_MODEL = None
_MODE = None


def mode_retrieval() -> str:
    """Mode of retrieval actif : 'sentence-to transforms' or 'tfidf'."""
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


def ollama_disponible() -> bool:
    """True if an Ollama server answers and serves the model asked for (tested once)."""
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


def mode_jugement() -> str:
    """Judging and routing mode: 'ollama' (real LLM) or 'regle' (deterministic)."""
    return "ollama" if ollama_disponible() else "regle"


def _llm(prompt: str, *, temperature: float = 0.0, num_predict: int = 128) -> str:
    import ollama
    r = ollama.chat(model=_OLLAMA_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": temperature, "num_predict": num_predict})
    return r["message"]["content"].strip()


# ===========================================================================
# Accounting of the cost — for compares the architectures objectivement
# ===========================================================================
@dataclass
class Counter:
    """Counts the operations costeuses : appels LLM and researchess (corpus + web).

 Each architecture (RAG, Self-RAG, CRAG, Adaptive) shares the same counter, which
    makes the chapter's comparison — "the loop is never free" — countable.
 """
    appels_llm: int = 0
    recherches_corpus: int = 0
    recherches_web: int = 0

    def llm(self, n: int = 1) -> None:
        self.appels_llm += n

    def corpus(self, n: int = 1) -> None:
        self.recherches_corpus += n

    def web(self, n: int = 1) -> None:
        self.recherches_web += n

    @property
    def total(self) -> int:
        return self.appels_llm + self.recherches_corpus + self.recherches_web

    def summary(self) -> str:
        return (f"{self.appels_llm} appels LLM, {self.recherches_corpus} rech. corpus, "
                f"{self.recherches_web} rech. web (total {self.total})")


# ===========================================================================
# Moteur of search (retrieval)
# ===========================================================================
class Search:
    """Indexe a corpus and classe the documents by relevance to a query."""

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

    def scores(self, requete: str) -> np.ndarray:
        if self.mode == "sentence-transformers":
            q = _ST_MODEL.encode([requete], normalize_embeddings=True)[0]
            return self._vecs @ q
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([requete])
        return cosine_similarity(q, self._mat)[0]

    def classer(self, requete: str, k: Optional[int] = None
                ) -> List[Tuple[int, float]]:
        s = self.scores(requete).astype(float)
        ordre = np.argsort(-s)
        res = [(int(i), float(s[i])) for i in ordre]
        return res[:k] if k else res


# ===========================================================================
#  Utilitaires lexicaux
# ===========================================================================
def _tokens(texte: str) -> List[str]:
    return re.findall(r"\w+", texte.lower())


def _phrases(texte: str) -> List[str]:
    parts = re.split(r"(?<=[\.\!\?])\s+|\n+", texte.strip())
    return [p.strip() for p in parts if p.strip()]


# The empty words, stripped before counting the "carrying" words of a question.
# This list is a MECHANISM, not decoration: the carrier count feeds the router's
# complexity rule below, and it also weights the Self-RAG relevance scores. Left
# in French against an English corpus it filters nothing, every question looks
# long and content-rich, and the routing drifts towards "iterative".
_STOP_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "at", "by",
    "with", "without", "is", "are", "be", "been", "was", "were", "it", "its",
    "this", "that", "these", "those", "what", "which", "who", "whom", "whose",
    "not", "more", "must", "can", "may", "should", "would", "his", "her",
    "their", "how", "when", "where", "you", "we", "i", "do", "does", "did",
    "there", "here", "from", "as", "if", "than", "then", "so", "such",
}


def _carriers(text: str) -> List[str]:
    """The "carrying" words: everything that is neither empty nor too short."""
    return [t for t in _tokens(text) if t not in _STOP_WORDS and len(t) > 2]


# ===========================================================================
# SELF-RAG — reflection tokens (ISREL / ISSUP / ISUSE) plus confidence
# ===========================================================================
# During generation, Self-RAG interleaves "reflection tokens" that judge:
# ISREL — is the retrieved passage RELEVANT to the question?
# ISSUP — the affirmation produite is-it SOUTENUE by the passage ?
# ISUSE — is the answer USEFUL (does it really answer the question)?
# Explicit functions: with Ollama, a real LLM performs the assessment; otherwise,
# a deterministic proxy (term overlap). The confidence aggregates those signals.

@dataclass
class SelfRAGJudgment:
    isrel: float           # relevance moyenne passages [0,1]
    issup: float           # ancrage of the answer in the passages [0,1]
    isuse: float           # the usefulness of the answer to the question [0,1]
    confiance: float       # the aggregated score [0,1]
    details: List[dict] = field(default_factory=list)


def isrel(question: str, passage: str, compteur: Optional[Counter] = None) -> float:
    """ISREL — is the passage relevant to the question? Returns [0,1]."""
    if ollama_disponible():
        if compteur:
            compteur.llm()
        prompt = ("Is the passage RELEVANT to answering the question? "
                  "Answer YES or NO, nothing else.\n\n"
                  f"Question: {question}\nPassage: {passage}\nAnswer:")
        return 1.0 if _llm(prompt, num_predict=3).upper().startswith(("OUI", "YES")) \
            else 0.0
    if compteur:
        compteur.llm()  # a jugement is a travail, that it soit LLM or regle
    q, p = set(_carriers(question)), set(_carriers(passage))
    if not q:
        return 0.0
    return min(1.0, len(q & p) / max(1, len(q)) * 1.5)


def issup(affirmation: str, passages: Sequence[str],
          compteur: Optional[Counter] = None) -> float:
    """ISSUP — is the statement supported by the passages? Returns [0,1]."""
    if ollama_disponible():
        if compteur:
            compteur.llm()
        ctx = "\n".join(f"- {p}" for p in passages)
        prompt = ("Is the statement DIRECTLY supported by the passages? "
                  "Answer YES or NO, nothing else.\n\n"
                  f"Passages:\n{ctx}\n\nStatement: {affirmation}\nAnswer:")
        return 1.0 if _llm(prompt, num_predict=3).upper().startswith(("OUI", "YES")) \
            else 0.0
    if compteur:
        compteur.llm()
    vocab = set()
    for p in passages:
        vocab |= set(_carriers(p))
    porteurs = _carriers(affirmation)
    if not porteurs:
        return 1.0
    return sum(1 for t in porteurs if t in vocab) / len(porteurs)


def isuse(question: str, reponse: str, compteur: Optional[Counter] = None) -> float:
    """ISUSE — the answer is-it utile vis-to-vis of the question ? Returns [0,1]."""
    if ollama_disponible():
        if compteur:
            compteur.llm()
        prompt = ("Does the answer usefully address the question (not off-topic, "
                  "not an empty admission)? Answer YES or NO.\n\n"
                  f"Question: {question}\nAnswer: {reponse}\nVerdict:")
        return 1.0 if _llm(prompt, num_predict=3).upper().startswith(("OUI", "YES")) \
            else 0.0
    if compteur:
        compteur.llm()
    if not reponse.strip() or "introuvable" in reponse.lower() \
            or "cannot find" in reponse.lower():
        return 0.2
    q, r = set(_carriers(question)), set(_carriers(reponse))
    if not q:
        return 0.5
    return min(1.0, len(q & r) / max(1, len(q)) * 1.5)


def tokens_reflexion(question: str, passages: Sequence[str], reponse: str,
                     compteur: Optional[Counter] = None) -> SelfRAGJudgment:
    """Apply the three reflection tokens and aggregate a confidence score.

    This is the heart of Self-RAG: the model "looks up while writing". The
    confidence is a weighted mean favouring grounding (ISSUP), because an
    unsupported answer is the main danger — false but confident.
 """
    details = []
    rel = []
    for p in passages:
        v = isrel(question, p, compteur)
        rel.append(v)
        details.append({"passage": p[:60], "isrel": v})
    moy_rel = float(np.mean(rel)) if rel else 0.0

    phrases = _phrases(reponse)
    sup = [issup(ph, passages, compteur) for ph in phrases] if phrases else [1.0]
    moy_sup = float(np.mean(sup))

    use = isuse(question, reponse, compteur)

    # Trust : the PERTINENCE (ISREL) and the UTILITE (ISUSE) pesent the more. A texte
    # hors-sujet recopie verbatim obtains a ISSUP eleve without rien valoir : on not the
    # laisse so not, a lui seul, gonfler the trust.
    confiance = 0.45 * moy_rel + 0.20 * moy_sup + 0.35 * use
    return SelfRAGJudgment(isrel=moy_rel, issup=moy_sup, isuse=use,
                           confiance=confiance, details=details)


# ===========================================================================
# CRAG — grader of relevance to trois verdicts + repli web simulated
# ===========================================================================
def grader_crag(question: str, passages: Sequence[str],
                seuil_bas: float = 0.20, seuil_haut: float = 0.55,
                compteur: Optional[Counter] = None) -> Tuple[str, float]:
    """Grader of relevance of CRAG. Returns (verdict, score) where verdict ∈

 {'confident', 'ambiguous', 'not_confident'}. The score measures the relevance globale 
    of the retrieved passages against the question.
 """
    if not passages:
        return ("not_confident", 0.0)
    if ollama_disponible():
        if compteur:
            compteur.llm()
        ctx = "\n".join(f"- {p}" for p in passages)
        prompt = ("Rate from 0 to 10 the OVERALL RELEVANCE of these passages for "
                  "answering the question. Answer with an integer ONLY.\n\n"
                  f"Question: {question}\nPassages:\n{ctx}\nRating:")
        m = re.search(r"\d+", _llm(prompt, num_predict=4))
        score = (min(10, int(m.group())) / 10.0) if m else 0.0
    else:
        if compteur:
            compteur.llm()
        q = set(_carriers(question))
        if not q:
            score = 0.0
        else:
            best = max(len(q & set(_carriers(p))) / len(q) for p in passages)
            score = min(1.0, best)
            # A "missing content" penalty: if the question names an entity
            # distinctive (P-99, M-18, HX-420...) absente of TOUS the passages, the bon
            # document is not the target, regardless of generic token overlap. Without this,
            # "stop P-99" would look confident, on the shared words "stop/pump".
            entites = set(re.findall(r"\b[a-z]{1,3}-?\d{2,4}\b", question.lower()))
            if entites:
                texte_passages = " ".join(passages).lower()
                if any(e not in texte_passages for e in entites):
                    score = min(score, 0.10)
    if score < seuil_bas:
        return ("not_confident", score)
    if score < seuil_haut:
        return ("ambiguous", score)
    return ("confident", score)


# The simulated web base: deterministic and offline. It represents "one more
# source" — regulation, external documentation — that the internal corpus lacks.
_SIMULATED_WEB = [
    {"subject": "web-heatwave-agency-workers",
     "text": "Employment law: in periods of high heat, the employer must adapt the "
             "organisation of work for agency workers as for permanent staff — "
             "cool water, breaks, adjusted hours."},
    {"subject": "web-p99-specs",
     "text": "Manufacturer documentation: pump P-99 (a recent series) stops in an "
             "emergency through a double electronic safety, cutting the drive and "
             "then closing the valves under power."},
    {"subject": "web-remote-work-2024",
     "text": "A recent regulatory update: the sector agreement raises remote work "
             "for apprentices to three days a week, subject to conditions of "
             "autonomy validated by the supervisor."},
    {"subject": "web-generic",
     "text": "A general external resource on industrial maintenance and employment "
             "regulation, to be cross-checked against official sources."},
]


def web_search(question: str, k: int = 1,
                  compteur: Optional[Counter] = None) -> List[dict]:
    """The SIMULATED web fallback: builds a query from the question, in the spirit

 transformation of query of the chap. 21), interroge a base externe deterministic,
 and returns the meilleurs passages. Hors-line, without key API.
 """
    if compteur:
        compteur.web()
    rech = Search([d["text"] for d in _SIMULATED_WEB])
    ordre = rech.classer(question, k=k)
    return [{"subject": _SIMULATED_WEB[i]["subject"], "text": _SIMULATED_WEB[i]["text"],
             "score": round(s, 3), "source": "web"} for i, s in ordre]


# ===========================================================================
# ADAPTIVE-RAG — a three-way complexity router
# ===========================================================================
# Trois voies : 'direct' (not of retrieval), 'simple' (a passe), 'iterative' (boucle).
# Markers of an ANALYTICAL question: their presence routes to the iterative path.
#
# CAREFUL WITH THIS LIST. "summarise" and "summary" are deliberately ABSENT: a
# request to summarise one procedure is a single-pass question, and adding them
# would misroute query 4 of the corpus. The French list excluded "résume" for
# exactly the same reason.
_ANALYSIS_WORDS = {"analyse", "analyze", "compare", "compared", "why", "causes",
                   "impact", "impacts", "consequences", "diagnose", "diagnostic",
                   "all", "together", "relations", "dependencies", "evaluate",
                   "assess", "synthesis"}
_FACTUAL_WORDS = {"reference", "code", "date", "number", "name", "many",
                  "definition"}


def routeur(question: str, compteur: Optional[Counter] = None) -> Tuple[str, str]:
    """The complexity router of Adaptive-RAG. Returns (path, justification).

 With Ollama : a true classificateur by prompt court. Sinon : rules
 linguistiques (longueur, marqueurs of analyse, conjonctions, words factuels).
 """
    if ollama_disponible():
        if compteur:
            compteur.llm()
        prompt = ("Classify the question by the effort it needs. Answer with ONE "
                  "word only:\n"
                  "DIRECT   = trivial or general knowledge, no search useful;\n"
                  "SIMPLE   = one documentary search is enough;\n"
                  "ITERATIVE= complex, multi-facet, needs several searches.\n\n"
                  f"Question: {question}\nClass:")
        v = _llm(prompt, num_predict=4).strip().lower()
        if "direct" in v or "direct" in v:
            return ("direct", "LLM: a trivial question, no search")
        if "iterativ" in v:
            return ("iterative", "LLM: a complex question, a loop is needed")
        return ("simple", "LLM: one search pass is enough")
    # --- Rules deterministics ---------------------------------------------
    qb = question.lower()
    toks = set(_tokens(qb))
    n = len(_carriers(qb))
    # Marqueurs of entities business : their presence implique that a search is utile
    # (you cannot answer "off the top of your head").
    # These markers must match the vocabulary of the corpus questions. They say
    # "a search is useful here", so their absence is what allows the direct route.
    has_entity = bool(re.search(r"\b[pm]-?\d{1,3}\b", qb)) or \
        any(m in qb for m in ("procedure", "corpus", "agreement", "bonus",
                              "remote work", "telework", "reference", "lubricant",
                              "bearings", "valves", "agency worker", "heatwave",
                              "employer", "obligations"))
    # ITERATIVE : marqueurs of analyse, comparaison explicite, or multi-volets.
    # The conjunction in the regex is "and": in French it was "et". Two codes
    # joined by it signal a comparison, and so the iterative path.
    if (toks & _ANALYSIS_WORDS) or qb.count(",") >= 2 or n >= 13 \
            or re.search(r"\b[pm]-?\d+\b.*\band\b.*\b[pm]-?\d+\b", qb):
        return ("iterative", "rule: analysis / comparison / multi-facet markers")
    # DIRECT: no business entity, a short question of general knowledge.
    if not has_entity and n <= 6:
        return ("direct", "rule: no business entity, a direct answer is possible")
    # SIMPLE: everything else. One documentary search is enough.
    return ("simple", "rule: a standard documentary question")


# ===========================================================================
# Generation of answer — Ollama or repli extractif
# ===========================================================================
def generate_answer(question: str, passages: Sequence[str],
                    compteur: Optional[Counter] = None) -> str:
    """Generate an answer from the passages: Ollama, or a deterministic extractive fallback."""
    if not passages:
        return "I cannot find that information in the sources available."
    if ollama_disponible():
        if compteur:
            compteur.llm()
        ctx = "\n".join(f"- {p}" for p in passages)
        prompt = ("Relying ONLY on these excerpts, answer briefly. If "
                  "l'information manque, dis-le.\n\n"
                  f"Excerpts:\n{ctx}\n\nQuestion: {question}\nAnswer:")
        return _llm(prompt, num_predict=200)
    if compteur:
        compteur.llm()
    q = set(_carriers(question))
    classes = sorted(passages, key=lambda p: len(q & set(_carriers(p))), reverse=True)
    retenus = [p for p in classes if q & set(_carriers(p))][:2]
    return " ".join(retenus) if retenus else \
        "I cannot find that information in the sources available."


# ===========================================================================
# Metrics of quality (for the comparaisons of the chapitre)
# ===========================================================================
def couverture(reponse: str, volets: Sequence[str]) -> float:
    """The share of the expected facets present in the answer, by label."""
    if not volets:
        return 1.0
    r = reponse.lower()
    return sum(1 for v in volets if v.lower() in r) / len(volets)


def fonde(reponse: str, passages: Sequence[str]) -> float:
    """Part sentences of the answer ancreatess in the passages (proxy of fidelity)."""
    return issup(reponse, passages) if reponse.strip() else 1.0
