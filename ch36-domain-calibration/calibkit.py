# -*- coding: utf-8 -*-
"""
calibkit.py — the shared module of the Chapter 36 lab.

The thesis of Chapter 36 — *a large part of the calibration is DEDUCED with no
model at all* — is demonstrated here, deterministically and reproducibly. And the
thesis of the book is verified by a score that rises: the gain of a retrieval
weighted by the business calibration is measured against a naive one.

The chain of the lab: annotate -> pre-annotate -> weight -> measure.

  - deduire_calibration  : the AUTOMATIC part (dates, folder, status) — no model
  - proposer_calibration : the PROPOSED part (an LLM if available, else enriched rules)
  - classer              : naive retrieval (similarity alone) against calibrated

THREE WORD LISTS DRIVE THE AUTOMATIC CALIBRATION, and each is matched against the
metadata or the text of the corpus:

  - _DOSSIER_AUTORITE : maps a folder path fragment to an authority score;
  - _STATUTS_ABROGES  : the statuses that mean "no longer in force";
  - _MOTS_CRITIQUES   : the risk keywords that raise criticality.

All three must stay in step with generate_corpus.py. A folder renamed in the
corpus but not added here falls back to the neutral 0.5, the calibration changes
nothing, and the lab reports recall@1 unchanged — with no error raised.

The TF-IDF vectoriser also needs an English stop list: without it the
interrogatives carry weight, and a FAQ outranked a procedure on a question about
cooling a press.
"""

from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

CORPUS = Path(__file__).resolve().parent / "corpus"

# The "current" date of the lab, fixed for reproducibility.
AUJOURDHUI = date(2026, 6, 26)


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
 An empty string when unavailable makes the lab use its deterministic fallback."""
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
    print("=" * 76)
    print(titre)
    print(f"  Embeddings: {emb}   |   Pre-annotation: {cerveau}")
    print("=" * 76)


# ===========================================================================
# 1) Normalisation and index vector-based
# ===========================================================================
def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texte)


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
            # A stop list is REQUIRED here. Without it the interrogatives carry
            # weight: "how" appears twice in the leave FAQ and once in the press
            # question, and the FAQ outranked the procedure on a question about
            # cooling a press. French got away with it because its content words
            # are more distinctive; English does not.
            self._vect = TfidfVectorizer(token_pattern=r"[a-zA-Z0-9]{2,}",
                                         stop_words="english",
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
    """Index vector-based : returns the cosine similarity of each document."""

    def __init__(self, documents: list[dict]):
        self.documents = documents
        self.emb = Embedder([d["texte"] for d in documents])

    def similarites(self, requete: str) -> np.ndarray:
        q = self.emb.encoder(requete)
        return self.emb.matrice @ q


# ===========================================================================
# 2) The calibration business : a representation manipulable
# ===========================================================================
@dataclass
class Calibration:
    """The operational value of a document, on axes normalised to [0, 1].

      - confiance : can it be trusted? (validated, sound provenance, recent)
      - criticite : what is the risk of being wrong? (safety, compliance)
      - usage     : is it actually consulted or cited? (a usage signal)
      - valide    : is it IN FORCE? (False means superseded, to be set aside)

    Each attribute carries a justification, for auditability (see Chapter 35).
 """
    autorite: float = 0.5
    confiance: float = 0.5
    criticite: float = 0.0
    usage: float = 0.5
    valide: bool = True
    justifs: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"autorite": round(self.autorite, 2),
                "confiance": round(self.confiance, 2),
                "criticite": round(self.criticite, 2),
                "usage": round(self.usage, 2),
                "valide": self.valide}


# --- keywords business for the rules deterministics -----------------------
# THREE WORD LISTS DRIVE THE AUTOMATIC CALIBRATION. Each is matched against the
# METADATA of the documents in generate_corpus.py — the filing folder, the status
# and the text. All three must stay in step with that corpus.
#
# The folder table is the most exposed: it maps a path fragment to an authority
# score. Rename a folder in the corpus without adding its new name here and every
# document falls back to the neutral 0.5. The calibration then changes nothing,
# and Lab 36-1 reports recall@1 unchanged — with no error raised. That is exactly
# what happened when the folders were translated: "/rh/accords/" became
# "/hr/agreements/", and "accords" no longer matched anything.
_DOSSIER_AUTORITE = {
    "validees": 1.0, "valides": 1.0, "validated": 1.0,
    "officiel": 1.0, "official": 1.0,
    "accords": 0.9, "agreements": 0.9,
    "procedures": 0.8, "notes": 0.5, "faq": 0.35,
    "brouillons": 0.15, "projets": 0.2, "drafts": 0.15, "archive": 0.3,
    "safety": 1.0, "securite": 1.0,
    "forum": 0.2, "manuals": 0.5, "manuels": 0.5, "misc": 0.2, "divers": 0.2,
}
_STATUTS_ABROGES = {"abroge", "abrogee", "remplace", "remplacee", "perime",
                    "perimee", "obsolete", "annule", "annulee", "brouillon",
                    "projet", "draft", "superseded", "repealed", "expired",
                    "cancelled"}
_MOTS_CRITIQUES = {"securite", "safety", "surchauffe", "overheating",
                   "arret d urgence", "emergency stop", "danger", "incendie",
                   "fire", "conformite", "compliance", "reglementaire",
                   "regulatory", "opposable", "binding", "obligation",
                   "sanction"}


# ===========================================================================
# 3) STEP A — to deduce the calibration WITHOUT model (the part automatique)
# ===========================================================================
def _anciennete_annees(d: dict) -> float | None:
    iso = d.get("date")
    if not iso:
        return None
    try:
        y, m, j = (int(x) for x in iso.split("-"))
        return (AUJOURDHUI - date(y, m, j)).days / 365.25
    except Exception:
        return None


def deduire_calibration(doc: dict) -> Calibration:
    """The part of the calibration DEDUCIBLE with no model at all — the thesis
    of Chapter 36.

 Use only signals already present: the storage folder, the
    the date, the workflow status, the "supersedes / superseded by" links and a
    possible consultation counter. This is the "free" part of the calibration.
 """
    cal = Calibration()
    justifs = {}

    # --- authority: deduced from the filing folder ---------------------------
    dossier = normaliser(doc.get("dossier", ""))
    auth = 0.5
    for cle, val in _DOSSIER_AUTORITE.items():
        if cle in dossier:
            auth = val
            justifs["autorite"] = f"folder \"{cle}\" -> {val}"
            break
    else:
        justifs["autorite"] = "a neutral folder -> 0.5"
    cal.autorite = auth

    # --- validity: workflow status and replacement links ------------
    statut = normaliser(doc.get("statut", ""))
    remplace_par = doc.get("remplace_par")
    if any(s in statut for s in _STATUTS_ABROGES) or remplace_par:
        cal.valide = False
        raison = remplace_par or statut or "status not in force"
        justifs["valide"] = f"not in force ({raison})"
    else:
        cal.valide = True
        justifs["valide"] = "in force"

    # --- trust : provenance + freshness (obsolescence dates) ------
    conf = 0.6
    prov = normaliser(doc.get("provenance", ""))
    if "officiel" in prov or "interne valide" in prov or "interne validee" in prov:
        conf += 0.3
    if "unverified web" in prov or "unverified external" in prov:
        conf -= 0.4
    age = _anciennete_annees(doc)
    if age is not None:
        # A gentle discount: -0.1 per year beyond one year, floored at 0
        decote = max(0.0, (age - 1.0)) * 0.10
        conf -= decote
        justifs["confiance"] = (f"provenance \"{doc.get('provenance','?')}\", "
                                f"age {age:.1f} year(s) -> discount {decote:.2f}")
    else:
        justifs["confiance"] = f"provenance \"{doc.get('provenance','?')}\""
    cal.confiance = float(np.clip(conf, 0.0, 1.0))

    # --- criticality: risk keywords in the text or the title -----------------
    blob = normaliser(doc.get("titre", "") + " " + doc.get("texte", ""))
    crit = 0.0
    touches = [m for m in _MOTS_CRITIQUES if m in blob]
    if touches:
        crit = min(1.0, 0.4 + 0.2 * len(touches))
        justifs["criticite"] = f"signaux : {', '.join(touches[:3])} -> {crit:.2f}"
    else:
        justifs["criticite"] = "no criticality signal -> 0.0"
    cal.criticite = crit

    # --- usage: consultation count (signal already available) -------
    vues = doc.get("consultations")
    if vues is not None:
        # normalisation log douce : 0 vue -> 0 ; ~200 vues -> ~1
        cal.usage = float(np.clip(math.log1p(vues) / math.log1p(200), 0.0, 1.0))
        justifs["usage"] = f"{vues} consultations -> {cal.usage:.2f}"
    else:
        cal.usage = 0.5
        justifs["usage"] = "pas de signal d'usage -> 0.5"

    cal.justifs = justifs
    return cal


# ===========================================================================
# 4) STEP B — propose the calibration (the inferred part: an LLM, or rules+)
# ===========================================================================
def proposer_calibration(doc: dict, base: Calibration) -> Calibration:
    """Refine the deduced calibration by an inference over the CONTENT.

    With Ollama, an LLM proposes justified adjustments — business criticality,
    perceived authority — that an expert would validate. Without Ollama, a few
    further rules over the text enrich the result. Either way it is a
 PROPOSITION — the validation experte reste hors-line (cf. validate_expert)."""
    modele = _ollama_modele()
    if modele:
        rep = llm(
            "You are calibrating the operational value of a maintenance or HR document. "
            "Donne un JSON {\"criticite\":0..1, \"autorite\":0..1, \"raison\":\"...\"}. "
            "high criticality if safety or compliance; high authority if the document "
            "fait foi.\n"
            f"Titre : {doc.get('titre','')}\nTexte : {doc.get('texte','')[:400]}")
        m = re.search(r"\{.*\}", rep, re.DOTALL)
        if m:
            try:
                d = json.loads(m.group(0))
                cal = Calibration(**{**base.__dict__})
                cal.justifs = dict(base.justifs)
                if "criticite" in d:
                    cal.criticite = float(np.clip(d["criticite"], 0, 1))
                    cal.justifs["criticite"] = f"LLM : {d.get('raison','')[:50]}"
                if "autorite" in d:
                    cal.autorite = float(np.clip(
                        0.5 * cal.autorite + 0.5 * float(d["autorite"]), 0, 1))
                return cal
            except Exception:
                pass
    # The fallback: the model-free deduction is already a good proposal.
    return base


def validate_expert(cal: Calibration, corrections: dict | None) -> Calibration:
    """Apply targeted expert corrections — the 20% that commits you.
 `corrections` : dict optionnel of attributs to forcer, fourni by the corpus."""
    if not corrections:
        return cal
    for k, v in corrections.items():
        if hasattr(cal, k):
            setattr(cal, k, v)
            cal.justifs[k] = f"validation experte -> {v}"
    return cal


def calibrate_corpus(documents: list[dict]) -> dict[str, Calibration]:
    """The complete chain A -> B -> validation, over the whole corpus."""
    cals = {}
    for d in documents:
        base = deduire_calibration(d)
        prop = proposer_calibration(d, base)
        final = validate_expert(prop, d.get("corrections_expertes"))
        cals[d["id"]] = final
    return cals


# ===========================================================================
# 5) STEP C — the weighted score (the formula of Chapter 35)
# ===========================================================================
@dataclass
class Weights:
    alpha: float = 1.0   # similarity semantic
    beta: float = 0.6    # criticality
    gamma: float = 0.8   # confiance
    delta: float = 0.3   # usage
    # A strong penalty if the document is NO LONGER in force (superseded)
    penalite_invalide: float = 1.0
    # The relevance threshold: below it the document is judged off-topic and the
    # calibration cannot "rescue" it. Similarity remains a filter.
    seuil_pertinence: float = 0.05


def score_pondere(similarite: float, cal: Calibration, poids: Weights) -> float:
    """Score = similarity plus the weighted criticality, confidence, usage and
    authority — BUT the similarity
 first acts as a relevance filter.

 Principe (cf. chapitre 35) : the calibration not REMPLACE not the similarity,
    COMPLETES it. An off-topic document, with near-zero similarity, must not be
    able to climb on its criticality or authority alone. Similarity therefore
    stays the foundation, and the calibration only reorders documents that are
    already thematically plausible. A document no longer in force is heavily
    penalised: that is what sets aside the superseded procedure, however close a
    match it looks."""
    if similarite < poids.seuil_pertinence:
        # hors-sujet : on returns a score plancher proportionnel to the similarity
        # Calibration cannot rescue an irrelevant document.
        return poids.alpha * similarite - (poids.penalite_invalide if not cal.valide else 0.0)

    # The calibration MODULE the relevance : the bonus is proportionnel to the
    # the similarity, so a barely relevant document receives only a small bonus,
    # and an off-topic one cannot "win" on its calibration alone. Faithful to the
    # principle: complete the similarity, do not
    # remplacer.
    facteur = (1.0
               + poids.beta * cal.criticite
               + poids.gamma * cal.confiance
               + poids.delta * cal.usage
               + 0.4 * cal.autorite)
    s = poids.alpha * similarite * facteur
    if not cal.valide:
        # A document no longer in force is brought below the level of a valid one
        # of the same relevance: the penalty is proportional to its relevance, so
        # a superseded AND highly relevant document falls all the further.
        s -= poids.penalite_invalide * (1.0 + poids.alpha * similarite * facteur)
    return s


# ===========================================================================
# 6) STEP D — ranking: naive retrieval against calibrated retrieval
# ===========================================================================
def classer_nu(documents, sims, k=5) -> list[dict]:
    """The "naive" retrieval: ranked by semantic similarity alone."""
    ordre = np.argsort(sims)[::-1][:k]
    return [dict(documents[i], score=float(sims[i])) for i in ordre]


def classer_calibre(documents, sims, cals, poids: Weights, k=5) -> list[dict]:
    """The calibrated retrieval: ranked by the weighted score."""
    scores = []
    for i, d in enumerate(documents):
        sc = score_pondere(float(sims[i]), cals[d["id"]], poids)
        scores.append(sc)
    ordre = np.argsort(scores)[::-1][:k]
    return [dict(documents[i], score=float(scores[i])) for i in ordre]


# ===========================================================================
# 7) STEP E — to measure the gain
# ===========================================================================
def recall_at_k(recuperes_ids: list[str], attendus_ids: list[str], k: int) -> float:
    if not attendus_ids:
        return 0.0
    return len(set(recuperes_ids[:k]) & set(attendus_ids)) / len(attendus_ids)


def mrr(recuperes_ids: list[str], attendus_ids: list[str]) -> float:
    for i, did in enumerate(recuperes_ids, start=1):
        if did in attendus_ids:
            return 1.0 / i
    return 0.0


# ===========================================================================
# 8) Access corpus
# ===========================================================================
def load_documents(nom: str = "documents.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))


def load_questions(nom: str = "questions.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))
