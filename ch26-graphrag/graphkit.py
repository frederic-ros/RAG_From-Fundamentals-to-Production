# -*- coding: utf-8 -*-
"""
graphkit.py — the shared module of the Chapter 26 labs (GraphRAG).

Built on the same principle as the rest of the book: everything runs WITH NO API
key and no network, while allowing the labs to be "moved up a gear" if the
optional tools are present.

The chapter's thesis — *the vector finds documents, the graph finds paths* — is
made entirely visible offline, and reproducibly.

What this module supplies:

  - Graph            : a directed in-memory graph (neighbours, paths, communities)
  - extract_triples  : rule-based extraction by default, Ollama on request
  - global_search    : community summaries, for aggregation
  - vectorcypher     : a vector entry point, then a graph traversal
  - routeur_complexite: chooses the strategy from linguistic signals

TWO MECHANISMS IN THIS FILE ARE LANGUAGE-BOUND, and both are measured:

  1. _PATTERNS maps verb phrases to relation labels. The labels must match
     EXPECTED_TRIPLES in generate_corpus.py. Lab 26-2 prints precision, recall
     and F1 (French baseline: 1.00 / 0.73 / 0.84).
  2. The three router word lists decide the strategy. Lab 26-5 prints the routing
     accuracy over the 25 questions (French baseline: 22/25).

Run either lab after touching a list: a broken link shows up as a collapsed
score, never as an error.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np

CORPUS = Path(__file__).resolve().parent / "corpus"


# ===========================================================================
# 0) Detection outils optionnels (never obligatoires)
# ===========================================================================
def _a_sentence_transformers() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def _a_networkx() -> bool:
    try:
        import networkx  # noqa: F401
        return True
    except Exception:
        return False


def _ollama_modele() -> str | None:
    """Return the name of the Ollama model if requested AND available, else None."""
    modele = os.environ.get("OLLAMA_MODEL")
    if not modele:
        return None
    try:
        import ollama  # noqa: F401
        return modele
    except Exception:
        return None


def bandeau(titre: str) -> None:
    """in-head of TP : rcalls the mode (repli vs usage real)."""
    emb = "sentence-transformers" if _a_sentence_transformers() else "TF-IDF"
    cerveau = _ollama_modele() or "deterministic rules"
    graphe = "networkx" if _a_networkx() else "interne"
    print("=" * 72)
    print(titre)
    print(f"  Embeddings : {emb}   |   Extraction : {cerveau}   |   Graph : {graphe}")
    print("=" * 72)


# ===========================================================================
# 1) Chargement of the corpus
# ===========================================================================
def load_documents() -> list[dict]:
    f = CORPUS / "fragments.json"
    if not f.exists():
        raise FileNotFoundError(
            "corpus/fragments.json introuvable — lancez d'abord :  python generate_corpus.py")
    return json.loads(f.read_text(encoding="utf-8"))["documents"]


def load_questions() -> list[dict]:
    f = CORPUS / "questions.json"
    if not f.exists():
        raise FileNotFoundError(
            "corpus/questions.json introuvable — lancez d'abord :  python generate_corpus.py")
    return json.loads(f.read_text(encoding="utf-8"))["questions"]


def load_expected_graph() -> list[list[str]]:
    f = CORPUS / "expected_graph.json"
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8"))["triplets"]


# ===========================================================================
# 2) Search vector-basedle (TF-IDF by default, embeddings si dispo)
# ===========================================================================
class Search:
    """A simple vector index over a list of documents {id, content, ...}."""

    def __init__(self, documents: list[dict]):
        self.documents = documents
        self.textes = [d["content"] for d in documents]
        self._mode = "embeddings" if _a_sentence_transformers() else "tfidf"
        if self._mode == "embeddings":
            from sentence_transformers import SentenceTransformer
            self._modele = SentenceTransformer("all-MiniLM-L6-v2")
            self._mat = self._modele.encode(self.textes, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vec = TfidfVectorizer()
            self._mat = self._vec.fit_transform(self.textes)

    def cherche(self, question: str, k: int = 3) -> list[dict]:
        if self._mode == "embeddings":
            q = self._modele.encode([question], normalize_embeddings=True)
            scores = (self._mat @ q[0])
        else:
            from sklearn.metrics.pairwise import cosine_similarity
            q = self._vec.transform([question])
            scores = cosine_similarity(q, self._mat)[0]
        ordre = np.argsort(scores)[::-1][:k]
        return [dict(self.documents[i], score=float(scores[i])) for i in ordre]


# ===========================================================================
# 3) Triple extraction (rules by default, Ollama on request)
# ===========================================================================
# The vocabulary of relations the deterministic extractor recognises. The
# The point of the chapter is that THIS step is the difficult one: expose it
# lesson is shown in the open, rather than hidden behind an API.
# THE EXTRACTION PATTERNS. Each pattern maps a verb phrase found in the documents
# onto a relation label. The labels MUST match those of EXPECTED_TRIPLES in
# generate_corpus.py, and the patterns must match the wording of the documents.
# Break either link and the extraction score collapses with no error: Lab 26-2
# would simply report a recall of 0.
#
# Order matters: "manufactured by" is tested before "manufactures", otherwise the
# passive form would be caught by the active pattern.
_PATTERNS = [
    (r"\bfeeds\b", "feeds"),
    (r"\bmanufactured\s+by\b", "manufactured_by"),
    (r"\bmanufactures\b", "manufactures"),
    (r"\b(?:is\s+)?linked\s+to\b", "linked_to"),
    (r"\b(?:are\s+)?supplied\s+by\b", "parts_supplied_by"),
    (r"\bmaintenance\s+(?:of\s+\S+\s+)?(?:is\s+)?carried\s+out\s+by\b", "maintained_by"),
    (r"\breplaces\b", "replaces"),
]

# Entities connues of the domaine (ancrage deterministic). in usage real, it is the LLM
# would discover the entities; here it is bounded, to stay reproducible.
_ENTITIES = [
    "P-42", "E-7", "L-3", "L-5", "P-17", "R-2",
    "product X", "product Y", "Rexel", "team B",
    "contract 2024-07", "procedure SE-12", "procedure SE-09",
]


def _normalise(txt: str) -> str:
    txt = unicodedata.normalize("NFC", txt)
    return re.sub(r"\s+", " ", txt).strip()


def _entites_presentes(phrase: str) -> list[str]:
    bas = phrase.lower()
    trouve = []
    for e in _ENTITIES:
        if e.lower() in bas:
            trouve.append(e)
    # garder l'ordre d'apparition
    return sorted(set(trouve), key=lambda e: bas.find(e.lower()))


def _extract_rules(document: dict) -> list[tuple[str, str, str]]:
    """Extraction deterministic : sentence by sentence, we look for a relation and
 on relie the deux entities the closest of part and of other of the verbe."""
    triplets: list[tuple[str, str, str]] = []
    for phrase in re.split(r"[.;]", document["content"]):
        phrase = _normalise(phrase)
        if not phrase:
            continue
        ents = _entites_presentes(phrase)
        if len(ents) < 2:
            continue
        bas = phrase.lower()
        for patron, relation in _PATTERNS:
            m = re.search(patron, bas)
            if not m:
                continue
            pos = m.start()
            avant = [e for e in ents if bas.find(e.lower()) < pos]
            apres = [e for e in ents if bas.find(e.lower()) >= pos]
            if avant and apres:
                sujet = max(avant, key=lambda e: bas.find(e.lower()))
                objet = min(apres, key=lambda e: bas.find(e.lower()))
                triplets.append((sujet, relation, objet))
                break  # a relation by sentence suffit for the demonstration
    return triplets


def _extract_ollama(document: dict, modele: str) -> list[tuple[str, str, str]]:
    """Extraction by LLM local. The LLM can se tromper : it is precisely the
    the teaching point of Lab 26-2: "the hard part is the extraction"."""
    import ollama
    prompt = (
        "Extract the triples (subject, relation, object) from the text.\n"
        "Answer in JSON ONLY: [[\"subject\",\"relation\",\"object\"], ...].\n"
        f"Texte : {document['content']}"
    )
    try:
        rep = ollama.generate(model=modele, prompt=prompt)["response"]
        m = re.search(r"\[.*\]", rep, re.S)
        data = json.loads(m.group(0)) if m else []
        return [(str(a), str(b), str(c)) for a, b, c in data if len([a, b, c]) == 3]
    except Exception:
        # If the LLM fails, fall back on the rules: the labs stay runnable.
        return _extract_rules(document)


def extract_triples(documents: Iterable[dict]) -> list[tuple[str, str, str]]:
    """The single entry point. Uses Ollama if OLLAMA_MODEL is set, otherwise
 the rules deterministics."""
    modele = _ollama_modele()
    tous: list[tuple[str, str, str]] = []
    for d in documents:
        if modele:
            tous.extend(_extract_ollama(d, modele))
        else:
            tous.extend(_extract_rules(d))
    # Deduplicate while keeping the order
    vu, uniques = set(), []
    for t in tous:
        if t not in vu:
            vu.add(t)
            uniques.append(t)
    return uniques


# ===========================================================================
# 4) The graph in memory
# ===========================================================================
@dataclass
class Graph:
    """A minimal directed graph. If networkx is present, it is also exposed via
    .to_networkx(), for visualisation and the more advanced algorithms."""
    aretes: list[tuple[str, str, str]] = field(default_factory=list)  # (sujet, relation, objet)
    _adj: dict[str, list[tuple[str, str]]] = field(default_factory=lambda: defaultdict(list))
    _adj_inv: dict[str, list[tuple[str, str]]] = field(default_factory=lambda: defaultdict(list))

    @classmethod
    def depuis_triplets(cls, triplets: Iterable[tuple[str, str, str]]) -> "Graph":
        g = cls()
        for s, r, o in triplets:
            g.add(s, r, o)
        return g

    def add(self, sujet: str, relation: str, objet: str) -> None:
        self.aretes.append((sujet, relation, objet))
        self._adj[sujet].append((relation, objet))
        self._adj_inv[objet].append((relation, sujet))

    @property
    def nodes(self) -> set[str]:
        n: set[str] = set()
        for s, _, o in self.aretes:
            n.add(s); n.add(o)
        return n

    def voisins(self, noeud: str) -> list[tuple[str, str]]:
        """(relation, voisin) en aval."""
        return list(self._adj.get(noeud, []))

    def voisins_amont(self, noeud: str) -> list[tuple[str, str]]:
        """(relation, voisin) in amont — for remonter toward the fournisseurs."""
        return list(self._adj_inv.get(noeud, []))

    def path(self, depart: str, arrivee: str, max_sauts: int = 6) -> list[str] | None:
        """The shortest directed path from start to goal, by BFS."""
        if depart == arrivee:
            return [depart]
        file = deque([(depart, [depart])])
        vus = {depart}
        while file:
            courant, route = file.popleft()
            if len(route) > max_sauts:
                continue
            for _, voisin in self._adj.get(courant, []):
                if voisin == arrivee:
                    return route + [voisin]
                if voisin not in vus:
                    vus.add(voisin)
                    file.append((voisin, route + [voisin]))
        return None

    def descendants(self, depart: str, profondeur: int = 3) -> list[str]:
        """Tous the nodes atteignables in aval (Dependencies) jusqu'to `profondeur`."""
        out, file, vus = [], deque([(depart, 0)]), {depart}
        while file:
            courant, prof = file.popleft()
            if prof >= profondeur:
                continue
            for _, voisin in self._adj.get(courant, []):
                if voisin not in vus:
                    vus.add(voisin)
                    out.append(voisin)
                    file.append((voisin, prof + 1))
        return out

    def communautes(self) -> dict[str, list[str]]:
        """Weakly connected components — the minimal analogue of "communities"
 of GraphRAG. in production : Leiden or Louvain (cf. chapitre)."""
        parent: dict[str, str] = {n: n for n in self.nodes}

        def trouve(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for s, _, o in self.aretes:
            parent[trouve(s)] = trouve(o)
        groupes: dict[str, list[str]] = defaultdict(list)
        for n in self.nodes:
            groupes[trouve(n)].append(n)
        return {f"communaute_{i}": sorted(v)
                for i, v in enumerate(sorted(groupes.values(), key=len, reverse=True))}

    def to_networkx(self):
        import networkx as nx
        g = nx.DiGraph()
        for s, r, o in self.aretes:
            g.add_edge(s, o, label=r)
        return g

    def evaluate_against(self, attendus: list[list[str]]) -> dict:
        """Precision / recall of the extraction contre the ground truth."""
        extraits = {(s, r, o) for s, r, o in self.aretes}
        ref = {(s, r, o) for s, r, o in attendus}
        vp = len(extraits & ref)
        precision = vp / len(extraits) if extraits else 0.0
        recall = vp / len(ref) if ref else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        return {"precision": precision, "recall": recall, "f1": f1,
                "vrais_positifs": vp, "extraits": len(extraits), "attendus": len(ref)}


# ===========================================================================
# 5) The search strategies over the graph
# ===========================================================================
def local_search(graphe: Graph, entites: list[str], profondeur: int = 2) -> dict:
    """The neighbourhood of one or more entities. Returns visited nodes and facts."""
    visites: set[str] = set()
    faits: list[str] = []
    for e in entites:
        visites.add(e)
        for voisin in graphe.descendants(e, profondeur):
            visites.add(voisin)
        for relation, voisin in graphe.voisins(e):
            faits.append(f"{e} {relation} {voisin}")
            visites.add(voisin)
    return {"strategie": "local", "nodes": sorted(visites), "faits": faits,
            "n_noeuds": len(visites)}


def global_search(graphe: Graph) -> dict:
    """Community summaries — for aggregation questions."""
    communautes = graphe.communautes()
    resumes = []
    for nom, membres in communautes.items():
        # A minimal "summary": the most connected member, plus the size
        degre = {m: len(graphe.voisins(m)) + len(graphe.voisins_amont(m)) for m in membres}
        pivot = max(membres, key=lambda m: degre[m]) if membres else "?"
        resumes.append({"communaute": nom, "taille": len(membres),
                        "pivot": pivot, "membres": membres})
    resumes.sort(key=lambda r: r["taille"], reverse=True)
    return {"strategie": "global", "communautes": resumes,
            "n_noeuds": len(graphe.nodes)}


def vector_cypher(question: str, search: Search, graphe: Graph,
                  profondeur: int = 3, k: int = 3) -> dict:
    """The pattern gagnant : the vector finds the POINTS of INPUT, the graph
    WIDENS by following the relations, downstream AND upstream."""
    # 1) input vector-basedle
    docs = search.cherche(question, k=k)
    # 2) Which entities appear in the documents found?
    entrees = []
    for d in docs:
        for e in _entites_presentes(d["content"]):
            if e not in entrees:
                entrees.append(e)
    # 3) expansion graph : aval (Dependencies) + amont (fournisseurs)
    sous_graphe: list[str] = []
    nodes: set[str] = set(entrees)
    for e in entrees:
        for voisin in graphe.descendants(e, profondeur):
            nodes.add(voisin)
        for relation, voisin in graphe.voisins(e):
            sous_graphe.append(f"{e} {relation} {voisin}"); nodes.add(voisin)
        for relation, voisin in graphe.voisins_amont(e):
            sous_graphe.append(f"{voisin} {relation} {e}"); nodes.add(voisin)
    return {"strategie": "vectorcypher",
            "documents": docs, "entrees": entrees,
            "sous_graphe": sous_graphe, "nodes": sorted(nodes),
            "n_docs": len(docs), "n_noeuds": len(nodes)}


# ===========================================================================
# 6) The complexity router (rules by default, LLM on request)
# ===========================================================================
# THE ROUTER WORD LISTS. Three sets of markers decide the strategy. They are
# matched against the text of the questions, so they must be in the corpus
# language and match the wording of the 25 questions in generate_corpus.py.
# Lab 26-5 measures the accuracy: the French baseline is 22/25.
#
# The order of the tests below matters as much as the lists: aggregation is
# checked first, then supplier, then relation. A question mentioning both a
# supplier and a chain goes to VectorCypher, which is the intent.
_RELATION_WORDS = ["depend", "depends", "feeds", "fed by", "linked", "replaces",
                   "impacts", "involved", "chain", "indirectly", "between ",
                   "end of the chain", "upstream", "isolated"]
_AGGREGATION_WORDS = ["all the", "which are", "what are the main", "main ",
                      "main themes", "critical points", "production lines",
                      "belongs to", "belong to"]
_SUPPLIER_WORDS = ["supplier", "suppliers", "contract"]


def routeur_complexite(question: str) -> str:
    """Returns 'vector-based' | 'local' | 'global' | 'vectorcypher'.

    Reproduces the chapter's logic: aggregation signals -> global;
 signaux fournisseur/amont -> vectorcypher ; signaux relationnels -> local ;
 sinon -> vector-based (the less cher)."""
    modele = _ollama_modele()
    if modele:
        rep = _routeur_llm(question, modele)
        if rep in {"vectoriel", "local", "global", "vectorcypher"}:
            return rep
    bas = question.lower()
    if any(m in bas for m in _AGGREGATION_WORDS):
        return "global"
    if any(m in bas for m in _SUPPLIER_WORDS):
        return "vectorcypher"
    if any(m in bas for m in _RELATION_WORDS):
        return "local"
    return "vectoriel"


def _routeur_llm(question: str, modele: str) -> str:
    import ollama
    prompt = (
        "Classify the question into EXACTLY one category among: "
        "vectoriel, local, global, vectorcypher.\n"
        "- vectoriel : fait simple, un seul document.\n"
        "- local: a direct relation between entities (dependencies).\n"
        "- global: aggregation, \"all the...\", themes.\n"
        "- vectorcypher: walking up a chain (supplier, upstream, multi-hop).\n"
        f"Question: {question}\nAnswer with a single word."
    )
    try:
        rep = ollama.generate(model=modele, prompt=prompt)["response"].strip().lower()
        for cat in ("vectorcypher", "global", "local", "vectoriel"):
            if cat in rep:
                return cat
    except Exception:
        pass
    return ""


# ===========================================================================
# 7) Accounting of the cost
# ===========================================================================
@dataclass
class Counter:
    recherches_vectorielles: int = 0
    noeuds_visites: int = 0
    documents_lus: int = 0

    def ajoute(self, *, docs: int = 0, nodes: int = 0, recherches: int = 0) -> None:
        self.documents_lus += docs
        self.noeuds_visites += nodes
        self.recherches_vectorielles += recherches

    def summary(self) -> str:
        return (f"recherches={self.recherches_vectorielles}  "
                f"docs_lus={self.documents_lus}  noeuds_visites={self.noeuds_visites}")
