# -*- coding: utf-8 -*-
"""
agentkit.py — the shared building blocks of Chapter 25.

Chapter 25 takes RAG from the pipeline to the agent: a system that decides for
itself what to do. This module supplies the pieces — the conditional brain, the
bounded investigation, the two memories (short and long term), and the four roles
of a reliable multi-agent system.

  - cerveau_* : the decision "search / answer / delegate", in rule mode or LLM
    mode (Ollama). This is the chapter's "location of the decision";
  - ShortTermMemory / LongTermMemory: the architectural distinction;
  - AgentRAG: a conditional, bounded-iterative agent, with memory;
  - SpecialistAgent and the orchestrator: Planner, Executor, Critic, Supervisor.

As close to real usage as possible
----------------------------------
As in the earlier chapters, two levels of realism and no API key: Ollama if a
local model answers, otherwise deterministic rules.

The chapter's thesis holds in both cases: the difference between a workflow and
an agent is not the technology, it is the LOCATION OF THE DECISION. That is shown
by keeping the same graph either way.

A WARNING ON THE WORD LISTS. Several mechanisms here key on literal strings: the
stop words, the trivial-question markers, the business entity markers, the
conversation themes, and above all the ELLIPSIS MARKERS used by
resoudre_referent(). All are matched against the text of the questions and must
stay in step with generate_corpus.py. The ellipsis markers are the most exposed:
if they match nothing, no referent is ever resolved and Lab 25-3 reports that
memory changes nothing, with no error.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# Detection optionnelle moteurs (embeddings + LLM local)
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


def ollama_disponible() -> bool:
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


def mode_cerveau() -> str:
    """Mode of the cerveau agents : 'ollama' (true LLM) or 'regle' (deterministic)."""
    return "ollama" if ollama_disponible() else "regle"


def _llm(prompt: str, *, temperature: float = 0.0, num_predict: int = 128) -> str:
    import ollama
    r = ollama.chat(model=_OLLAMA_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": temperature, "num_predict": num_predict})
    return r["message"]["content"].strip()


# ===========================================================================
# Accounting of the cost
# ===========================================================================
@dataclass
class Counter:
    appels_llm: int = 0
    recherches: int = 0
    delegations: int = 0

    def llm(self, n: int = 1) -> None:
        self.appels_llm += n

    def rech(self, n: int = 1) -> None:
        self.recherches += n

    def delegue(self, n: int = 1) -> None:
        self.delegations += n

    @property
    def total(self) -> int:
        return self.appels_llm + self.recherches + self.delegations

    def summary(self) -> str:
        return (f"{self.appels_llm} LLM calls, {self.recherches} searches, "
                f"{self.delegations} delegations (total {self.total})")


# ===========================================================================
#  Utilitaires lexicaux
# ===========================================================================
def _tokens(t: str) -> List[str]:
    return re.findall(r"\w+", t.lower())


# The empty words. This list is a mechanism, not decoration: it feeds the
# overlap scoring used to rank passages, so it must be in the corpus language.
_STOP_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "and", "or", "at", "by",
    "with", "without", "is", "are", "be", "was", "were", "it", "its", "this",
    "that", "these", "those", "what", "which", "who", "how", "when", "where",
    "not", "more", "must", "can", "may", "should", "would", "his", "her",
    "their", "you", "we", "i", "do", "does", "did", "if", "from", "as", "many",
}


def _destem(mot: str) -> str:
    # A light stemming: neutralises the common plural (apprentice ~ apprentices).
    # The French version also handled the feminine and the -aux plural.
    for suf in ("ies", "es", "s"):
        if len(mot) > 4 and mot.endswith(suf):
            return mot[:-len(suf)]
    return mot


def _porteurs(t: str) -> List[str]:
    return [_destem(x) for x in _tokens(t)
            if x not in _STOP_WORDS and len(x) > 2]


# ===========================================================================
# Moteur of search + Tool
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


@dataclass
class Tool:
    """A outil appelable by a agent (nom, description, fonction, journal)."""
    nom: str
    description: str
    fonction: Callable
    journal: List[dict] = field(default_factory=list)

    def appeler(self, **kwargs):
        self.journal.append(dict(kwargs))
        return self.fonction(**kwargs)


def search_tool(rech: Search, frags: List[dict], k: int = 3) -> Tool:
    """Fabrique the outil of search documentaire to partir of a index + fragments."""
    def _f(requete: str):
        return [{"id": frags[i]["id"], "subject": frags[i]["subject"],
                 "text": frags[i]["text"], "score": round(s, 3)}
                for i, s in rech.classer(requete, k=k)]
    return Tool("recherche_documentaire",
                 "Search the technical corpus and return the relevant excerpts.",
                 _f)


# ===========================================================================
# Memory court terme — historique of a conversation, with compression
# ===========================================================================
@dataclass
class ShortTermMemory:
    """Keep the thread of a conversation. Past a threshold, compress the old turns.

    The compression — a summary of the older exchanges — is what extends the
    autonomy of the agent without saturating the context window. With no LLM, the
    "summary" extracts
    the entities and salient subjects of the older turns — enough to keep the referent.
 """
    seuil_compression: int = 4
    tours: List[dict] = field(default_factory=list)
    summary: str = ""

    def add(self, question: str, reponse: str) -> None:
        self.tours.append({"question": question, "reponse": reponse})
        if len(self.tours) > self.seuil_compression:
            self._compresser()

    def _compresser(self) -> None:
        anciens = self.tours[:-self.seuil_compression // 2 or None]
        recents = self.tours[len(anciens):]
        sujets = []
        for t in anciens:
            sujets += [e for e in re.findall(r"\b[a-z]{1,3}-?\d{2,4}\b",
                                             (t["question"] + " " + t["reponse"]).lower())]
            sujets += [m for m in ("remote work", "telework", "bonus", "stop",
                                   "overheating", "maintenance", "apprentice")
                       if m in (t["question"] + t["reponse"]).lower()]
        uniq = sorted(set(sujets))
        ajout = ("Subjects already covered: " + ", ".join(uniq) + ".") if uniq else ""
        self.summary = (self.summary + " " + ajout).strip()
        self.tours = recents

    def contexte(self) -> str:
        """The conversational context: the compressed summary plus the recent turns."""
        lignes = []
        if self.summary:
            lignes.append(f"[Memory] {self.summary}")
        for t in self.tours:
            lignes.append(f"Q: {t['question']}\nR: {t['reponse']}")
        return "\n".join(lignes)

    def referents(self) -> List[str]:
        """The entities already mentioned, used to resolve "and for the P-42?"."""
        texte = (self.summary + " " +
                 " ".join(t["question"] + " " + t["reponse"] for t in self.tours))
        vus, ordre = set(), []
        for e in re.findall(r"\b[a-z]-?\d{2,4}\b", texte.lower()):
            if e not in vus:
                vus.add(e); ordre.append(e)
        return ordre  # order of appearance: the last-mentioned entity comes last


# ===========================================================================
# Memory long terme — persistance between sessions (file JSON local)
# ===========================================================================
class LongTermMemory:
    """Persist what the agent has LEARNT from its interactions: preferences and
    established facts.

    Distinct from the corpus (the library): this is the agent's notebook. Stored
    in a local JSON file — no external database, no API key.
 """

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.data: Dict[str, dict] = {}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self.data = {}

    def memoriser(self, cle: str, valeur, categorie: str = "fait") -> None:
        self.data[cle] = {"valeur": valeur, "categorie": categorie}
        self._sauver()

    def rappeler(self, cle: str):
        item = self.data.get(cle)
        return item["valeur"] if item else None

    def preferences(self) -> Dict[str, str]:
        return {k: v["valeur"] for k, v in self.data.items()
                if v.get("categorie") == "preference"}

    def tout(self) -> Dict[str, dict]:
        return dict(self.data)

    def _sauver(self) -> None:
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2),
                               encoding="utf-8")

    def effacer(self) -> None:
        self.data = {}
        if self.path.exists():
            self.path.unlink()


# ===========================================================================
# The agent's brain — the "location of the decision"
# ===========================================================================
def cerveau_conditionnel(question: str, referents: Sequence[str],
                         compteur: Optional[Counter] = None) -> Tuple[str, str]:
    """Patron 1 — Conditionnel : faut-it to search, or to answer directly ?

    Returns ('repondre', reason) if the question is trivial or out of domain,
 ('to search', query). With Ollama : true jugement. Sinon : rules.
 """
    if ollama_disponible():
        if compteur:
            compteur.llm()
        prompt = ("Is a documentary search needed to answer? Reply SEARCH if the "
                  "question is about internal procedures, equipment or rules, "
                  "ANSWER if it is trivial or general knowledge.\n\n"
                  f"Question: {question}\nReply (SEARCH/ANSWER):")
        v = _llm(prompt, num_predict=4).upper()
        if v.startswith("REPOND"):
            return ("repondre", "LLM: a trivial question, no search")
        return ("chercher", question)
    qb = question.lower()
    # Both lists below must be in the corpus language: they decide whether a
    # search is worth running at all.
    trivial = any(m in qb for m in ("date", "hello", "thanks", "who are you",
                                    "how are you"))
    a_entite = bool(re.search(r"\b[pm]-?\d{1,3}\b", qb)) or \
        any(m in qb for m in ("procedure", "stop", "remote work", "telework",
                              "bonus", "overheating", "maintenance", "failure",
                              "equipment", "depend", "impact"))
    if trivial and not a_entite:
        return ("repondre", "rule: a trivial question, no search")
    return ("chercher", question)


# ===========================================================================
# AgentRAG — conditional plus bounded-iterative, with short-term memory
# ===========================================================================
def generate(question: str, passages: Sequence[str], contexte_memoire: str = "",
            compteur: Optional[Counter] = None) -> str:
    if ollama_disponible():
        if compteur:
            compteur.llm()
        ctx = "\n".join(f"- {p}" for p in passages) or "(no passage)"
        mem = f"\nContexte de conversation :\n{contexte_memoire}\n" if contexte_memoire else ""
        prompt = (f"{mem}\nRelying on the excerpts, answer briefly.\n\n"
                  f"Excerpts:\n{ctx}\n\nQuestion: {question}\nAnswer:")
        return _llm(prompt, num_predict=160)
    if not passages:
        return "I did not need to search for this question."
    q = set(_porteurs(question))
    def score(p):
        chevauche = len(q & set(_porteurs(p)))
        # Bonus when the passage contains a distinctive entity named in the question.
        ents_q = set(re.findall(r"\b[a-z]{1,3}-?\d{1,4}\b", question.lower()))
        ents_p = set(re.findall(r"\b[a-z]{1,3}-?\d{1,4}\b", p.lower()))
        return chevauche + 3 * len(ents_q & ents_p)
    classes = sorted(passages, key=score, reverse=True)
    meilleur = classes[0]
    return meilleur if score(meilleur) > 0 else \
        "I cannot find that information in the corpus."


# The salient themes: the conversational predicate an elliptical question
# inherits from the previous turn ("and for the P-42?" inherits "emergency
# stop"). These strings are matched against the text of the turns, so they must
# match the wording of the corpus.
_THEMES = ["emergency stop procedure", "emergency stop", "remote work",
           "bonus", "overheating", "maintenance", "cooling", "length of service"]

# The HR themes: for these, an equipment referent must NOT be appended. Asking
# "and for a permanent employee?" after a remote-work question has nothing to do
# with pump P-42, even though P-42 was mentioned earlier in the conversation.
_HR_THEMES = ("remote work", "bonus", "length of service")


def _theme_du_tour(texte: str) -> Optional[str]:
    tl = texte.lower()
    for th in _THEMES:
        if th in tl:
            return th
    return None


def resoudre_referent(question: str, memoire: ShortTermMemory) -> str:
    """Resolve an elliptical question by re-injecting the THEME of the last turn.

    "And for the P-42?" after "the stop procedure for the P-12?" becomes "the
    stop procedure for P-42". "And for a permanent employee?" after a question
    about remote work inherits "remote work". Short-term memory is what makes the
    conversation possible: without it, these questions lose their subject. The
    theme is inherited, and the known entity too — but only if the question names
    none itself.

    THE MARKER LIST BELOW IS THE MECHANISM. If it matches nothing, no question is
    ever treated as elliptical, no referent is ever resolved, and Lab 25-3 reports
    that memory changes nothing — with no error at all. The markers must match the
    wording of the conversation in generate_corpus.py.
    """
    qb = question.lower()
    elliptique = bool(re.search(r"\b(and for|what about|and what about|"
                                r"same for|the same|and with|likewise|"
                                r"and a|and an)\b", qb))
    if not elliptique or not memoire.tours:
        return question
    dernier = memoire.tours[-1]
    theme = _theme_du_tour(dernier["question"] + " " + dernier["reponse"])
    cite_entite = bool(re.search(r"\b[pm]-?\d{1,3}\b", qb))
    enrichi = question
    if theme and theme not in qb:
        enrichi = f"{question} [{theme}]"
    if not cite_entite and theme not in _HR_THEMES:
        refs = memoire.referents()
        if refs:
            enrichi = f"{enrichi} (au sujet de {refs[-1]})"
    return enrichi


@dataclass
class AgentRAG:
    """A conditional, bounded-iterative agent, with short-term memory.

      - conditional: decides whether a search is needed (cerveau_conditionnel);
      - iterative: if so, a loop bounded by a budget;
      - memory: keeps the thread of the conversation and resolves the references.
 """
    outil: Tool
    memoire: ShortTermMemory = field(default_factory=ShortTermMemory)
    budget: int = 3

    def repondre(self, question: str, compteur: Optional[Counter] = None) -> dict:
        compteur = compteur or Counter()
        trace = []
        q_resolue = resoudre_referent(question, self.memoire)
        if q_resolue != question:
            trace.append(f"memory: referent resolved -> \"{q_resolue}\"")

        decision, arg = cerveau_conditionnel(q_resolue, self.memoire.referents(),
                                             compteur)
        trace.append(f"routeur conditionnel → {decision}")
        if decision == "repondre":
            rep = generate(q_resolue, [], self.memoire.contexte(), compteur)
            self.memoire.add(question, rep)
            return {"reponse": rep, "trace": trace, "cout": compteur, "path": "direct"}

        # The bounded iterative loop.
        contexte, vus = [], set()
        requete = arg
        for tour in range(1, self.budget + 1):
            compteur.rech()
            res = self.outil.appeler(requete=requete)
            # On retient the meilleurs passages encore inconnus (jusqu'a 2 by tour) :
            # the generateur to choosea next the more relevant a the question.
            ajoutes = []
            for r in res[:2]:
                if r["subject"] not in vus:
                    contexte.append(r["text"])
                    vus.add(r["subject"])
                    ajoutes.append(r["subject"])
            principal = res[0]
            trace.append(f"turn {tour}: search(\"{requete[:40]}\") -> "
                         f"{', '.join(ajoutes) or principal['subject']}")
            # Condition of arret : a passage nettement relevant suffit for a
            # question mono-sujet ; sinon on poursuit jusqu'at the budget.
            if principal["score"] > 0.15 and tour >= 1:
                break
            requete = q_resolue
        rep = generate(q_resolue, contexte, self.memoire.contexte(), compteur)
        self.memoire.add(question, rep)
        return {"reponse": rep, "trace": trace, "cout": compteur, "path": "agent"}


# ===========================================================================
# Multi-agent — specialist agents plus an orchestrator (a state graph)
# ===========================================================================
@dataclass
class SpecialistAgent:
    """An expert agent for a sub-domain, with its own restricted search tool."""
    nom: str
    domaine: str
    outil: Tool
    mots_cles: List[str] = field(default_factory=list)

    def competence(self, question: str) -> float:
        """How far does this question fall within my domain? [0,1].

 On counts the words-cles of the domain reellement presents in the question. A seul
 word incident not suffit not a mobiliser the agent : it faut a presence nette.
 """
        ql = question.lower()
        if not self.mots_cles:
            return 0.0
        touches = sum(1 for m in self.mots_cles if m in ql)
        return min(1.0, touches / 2.0)  # 2 mots-cles -> competence pleine

    def contribuer(self, question: str, compteur: Optional[Counter] = None) -> dict:
        """Produce a contribution on the question, from its own specialist corpus.

 If the question names a distinctive entity (P-42, M-18...), prefer the
 passage that mentions it over the passage with the best lexical score (otherwise
    "stop P-42" could return the P-12 sheet, which is lexically close). The
 fiabilite laisse the Critic rejeter the contributions too low (anti-bruit).
 """
        if compteur:
            compteur.rech()
        res = self.outil.appeler(requete=question)
        if not res:
            return {"agent": self.nom, "domain": self.domaine,
                    "contribution": "", "reliable": False, "score": 0.0}
        ents_q = set(re.findall(r"\b[a-z]{1,3}-?\d{1,4}\b", question.lower()))
        meilleur = res[0]
        if ents_q:
            for r in res:
                if ents_q & set(re.findall(r"\b[a-z]{1,3}-?\d{1,4}\b",
                                           r["text"].lower())):
                    meilleur = r
                    break
        # Fiabilite by threshold of relevance : a contribution too low is traitee
        # as unreliable and will be rejected by the Critic (the anti-noise guardrail).
        reliable = meilleur["score"] > 0.18
        texte = meilleur["text"] if reliable else ""
        return {"agent": self.nom, "domain": self.domaine,
                "contribution": texte, "reliable": reliable,
                "score": meilleur["score"]}


class Orchestrator:
    """The graph of state multi-agents : Planner / Executor / Critic / Supervisor.

    The golden rule of the chapter: no agent calls another directly. All routing
    goes through the orchestrator, which makes the flow deterministic and
    traceable.

      - Planner: decomposes and chooses which specialists to mobilise;
      - Executor: runs the contributions of the chosen specialists;
 - Critic: reviews and rejects unreliable contributions (safeguard
        the "false but confident" case);
      - Supervisor: applies the budget, can force an end, and synthesises.
 """

    def __init__(self, specialistes: List[SpecialistAgent], budget: int = 6) -> None:
        self.specialistes = specialistes
        self.budget = budget

    def process(self, question: str, compteur: Optional[Counter] = None) -> dict:
        compteur = compteur or Counter()
        trace = []

        # --- PLANNER: choose the competent specialists ------------------------
        scores = [(a, a.competence(question)) for a in self.specialistes]
        choisis = [a for a, s in scores if s > 0.0] or [max(scores, key=lambda x: x[1])[0]]
        trace.append("PLANNER : agents mobilised -> " +
                     ", ".join(a.nom for a in choisis))

        # --- EXECUTOR : recueillir the contributions -----------------------
        contributions = []
        for a in choisis:
            if compteur.delegations >= self.budget:
                trace.append("SUPERVISOR: budget reached, delegations stopped")
                break
            compteur.delegue()
            c = a.contribuer(question, compteur)
            contributions.append(c)
            trace.append(f"EXECUTOR : {a.nom} contribue "
                         f"({'reliable' if c['reliable'] else 'vide'}, "
                         f"score {c['score']:.2f})")

        # --- CRITIC: reject unreliable contributions ----------------
        retenues = [c for c in contributions if c["reliable"]]
        rejetees = [c for c in contributions if not c["reliable"]]
        for c in rejetees:
            trace.append(f"CRITIC : contribution de {c['agent']} rejected (unreliable)")

        # --- SUPERVISOR : synthesis finale ----------------------------------
        if not retenues:
            trace.append("SUPERVISOR: no reliable contribution -> an honest admission")
            synthese = ("No agent holds reliable information on this question.")
        else:
            if ollama_disponible():
                compteur.llm()
                blocs = "\n".join(f"[{c['agent']}] {c['contribution']}" for c in retenues)
                synthese = _llm("Synthesise these expert contributions into a coherent "
                                f"answer.\n\n{blocs}\n\nQuestion: {question}\n"
                                "Synthesis:", num_predict=200)
            else:
                synthese = " ".join(f"[{c['agent']}] {c['contribution']}"
                                    for c in retenues)
            trace.append(f"SUPERVISOR : synthesis of {len(retenues)} contribution(s)")

        return {"reponse": synthese, "trace": trace, "cout": compteur,
                "retenues": retenues, "rejetees": rejetees}
