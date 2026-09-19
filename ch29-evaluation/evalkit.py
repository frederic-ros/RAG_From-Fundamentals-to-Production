# -*- coding: utf-8 -*-
"""
evalkit.py — the shared module of the Chapter 29 labs
(evaluation: proving that a RAG is not drifting).

The chapter's thesis — *evaluation stops being an impression and becomes a
measurement* — stays entirely visible offline, and reproducibly.

A WARNING ON THE THRESHOLDS. Several constants in this chapter are compared
against lexical overlap scores: the support threshold (0.6) below, the strict
judge (0.7) and the verdict (0.6) in Lab 29-3, the abstention threshold (0.30)
in Lab 29-7, and the drift thresholds in Lab 29-4. Those constants were
calibrated on the score distribution of the FRENCH corpus. Translating the
corpus shifts that distribution, and a threshold can end up on the wrong side of
it without anything breaking.

Two cases were found and fixed when this chapter was translated:
  - the out-of-corpus question (G09) scored ABOVE the abstention threshold, so
    the one case abstention exists for sailed through while a legitimate case
    abstained instead;
  - the multi-hop case (G10) lost its second fragment to a distractor, because
    English does not inflect verbs the way French does.

If you edit a question or a document, re-run Labs 29-1, 29-3 and 29-7 and check
the figures against the baselines recorded in their headers.
"""

from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from dataclasses import dataclass, field
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
    juge = _ollama_modele() or "deterministic judge (fact overlap)"
    print("=" * 74)
    print(titre)
    print(f"  Embeddings : {emb}   |   Juge : {juge}")
    print("=" * 74)


# ===========================================================================
# 1) Normalisation and sentences
# ===========================================================================
def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texte)


def _phrases(texte: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", texte.strip())
    return [p.strip() for p in parts if p.strip()]


def _mots(texte: str) -> set[str]:
    # THIS STOP LIST IS A MECHANISM, not decoration. _mots() feeds the fidelity
    # judge, the relevance score and the context recall, all three by term
    # overlap. Left in French against an English corpus it filters almost
    # nothing, every grammatical word counts as content, and all three scores
    # drift upwards together — with no error raised.
    stop = {"the", "and", "for", "with", "that", "this", "these", "those",
            "are", "was", "were", "not", "but", "you", "your", "our", "its",
            "can", "will", "would", "should", "must", "have", "has", "had",
            "any", "all", "which", "what", "when", "where", "who",
            "from", "into", "than", "then", "there", "here", "such", "each"}
    return {m for m in normaliser(texte).split() if len(m) > 2 and m not in stop}


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

    def chercher(self, requete: str, k: int = 5) -> list[dict]:
        q = self.emb.encoder(requete)
        scores = self.emb.matrice @ q
        ordre = np.argsort(scores)[::-1][:k]
        out = []
        for i in ordre:
            f = dict(self.fragments[i])
            f["score"] = float(scores[i])
            out.append(f)
        return out


# ===========================================================================
# 3) Metrics of retrieval : recall@k, MRR, nDCG
# ===========================================================================
def recall_at_k(recuperes: list[str], relevant: list[str], k: int) -> float:
    if not relevant:
        return 0.0
    top = recuperes[:k]
    return len(set(top) & set(relevant)) / len(relevant)


def mrr(recuperes: list[str], relevant: list[str]) -> float:
    """Mean Reciprocal Rank for A query : 1/rank of the 1er relevant."""
    for i, doc in enumerate(recuperes, start=1):
        if doc in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(recuperes: list[str], relevant: list[str], k: int) -> float:
    """Binary nDCG (gain 1 if relevant, 0 otherwise)."""
    dcg = 0.0
    for i, doc in enumerate(recuperes[:k], start=1):
        if doc in relevant:
            dcg += 1.0 / math.log2(i + 1)
    ideal = sum(1.0 / math.log2(i + 1)
                for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal > 0 else 0.0


# ===========================================================================
# 4) Pipeline RAG jouable hors-line (retrieval + generation extractive)
# ===========================================================================
@dataclass
class RAGAnswer:
    question: str
    reponse: str
    fragments: list[dict] = field(default_factory=list)
    abstention: bool = False


class RAGPipeline:
    """RAG minimal and reproductible : retrieval vector-based + generation
    extractive: the sentences of the fragments that answer best are assembled.
    With Ollama the generation becomes a real LLM call, grounded on the context.

    The `threshold_abstention` parameter allows the coverage-against-reliability
    trade-off to be studied (Lab 29-5): if the best retrieval score is too low,
 system abstient rather than of to answer at the hasard.
 """

    def __init__(self, fragments: list[dict], k: int = 3,
                 seuil_abstention: float = 0.0):
        self.fragments = fragments
        self.rech = Search(fragments)
        self.k = k
        self.threshold = seuil_abstention

    def repondre(self, question: str) -> RAGAnswer:
        trouves = self.rech.chercher(question, k=self.k)
        meilleur = trouves[0]["score"] if trouves else 0.0
        if meilleur < self.threshold:
            return RAGAnswer(question, "I do not have reliable material with "
                              "which to answer.", trouves, abstention=True)

        contexte = " ".join(f["texte"] for f in trouves)
        rep_llm = llm(
            "Answer the question ONLY from the context. If the context does not "
            "hold the answer, say so.\n"
            f"Context: {contexte}\nQuestion: {question}\nAnswer:")
        if rep_llm:
            return RAGAnswer(question, rep_llm, trouves)

        # repli extractif : sentences of the context the closest of the question
        phrases = [p for f in trouves for p in _phrases(f["texte"])]
        if not phrases:
            return RAGAnswer(question, "No material.", trouves, abstention=True)
        emb = Embedder(phrases + [question])
        q = emb.matrice[-1]
        sims = emb.matrice[:-1] @ q
        ordre = np.argsort(sims)[::-1][:2]
        reponse = " ".join(phrases[i] for i in sorted(ordre))
        return RAGAnswer(question, reponse, trouves)


# ===========================================================================
# 5) LLM-as-a-Judge : fidelity, relevance (with repli deterministic)
# ===========================================================================
def juge_fidelite(reponse: str, contexte: str) -> float:
    """Fidelity (faithfulness) : part affirmations of the answer soutenues
 by the context. Scale binaire sentence by sentence (recommandation of the
 chapitre). With Ollama : true juge LLM with Chain-of-Thought."""
    phrases = _phrases(reponse)
    if not phrases:
        return 0.0

    modele = _ollama_modele()
    if modele:
        soutenues = 0
        for ph in phrases:
            rep = llm(
                "Answer YES or NO only.\n"
                f"Contexte : {contexte}\n"
                f"Is the following statement supported by the context? "
                f"\"{ph}\"")
            if rep and rep.strip().lower().startswith("oui"):
                soutenues += 1
        return soutenues / len(phrases)

    # Deterministic fallback: a sentence is supported if most of its words
    # significatifs se refinds in the context.
    mots_ctx = _mots(contexte)
    soutenues = 0
    for ph in phrases:
        mots_ph = _mots(ph)
        if not mots_ph:
            continue
        recouvrement = len(mots_ph & mots_ctx) / len(mots_ph)
        if recouvrement >= 0.6:
            soutenues += 1
    return soutenues / len(phrases)


def cohen_kappa(labels_humain: list[str], labels_juge: list[str]) -> float:
    """Cohen's Kappa : accord between deux annotateurs (ici, a humain and a
    judge) beyond what chance would already produce. 1.0 is perfect agreement,
    0.0 means agreement no better than chance; negative means worse than chance.
    Used to calibrate an LLM judge before trusting it at
    scale (Chapter 29)."""
    assert len(labels_humain) == len(labels_juge)
    n = len(labels_humain)
    categories = sorted(set(labels_humain) | set(labels_juge))

    # Observed agreement: the proportion of cases where the two annotators concur
    accord_observe = sum(
        1 for h, j in zip(labels_humain, labels_juge) if h == j) / n

    # Agreement expected by chance: based on the marginal distribution of each
    # annotateur (formule standard du kappa de Cohen)
    accord_hasard = 0.0
    for cat in categories:
        p_humain = labels_humain.count(cat) / n
        p_juge = labels_juge.count(cat) / n
        accord_hasard += p_humain * p_juge

    if accord_hasard == 1.0:
        return 1.0  # a degenerate case: a single category used throughout
    return (accord_observe - accord_hasard) / (1 - accord_hasard)



def juge_pertinence(reponse: str, question: str) -> float:
    """Relevance of the answer (answer relevancy) : the answer adresse-t-it
 the question ? Repli : similarity lexicale question/answer."""
    modele = _ollama_modele()
    if modele:
        rep = llm("Rate from 0 to 10 how well the answer addresses the question. "
                  "Donne UNIQUEMENT le nombre.\n"
                  f"Question: {question}\nAnswer: {reponse}")
        m = re.search(r"\d+(?:[.,]\d+)?", rep)
        if m:
            return min(float(m.group().replace(",", ".")) / 10.0, 1.0)
    mq, mr = _mots(question), _mots(reponse)
    if not mq:
        return 0.0
    return len(mq & mr) / len(mq)


def context_recall(contexte: str, reference: str) -> float:
    """Context recall : the answer of reference is-it couverte by the
    retrieved context? A deterministic proxy, by keyword overlap."""
    mots_ref = _mots(reference)
    if not mots_ref:
        return 0.0
    return len(mots_ref & _mots(contexte)) / len(mots_ref)


# ===========================================================================
#  6)  Indicateurs montants : abstention, attribution
# ===========================================================================
def taux_abstention(reponses: list[RAGAnswer]) -> float:
    if not reponses:
        return 0.0
    return sum(1 for r in reponses if r.abstention) / len(reponses)


def taux_attribution(reponses: list[RAGAnswer]) -> float:
    """The share of answers (non-abstaining) supported by at least one fragment
    actually used, with a score above 0."""
    rep = [r for r in reponses if not r.abstention]
    if not rep:
        return 0.0
    attribues = sum(1 for r in rep
                    if r.fragments and r.fragments[0]["score"] > 0)
    return attribues / len(rep)


# ===========================================================================
# 7) Access corpus / golden set
# ===========================================================================
def load_fragments(nom: str = "documents.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))


def load_golden(nom: str = "golden_set.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))
