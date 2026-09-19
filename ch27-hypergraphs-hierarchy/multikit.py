# -*- coding: utf-8 -*-
"""
multikit.py — the shared module of the Chapter 27 labs.

Everything runs with no API key; the optional tools raise the realism when
present:

    | Embeddings | TF-IDF                  | sentence-transformers if installed |
    | Summaries  | deterministic extractive| Ollama if OLLAMA_MODEL is set      |
    | Clustering | k-means (scikit-learn)  | HDBSCAN if installed               |
    | Hypergraph | an internal dict        | hypernetx if installed             |

The chapter's thesis — *several parallel representations of the same knowledge,
and a router that sends each question to the right one* — stays entirely visible
offline.

A WARNING ON THE ROUTER WORD LISTS (_WORDS, below). They are the mechanism that
chooses the engine, they are matched against the text of the questions, and they
must stay in step with generate_corpus.py. Lab 27-5 measures the accuracy and
prints a confusion matrix; a list that stops matching shows up there as a column
collapsing into "vector", the default. The French baseline is 41/50.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
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


def _a_hdbscan() -> bool:
    try:
        import hdbscan  # noqa: F401
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


def bandeau(titre: str) -> None:
    emb = "sentence-transformers" if _a_sentence_transformers() else "TF-IDF"
    resum = _ollama_modele() or "deterministic extractive"
    clust = "HDBSCAN dispo" if _a_hdbscan() else "k-means"
    print("=" * 74)
    print(titre)
    print(f"  Embeddings: {emb}   |   Summaries: {resum}   |   Clustering: {clust}")
    print("=" * 74)


# ===========================================================================
# 1) Chargement of the corpus
# ===========================================================================
def _load(nom: str):
    f = CORPUS / nom
    if not f.exists():
        raise FileNotFoundError(
            f"corpus/{nom} introuvable — lancez d'abord :  python generate_corpus.py")
    if nom.endswith(".json"):
        return json.loads(f.read_text(encoding="utf-8"))
    return f.read_text(encoding="utf-8")


def load_procedures() -> tuple[list[dict], dict]:
    d = _load("procedures.json")
    return d["procedures"], d["themes"]


def load_inspections() -> list[dict]:
    return _load("inspections.json")["reports"]


def load_turbine_md() -> str:
    return _load("turbine.md")


def load_questions() -> list[dict]:
    return _load("questions.json")["questions"]


def load_cost() -> dict:
    return _load("cost.json")


# ===========================================================================
#  2)  Embeddings + search vectorielle
# ===========================================================================
class Embedder:
    """Vectorise a list of texts. Use TF-IDF by default and embeddings when available."""

    def __init__(self, textes: list[str]):
        self.textes = textes
        self._mode = "embeddings" if _a_sentence_transformers() else "tfidf"
        if self._mode == "embeddings":
            from sentence_transformers import SentenceTransformer
            self._modele = SentenceTransformer("all-MiniLM-L6-v2")
            self.matrice = np.asarray(
                self._modele.encode(textes, normalize_embeddings=True))
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vec = TfidfVectorizer()
            self.matrice = self._vec.fit_transform(textes).toarray()
            # normaliser for produit scalaire = cosinus
            n = np.linalg.norm(self.matrice, axis=1, keepdims=True)
            self.matrice = self.matrice / np.clip(n, 1e-9, None)

    def encode(self, textes: list[str]) -> np.ndarray:
        if self._mode == "embeddings":
            return np.asarray(self._modele.encode(textes, normalize_embeddings=True))
        m = self._vec.transform(textes).toarray()
        n = np.linalg.norm(m, axis=1, keepdims=True)
        return m / np.clip(n, 1e-9, None)


class Search:
    """A simple vector index over a list of documents {id, content, ...}."""

    def __init__(self, documents: list[dict], champ: str = "content"):
        self.documents = documents
        self.emb = Embedder([d[champ] for d in documents])

    def cherche(self, question: str, k: int = 3) -> list[dict]:
        q = self.emb.encode([question])[0]
        scores = self.emb.matrice @ q
        ordre = np.argsort(scores)[::-1][:k]
        return [dict(self.documents[i], score=float(scores[i])) for i in ordre]


# ===========================================================================
# 3) Hypergraph thematic
# ===========================================================================
@dataclass
class Hypergraph:
    """Hyperedges = themes ; each hyperedge relie a groupe of documents."""
    hyperaretes: dict[str, list[str]] = field(default_factory=dict)  # theme -> [doc_id]

    def add(self, theme: str, doc_ids: list[str]) -> None:
        self.hyperaretes[theme] = list(doc_ids)

    def themes_de(self, doc_id: str) -> list[str]:
        return [t for t, membres in self.hyperaretes.items() if doc_id in membres]

    def documents_du_theme(self, theme: str) -> list[str]:
        return self.hyperaretes.get(theme, [])

    def chercher_theme(self, question: str, emb: Embedder) -> tuple[str, list[str]]:
        """Find the hyperedge whose name is closest to the question."""
        if not self.hyperaretes:
            return "", []
        noms = list(self.hyperaretes)
        q = emb.encode([question])[0]
        mat = emb.encode(noms)
        scores = mat @ q
        i = int(np.argmax(scores))
        return noms[i], self.hyperaretes[noms[i]]

    def evaluate_against(self, ground_truth: dict[str, list[str]]) -> dict:
        """Purity: the fraction of documents correctly grouped."""
        # appariement glouton hyperedge extraite -> theme GT by recouvrement max
        total, corrects = 0, 0
        for membres in self.hyperaretes.values():
            total += len(membres)
            meilleur = 0
            for gt in ground_truth.values():
                meilleur = max(meilleur, len(set(membres) & set(gt)))
            corrects += meilleur
        return {"purete": corrects / total if total else 0.0,
                "n_hyperaretes": len(self.hyperaretes)}


def build_hypergraph_themes(documents: list[dict], k: int = 2,
                                  methode: str = "kmeans",
                                  champ: str = "content") -> Hypergraph:
    """Clustering documents -> a hyperedge by cluster. The nom of the theme
 is the terme the more saillant of the cluster (heuristique deterministic)."""
    emb = Embedder([d[champ] for d in documents])
    X = emb.matrice

    if methode == "hdbscan" and _a_hdbscan():
        import hdbscan
        lab = hdbscan.HDBSCAN(min_cluster_size=2).fit_predict(X)
    else:
        from sklearn.cluster import KMeans
        lab = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)

    clusters: dict[int, list[int]] = defaultdict(list)
    for i, c in enumerate(lab):
        if c == -1:           # bruit HDBSCAN
            continue
        clusters[int(c)].append(i)

    hg = Hypergraph()
    for c, idx in clusters.items():
        nom = f"theme_{c}"
        hg.add(nom, [documents[i]["id"] for i in idx])
    return hg


# ===========================================================================
# 4) Summary extractif deterministic (or Ollama)
# ===========================================================================
def _phrases(texte: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", texte.strip())
    return [p.strip() for p in parts if p.strip()]


def summarize(texte: str, n: int = 2) -> str:
    """Summary extractif : on garde the n sentences the more centrales (similarity
 moyenne to the other). Deterministic. With Ollama, true summary abstractif."""
    modele = _ollama_modele()
    if modele:
        try:
            import ollama
            prompt = f"Summarise this text in {n} sentences, in English:\n{texte}"
            return ollama.generate(model=modele, prompt=prompt)["response"].strip()
        except Exception:
            pass  # repli extractif
    phrases = _phrases(texte)
    if len(phrases) <= n:
        return " ".join(phrases)
    emb = Embedder(phrases)
    sim = emb.matrice @ emb.matrice.T
    centralite = sim.sum(axis=1)
    top = sorted(np.argsort(centralite)[::-1][:n])  # garder the ordre of the texte
    return " ".join(phrases[i] for i in top)


# ===========================================================================
# 5) Tree documentaire + index hierarchical (RAPTOR-like)
# ===========================================================================
@dataclass
class Node:
    titre: str
    niveau: int
    contenu: str = ""
    enfants: list["Node"] = field(default_factory=list)
    summary: str = ""


class DocTree:
    """Parse a Markdown to titles (#, ##, ###, ####) in tree."""

    def __init__(self, markdown: str):
        self.racine = Node(titre="(racine)", niveau=0)
        self._parser(markdown)

    def _parser(self, md: str) -> None:
        pile = [self.racine]
        for ligne in md.splitlines():
            m = re.match(r"^(#{1,6})\s+(.*)$", ligne)
            if m:
                niveau = len(m.group(1))
                noeud = Node(titre=m.group(2).strip(), niveau=niveau)
                while pile and pile[-1].niveau >= niveau:
                    pile.pop()
                (pile[-1] if pile else self.racine).enfants.append(noeud)
                pile.append(noeud)
            else:
                if len(pile) > 1 and ligne.strip():
                    pile[-1].contenu += (" " if pile[-1].contenu else "") + ligne.strip()

    def parcours(self) -> list[Node]:
        out: list[Node] = []
        def rec(n: Node):
            for e in n.enfants:
                out.append(e); rec(e)
        rec(self.racine)
        return out

    def summarize_recursively(self) -> None:
        """RAPTOR: each parent node receives a summary of its children, bottom-up."""
        def rec(n: Node) -> str:
            for e in n.enfants:
                rec(e)
            propre = n.contenu
            enfants = " ".join(e.summary for e in n.enfants if e.summary)
            base = (propre + " " + enfants).strip()
            n.summary = summarize(base, n=2) if base else n.titre
            return n.summary
        rec(self.racine)


@dataclass
class HierarchicalIndex:
    """Index multi-levelx : fragments (feuilles), summaries of section, summary
    global. The retrieval can land at the right level, according to the scope."""
    fragments: list[dict] = field(default_factory=list)   # niveau 0
    sections: list[dict] = field(default_factory=list)    # level summary
    global_: dict = field(default_factory=dict)           # racine

    @classmethod
    def depuis_arbre(cls, arbre: DocTree) -> "HierarchicalIndex":
        arbre.summarize_recursively()
        idx = cls()
        for n in arbre.parcours():
            if n.contenu:
                idx.fragments.append({"id": n.titre, "content": n.contenu,
                                      "niveau": n.niveau})
            if n.enfants:  # node interne -> summary of section
                idx.sections.append({"id": f"summary:{n.titre}", "content": n.summary,
                                     "niveau": n.niveau})
        racine = arbre.racine
        idx.global_ = {"id": "global summary",
                       "content": summarize(" ".join(e.summary for e in racine.enfants), n=3),
                       "niveau": 0}
        return idx

    def search(self, question: str, niveau: str) -> dict:
        """niveau ∈ {'fragment','section','global'}."""
        if niveau == "global":
            return self.global_
        pool = self.fragments if niveau == "fragment" else self.sections
        if not pool:
            return self.global_
        r = Search(pool)
        return r.cherche(question, k=1)[0]


# ===========================================================================
# 6) Graph of tree (Dependencies structurelles parent/enfant)
# ===========================================================================
class GraphTree:
    """Graph of Dependencies structurelles issu of the tree documentaire."""

    def __init__(self, arbre: DocTree):
        self.enfants: dict[str, list[str]] = defaultdict(list)
        self.parent: dict[str, str] = {}
        def rec(n: Node):
            for e in n.enfants:
                self.enfants[n.titre].append(e.titre)
                self.parent[e.titre] = n.titre
                rec(e)
        rec(arbre.racine)

    def composants_de(self, titre: str) -> list[str]:
        return list(self.enfants.get(titre, []))

    def depend_de(self, a: str, b: str) -> bool:
        """Does a depend, structurally, on b? That is, is b an ancestor of a?"""
        cur = self.parent.get(a)
        while cur:
            if cur == b:
                return True
            cur = self.parent.get(cur)
        return False


# ===========================================================================
# 7) The multi-resolution router
# ===========================================================================
# THE ROUTER WORD LISTS. Each set of markers votes for one engine; two or more
# active sets mean "mixed". They are matched against the text of the questions,
# so they must be in the corpus language and match the wording of the 50
# questions in generate_corpus.py.
#
# Lab 27-5 measures the accuracy and prints a confusion matrix. The French
# baseline is 41/50. A list that stops matching shows up there as a column
# collapsing into "vector", the default — never as an error.
_WORDS = {
    "hierarchy": ["describe", "operation", "general", "overview", "synthesis",
                   "architecture", "main parts", "structure", "summary",
                   "summarise", "present ", "manual", "chapter on",
                   "sub-assemblies are described"],
    "hypergraph": ["theme", "themes", "thematic", "continuity", "compliance",
                    "participate", "come under", "deal with", "crossing",
                    "contribute", "share an objective", "share the",
                    "broad sense", "regulation", "converge"],
    "graph": ["depend", "depends", "components", "belong", "contains the",
               "linked to", "sub-assembly", "downstream", "compose",
               "elements compose"],
}


def routeur_multiresolution(question: str) -> str:
    """vectoriel | graphe | hypergraphe | hierarchie | mixte."""
    modele = _ollama_modele()
    if modele:
        r = _routeur_llm(question, modele)
        if r in {"vector", "graph", "hypergraph", "hierarchy", "mixed"}:
            return r
    bas = question.lower()
    score = {m: sum(1 for w in words if w in bas) for m, words in _WORDS.items()}
    actifs = [m for m, s in score.items() if s > 0]
    if len(actifs) >= 2:
        return "mixed"
    if actifs:
        return actifs[0]
    return "vector"


def _routeur_llm(question: str, modele: str) -> str:
    import ollama
    prompt = (
        "Classify the question into ONE category: vectoriel, graphe, hypergraphe, "
        "hierarchie, mixte.\n"
        "- vectoriel: a precise fact inside a fragment.\n"
        "- graphe: a dependency or composition between entities.\n"
        "- hypergraphe: a crossing theme grouping documents.\n"
        "- hierarchie: navigation or synthesis of a section or the document.\n"
        "- mixte: combines several of the above.\n"
        f"Question: {question}\nAnswer with a single word."
    )
    try:
        rep = ollama.generate(model=modele, prompt=prompt)["response"].strip().lower()
        for cat in ("mixed", "hypergraph", "hierarchy", "graph", "vector"):
            if cat in rep:
                return cat
    except Exception:
        pass
    return ""


# ===========================================================================
# 8) Accounting of the cost
# ===========================================================================
@dataclass
class Counter:
    documents_lus: int = 0
    noeuds_visites: int = 0
    cout: float = 0.0
    latence_ms: float = 0.0

    def ajoute(self, *, docs: int = 0, nodes: int = 0,
               cout: float = 0.0, latence: float = 0.0) -> None:
        self.documents_lus += docs
        self.noeuds_visites += nodes
        self.cout += cout
        self.latence_ms += latence

    def summary(self) -> str:
        return (f"docs={self.documents_lus}  nodes={self.noeuds_visites}  "
                f"cost={self.cout:.1f}  latency={self.latence_ms:.0f}ms")


def cout_de(moteur: str, modele_cout: dict) -> tuple[float, float]:
    """(query cost, latency in ms) of an engine, according to the cost model."""
    c = modele_cout["par_requete"].get(moteur, 1.0)
    l = modele_cout["latence_ms"].get(moteur, 10)
    return c, float(l)
