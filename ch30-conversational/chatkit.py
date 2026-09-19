# -*- coding: utf-8 -*-
"""
chatkit.py — the shared module of the Chapter 30 labs (conversational RAG).

The chapter's thesis — *in conversation, the quality of the retrieval depends
first on the quality of the reformulation, not on the embedding model* — stays
entirely visible offline.

What this module supplies:

  - Search              : the vector retrieval over the fragments
  - reformuler          : a conversational turn -> a self-contained query
  - router_tour         : chitchat / followup / search
  - WindowMemory, SummaryMemory, StateMemory, HybridMemory: the memory strategies
  - the state extractors: equipment, problem, supplier, technician, contract, date

FIVE MECHANISMS IN THIS FILE ARE LANGUAGE-BOUND, and none of them raises an error
when it stops matching:

  1. _PRONOUNS       — decides whether a turn needs anchoring;
  2. _MOTIF_EQUIP    — recognises "pump P-42" and the like;
  3. the theme list  — completes an ellipsis;
  4. the router sets — chitchat and followup markers;
  5. _MOTIFS_ETAT    — the state extractors.

Each is matched against the text of the conversation in generate_corpus.py and
must stay in step with it. Lab 30-2 prints the mean reformulation gain (French
baseline: +25%) and Lab 30-5 shows whether the late turns resolve from state:
both are the checks to run after any edit.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import deque
from pathlib import Path

import numpy as np

CORPUS = Path(__file__).resolve().parent / "corpus"


# ===========================================================================
#  0)  Outils optionnels
# ===========================================================================
def _a_sentence_transformers() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def _ollama_modele() -> str | None:
    modele = os.environ.get("OLLAMA_MODEL")
    if not modele:
        return None
    try:
        import ollama  # noqa: F401
        return modele
    except Exception:
        return None


def llm(prompt: str) -> str:
    """Point of input unique toward a LLM local (Ollama, ex. Mistral).
 An empty string when unavailable makes the labs use their deterministic fallback.
 """
    modele = _ollama_modele()
    if not modele:
        return ""
    try:
        import ollama
        rep = ollama.generate(model=modele, prompt=prompt,
                              options={"temperature": 0.0})
        return rep["response"].strip()
    except Exception:
        return ""


def bandeau(titre: str) -> None:
    emb = "sentence-transformers" if _a_sentence_transformers() else "TF-IDF"
    cerveau = _ollama_modele() or "deterministic fallback (rules)"
    print("=" * 74)
    print(titre)
    print(f"  Embeddings : {emb}   |   Raisonnement : {cerveau}")
    print("=" * 74)


# ===========================================================================
#  1)  Normalisation
# ===========================================================================
def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texte)


def _mots(texte: str) -> set[str]:
    stop = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or",
            "at", "by", "with", "is", "are", "be", "was", "were", "it", "its",
            "this", "that", "we", "you", "i", "do", "does", "did", "have",
            "has", "had", "any", "what", "who", "how", "when", "there",
            "them", "they", "our", "your", "us", "can", "will"}
    return {m for m in normaliser(texte).split() if len(m) > 1 and m not in stop}


# ===========================================================================
#  2)  Index vectoriel
# ===========================================================================
class Embedder:
    def __init__(self, textes: list[str]):
        self.textes = textes
        if _a_sentence_transformers():
            from sentence_transformers import SentenceTransformer
            self._modele = SentenceTransformer("all-MiniLM-L6-v2")
            self.matrice = self._modele.encode(textes, normalize_embeddings=True)
            self._dense = True
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vect = TfidfVectorizer(token_pattern=r"[a-zA-Z0-9]{2,}",
                                         lowercase=True)
            self.matrice = self._vect.fit_transform(textes).toarray()
            n = np.linalg.norm(self.matrice, axis=1, keepdims=True)
            self.matrice = self.matrice / np.clip(n, 1e-9, None)
            self._dense = False

    def encoder(self, texte: str) -> np.ndarray:
        if self._dense:
            return self._modele.encode([texte], normalize_embeddings=True)[0]
        v = self._vect.transform([texte]).toarray()[0]
        return v / max(np.linalg.norm(v), 1e-9)


class Search:
    def __init__(self, fragments: list[dict]):
        self.fragments = fragments
        self.emb = Embedder([f["texte"] for f in fragments])

    def chercher(self, requete: str, k: int = 3) -> list[dict]:
        q = self.emb.encoder(requete)
        scores = self.emb.matrice @ q
        ordre = np.argsort(scores)[::-1][:k]
        out = []
        for i in ordre:
            f = dict(self.fragments[i])
            f["score"] = float(scores[i])
            out.append(f)
        return out


def context_recall(recuperes_ids: list[str], attendus_ids: list[str]) -> float:
    if not attendus_ids:
        return 0.0
    return len(set(recuperes_ids) & set(attendus_ids)) / len(attendus_ids)


# ===========================================================================
# 3) Reformulation : tour conversationnel -> query autonome
# ===========================================================================
# A minimal business lexicon for the deterministic resolution of anaphora and
# In real use, the LLM (Ollama) handles this; here, rules are sufficient
# ellipsis. In real use the LLM (Ollama) handles this; here, rules are enough to
# THE PRONOUN SET IS THE MECHANISM, NOT A FILTER.
#
# It decides whether a turn needs anchoring on the entity of the previous one.
# Left in French against English turns it matches nothing, no turn is ever
# anchored, and Lab 30-2 reports a reformulation gain of zero — with no error.
# Chapter 21 depends on the same mechanism.
#
# Kept deliberately NARROW. Anchoring only fires when the question does not name
# an entity itself, so a false positive is mostly harmless; but "the" and "is"
# would match every sentence, so they are excluded.
_PRONOUNS = {"it", "its", "them", "they", "one", "this one", "that one",
             "the latter", "on it", "there"}


_MOTIF_EQUIP = re.compile(r"\b(pump|valve|motor|circuit|bearing|compressor)\s+"
                          r"([a-z]?-?\d+|[a-z]-\d+)", re.IGNORECASE)
# A bare code: 'V-7', 'P-42', 'M-3' — letter, hyphen, digits, with a known prefix.
_SIGLE_TYPE = {"p": "pump", "v": "valve", "m": "motor", "c": "compressor"}
_MOTIF_SIGLE = re.compile(r"\b([PVMC])-(\d+)\b", re.IGNORECASE)


def _entite_dans(texte: str) -> str | None:
    m = _MOTIF_EQUIP.search(texte or "")
    if m:
        return f"{m.group(1).lower()} {m.group(2).upper()}"
    s = _MOTIF_SIGLE.search(texte or "")
    if s:
        lettre = s.group(1).lower()
        return f"{_SIGLE_TYPE.get(lettre, '')} {lettre.upper()}-{s.group(2)}".strip()
    return None


def _derniere_entite(historique: list[dict]) -> str | None:
    """The last equipment entity mentioned in the history."""
    for msg in reversed(historique):
        e = _entite_dans(msg.get("texte", ""))
        if e:
            return e
    return None


def _dernier_theme(historique: list[dict]) -> str | None:
    """The last 'theme' raised: the salient technical keyword of the history.

    These strings are matched against the normalised text of the turns, so they
    must be in the language of the conversation."""
    # NOTE: normaliser() replaces every non-alphanumeric character with a
    # space, so a hyphenated term must be written WITHOUT its hyphen here
    # ("lock off", not "lock-off") or it will never match.
    themes = ["cavitation", "lock off", "leak", "supplier",
              "overheating", "alignment", "greasing", "gasket", "lead time",
              "part"]
    for msg in reversed(historique):
        bas = normaliser(msg.get("texte", ""))
        for t in themes:
            if t in bas:
                return t
    return None


def reformuler(question: str, historique: list[dict]) -> str:
    """Turn a conversational turn into a self-contained query.

    The deterministic fallback anchors the question on the current entity — the
    one the question introduces itself if it does, otherwise the last one in the
    history — and completes the ellipses with the current theme. With Ollama, a
    real LLM reformulator does the work.
    """
    modele = _ollama_modele()
    if modele:
        hist = "\n".join(f"{m['role']}: {m['texte']}" for m in historique[-6:])
        rep = llm(
            "Rewrite the QUESTION as a self-contained, complete search query, "
            "resolving the pronouns and the things left unsaid from the HISTORY. "
            "Answer with the rewritten query ONLY, no preamble.\n"
            f"HISTORY:\n{hist}\n\nQUESTION: {question}")
        if rep:
            return rep.strip().strip('"')

    # --- repli deterministic -------------------------------------------------
    q = question.strip()
    bas = normaliser(q)

    # 1) The reference entity: priority to the one in the current question
    entite_q = _entite_dans(q)
    entite = entite_q or _derniere_entite(historique)

    # An ellipsis opens with the conjunction, "and " here where French had "et ".
    contient_pronom = any(re.search(rf"\b{re.escape(p)}\b", bas) for p in _PRONOUNS)
    est_ellipse = bas.startswith("and ") or len(_mots(q)) <= 2
    besoin_ancrage = contient_pronom or est_ellipse or "supplier" in bas \
        or "date" in bas or "lead time" in bas or "trouble" in bas \
        or "failures" in bas

    requete = q
    # 2) Anchor on the entity, only if it is not already in the question
    ancre = False
    if entite and besoin_ancrage and not entite_q:
        requete = f"{q} {entite}"
        ancre = True
    # 3) Complete the ellipsis with the current theme, if there is no entity and
    #    no pronominal anchoring has already happened
    if est_ellipse and not entite_q and not (ancre and contient_pronom):
        theme = _dernier_theme(historique)
        if theme and theme not in bas:
            requete = f"{requete} {theme}"
    return requete.strip()


# ===========================================================================
# 4) The conversational memory strategies
# ===========================================================================
def _approx_tokens(texte: str) -> int:
    """A rough estimate of the cost in tokens (about the number of words)."""
    return len(texte.split())


class RawMemory:
    """Keep the whole history. An exploding cost, and 'lost in the middle'."""
    nom = "historique brut"

    def __init__(self):
        self.tours: list[dict] = []

    def add(self, role, texte):
        self.tours.append({"role": role, "texte": texte})

    def contexte(self) -> str:
        return " ".join(t["texte"] for t in self.tours)

    def cout(self) -> int:
        return _approx_tokens(self.contexte())


class WindowMemory:
    """A sliding window of the last N turns. Compact but forgetful."""
    nom = "sliding window"

    def __init__(self, n: int = 5):
        self.n = n
        self.tours: deque = deque(maxlen=n)

    def add(self, role, texte):
        self.tours.append({"role": role, "texte": texte})

    def contexte(self) -> str:
        return " ".join(t["texte"] for t in self.tours)

    def cout(self) -> int:
        return _approx_tokens(self.contexte())


class SummaryMemory:
    """A rolling summary: the old is condensed, the recent kept fresh."""
    nom = "rolling summary"

    def __init__(self, garder: int = 3):
        self.garder = garder
        self.summary = ""
        self.recents: deque = deque(maxlen=garder)

    def add(self, role, texte):
        if len(self.recents) == self.garder:
            ancien = self.recents[0]["texte"]
            self.summary = self._summarize(self.summary + " " + ancien)
        self.recents.append({"role": role, "texte": texte})

    def _summarize(self, texte: str) -> str:
        rep = llm(f"Summarise in one sentence, in English:\n{texte}")
        if rep:
            return rep.strip()
        # repli extractif : on garde the firsts words significatifs
        mots = texte.split()
        return " ".join(mots[:25])

    def contexte(self) -> str:
        rec = " ".join(t["texte"] for t in self.recents)
        return (self.summary + " " + rec).strip()

    def cout(self) -> int:
        return _approx_tokens(self.contexte())


class StateMemory:
    """State semantic : a dictionnaire compact of variables persistantes.
 Compact, deterministic, robuste to the conversations longues."""
    nom = "semantic state"

    def __init__(self):
        self.etat: dict[str, str] = {}

    def add(self, role, texte):
        if role == "user" or role == "assistant":
            self.etat = mettre_a_jour_etat(self.etat, texte)

    def contexte(self) -> str:
        return " ".join(f"{k}: {v}" for k, v in self.etat.items())

    def cout(self) -> int:
        return _approx_tokens(self.contexte())


class HybridMemory:
    """The semantic state plus a small recent window: maximum robustness."""
    nom = "hybrid (state + window)"

    def __init__(self, n: int = 2):
        self.etat = StateMemory()
        self.fenetre = WindowMemory(n)

    def add(self, role, texte):
        self.etat.add(role, texte)
        self.fenetre.add(role, texte)

    def contexte(self) -> str:
        return (self.etat.contexte() + " " + self.fenetre.contexte()).strip()

    def cout(self) -> int:
        return _approx_tokens(self.contexte())


# ===========================================================================
#  5)  Routeur conversationnel
# ===========================================================================
def router_tour(question: str, historique: list[dict]) -> str:
    """Classify a turn as 'chitchat', 'followup' or 'search'.

    A lexical fallback; with Ollama, an LLM classifier. It decides whether the
    expensive RAG pipeline should be triggered at all.
    """
    modele = _ollama_modele()
    if modele:
        rep = llm(
            "Classify the question with ONE word among: chitchat, followup, search.\n"
            "- chitchat: politeness, thanks, a trivial clarification;\n"
            "- followup: about the previous answer, no new search needed;\n"
            "- search: requires querying the document base.\n"
            f"Question: {question}\nAnswer:")
        rep = normaliser(rep).split()
        for mot in rep:
            if mot in ("chitchat", "followup", "search"):
                return mot

    bas = normaliser(question)
    # chitchat: thanks, politeness, very short with no technical content.
    # These word sets are the router's mechanism and must be in the language of
    # the conversation; Lab 30-4 prints the classification per turn.
    chitchat = {"thanks", "thank", "hello", "hi", "ok", "great", "perfect",
                "goodbye", "good day", "brilliant", "cheers"}
    # Matched on WHOLE WORDS, not substrings: "hi" is a substring of "this",
    # and a substring test misclassified "How do we repair it, this leak?" as
    # chitchat. French was safe by accident ("merci", "bonjour"); English is not.
    mots_bas = set(bas.split())
    if (mots_bas & chitchat) and len(_mots(question)) <= 2:
        return "chitchat"
    # followup: about the answer itself ("rephrase", "explain", "detail").
    followup_mots = {"rephrase", "reword", "explain", "detail", "clarify",
                     "restate", "summarise", "summarize", "point", "again"}
    if any(m in bas for m in followup_mots):
        return "followup"
    # by default : new search
    return "search"


# ===========================================================================
# 6) State semantic : extraction / update
# ===========================================================================
# THE STATE EXTRACTORS. Each pattern pulls one variable out of the running
# conversation. They match on the wording of the turns in generate_corpus.py, so
# the two must stay in step: a pattern that stops matching leaves its variable
# empty, and the late anaphoric turns of Lab 30-5 resolve to "(absent)" without
# any error being raised.
_MOTIFS_ETAT = [
    ("equipement", re.compile(r"\b(pump|valve|motor|circuit|bearing|compressor)\s+"
                              r"([a-z]?-?\d+|[a-z]-\d+)", re.IGNORECASE)),
    ("probleme", re.compile(r"\b(cavitation|leak|overheating|unbalance|"
                            r"misalignment|wear|jam(?:med)?)\b", re.IGNORECASE)),
    ("fournisseur", re.compile(r"\b(sulzer|ksb|grundfos|eagleburgmann)\b",
                               re.IGNORECASE)),
    ("technicien", re.compile(r"\btechnician\s+(karim|julien|sophie)\b"
                              r"|\b(karim|julien|sophie)\s+(?:takes|assigned)",
                              re.IGNORECASE)),
    ("contrat", re.compile(r"\b(MAINT-\d{4}-\d{3})\b", re.IGNORECASE)),
    ("date", re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")),  # ISO only, unambiguous
    ("cause", re.compile(r"\bcause\s+(?:probable\s+|retained\s+)?(?:is\s+|:\s*)?"
                         r"(?:a\s+|an\s+)?([a-z ]+?)(?:\.|$|,)", re.IGNORECASE)),
]


def mettre_a_jour_etat(etat: dict, texte: str) -> dict:
    """Met to jour a state semantic (dictionnaire) to partir of a message.

 Repli deterministic by motifs ; with Ollama, extraction LLM possible.
    A key is only rewritten when a new value is found, so values persist.
 """
    etat = dict(etat)
    for cle, motif in _MOTIFS_ETAT:
        m = motif.search(texte)
        if m:
            if cle == "equipement":
                etat[cle] = f"{m.group(1).lower()} {m.group(2).upper()}"
            else:
                val = next((g for g in m.groups() if g), m.group(0))
                etat[cle] = val.strip()
    return etat


# ===========================================================================
# 7) Access corpus
# ===========================================================================
def load_fragments(nom: str = "documents.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))


def load_conversation(nom: str = "conversation.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))


def load_long_conversation(nom: str = "conversation_longue.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))
