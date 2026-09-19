# -*- coding: utf-8 -*-
"""
businesskit.py — the shared module of the Chapter 28 labs.

The chapter's thesis — *a semantic layer (taxonomy, ontology, business graph)
acts as a guardrail on retrieval and on extraction* — stays entirely visible
offline.

What this module supplies:

  - Taxonomy : concepts, synonyms, expansion -> the retrieval guardrail
  - Ontology : classes, permitted relations, axioms -> validation
  - a business graph built on the fly from the documents
  - a comparison of blind against guided extraction
  - banner and Counter: run-time comfort and accounting

Everything runs with no API key: Ollama is used if OLLAMA_MODEL is set, otherwise
a deterministic fallback.

A WARNING ON THE SYNONYM LISTS. They live in the corpus (failure_taxonomy.json)
rather than here, but the expansion below matches them literally against the text
of the reports. They must be in the corpus language and match the wording of the
reports. Lab 28-1 measures the effect as a recall with and without expansion; a
list that stops matching shows up there as a gain of zero, never as an error.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

CORPUS = Path(__file__).resolve().parent / "corpus"


# ===========================================================================
# 0) Outils optionnels (detection silencieuse)
# ===========================================================================
def _a_sentence_transformers() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def _ollama_modele() -> str | None:
    """Return the name of the Ollama model if configured AND available, else None.

 On active the LLM local in posant the variable of environnement OLLAMA_MODEL,
 for example : OLLAMA_MODEL=mistral python lab28-1_taxonomic_guardrail.py
 """
    modele = os.environ.get("OLLAMA_MODEL")
    if not modele:
        return None
    try:
        import ollama  # noqa: F401
        return modele
    except Exception:
        return None


def llm(prompt: str, *, json_attendu: bool = False) -> str:
    """Point of input unique toward a LLM local (Ollama, ex. Mistral).

    Returns an empty string if no LLM is available: the labs then fall back
    then on their deterministic fallback. No API key is ever used.
 """
    modele = _ollama_modele()
    if not modele:
        return ""
    try:
        import ollama
        options = {"temperature": 0.0}
        if json_attendu:
            prompt = prompt + "\n\nAnswer with valid JSON ONLY, no commentary."
        rep = ollama.generate(model=modele, prompt=prompt, options=options)
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
# 1) Normalisation of texte
# ===========================================================================
def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texte)


def _tokens(texte: str) -> list[str]:
    return [t for t in normaliser(texte).split() if len(t) > 1]


# ===========================================================================
# 2) Vector index (TF-IDF by default, dense embeddings when available)
# ===========================================================================
class Embedder:
    """Deterministic TF-IDF by default; sentence-transformers if installed."""

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
            normes = np.linalg.norm(self.matrice, axis=1, keepdims=True)
            self.matrice = self.matrice / np.clip(normes, 1e-9, None)
            self._dense = False

    def encoder(self, texte: str) -> np.ndarray:
        if self._dense:
            return self._modele.encode([texte], normalize_embeddings=True)[0]
        v = self._vect.transform([texte]).toarray()[0]
        return v / max(np.linalg.norm(v), 1e-9)


class Search:
    """Index vector-based minimal : top-k by cosine similarity."""

    def __init__(self, fragments: list[dict]):
        self.fragments = fragments
        self.emb = Embedder([f["text"] for f in fragments])

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
# 3) Taxonomy : tree is-a + synonymes -> expansion of query
# ===========================================================================
class Taxonomy:
    """Tree of classification (relation is-a) with synonymes business.

 The JSON attendu : a dict { concept: {type, sous_classes?, synonymes?} }.
 On reconstruit parents/enfants and a index synonyme -> concept canonique.
 """

    def __init__(self, donnees: dict):
        self.nodes = donnees
        self.parent: dict[str, str] = {}
        self.enfants: dict[str, list[str]] = defaultdict(list)
        for concept, meta in donnees.items():
            for fils in meta.get("subclasses", []):
                self.parent[fils] = concept
                self.enfants[concept].append(fils)
        # The index: any normalised term (a concept or a synonym) -> the canonical concept
        self.index: dict[str, str] = {}
        for concept, meta in donnees.items():
            self.index[normaliser(concept)] = concept
            for syn in meta.get("synonyms", []):
                self.index[normaliser(syn)] = concept

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Taxonomy":
        path = Path(path) if path else CORPUS / "failure_taxonomy.json"
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def concept_de(self, terme: str) -> str | None:
        """Resolve a term (canonical or synonym) onto its canonical concept."""
        return self.index.get(normaliser(terme))

    def voisinage(self, concept: str) -> dict[str, list[str]]:
        """The parent, siblings and direct children of a concept."""
        parent = self.parent.get(concept)
        freres = [c for c in self.enfants.get(parent, []) if c != concept] if parent else []
        return {
            "concept": [concept],
            "parents": [parent] if parent else [],
            "freres": freres,
            "enfants": list(self.enfants.get(concept, [])),
        }

    def expansion(self, concept: str) -> list[str]:
        """Every term useful for widening a query: the concept, its
    parents, siblings and children, AND all their synonyms."""
        vois = self.voisinage(concept)
        concepts = vois["concept"] + vois["parents"] + vois["freres"] + vois["enfants"]
        termes: list[str] = []
        for c in concepts:
            termes.append(c)
            termes.extend(self.nodes.get(c, {}).get("synonyms", []))
        # Deduplicate while preserving the order
        vus, out = set(), []
        for t in termes:
            cle = normaliser(t)
            if cle not in vus:
                vus.add(cle)
                out.append(t)
        return out


def mapper_concept(requete: str, taxo: Taxonomy) -> str | None:
    """Mappe a query user on the concept canonique of the taxonomy.

    Two levels of realism:
 - repli (by default) : appariement lexical on the index synonymes -> concept ;
      - real use (Ollama): the LLM is asked to choose among the concepts
 official terms, which captures indirect wording.
 """
    # 1) Try the LLM, if OLLAMA_MODEL is set
    concepts = list(taxo.nodes.keys())
    rep = llm(
        "Here is the list of concepts of an industrial failure taxonomy:\n"
        + ", ".join(concepts)
        + f"\n\nWhich concept is closest to the query: \"{requete}\"?\n"
        "Answer with a single concept EXACTLY as written in the list, or NONE."
    )
    rep = rep.strip().strip('"').strip()
    if rep and rep != "NONE" and rep in taxo.nodes:
        return rep

    # 2) repli lexical : we look for a terme connu (concept or synonyme) in the query
    rq = normaliser(requete)
    # priority to the correspondances the more longues (the more specifics)
    for terme in sorted(taxo.index, key=len, reverse=True):
        if terme and terme in rq:
            return taxo.index[terme]
    return None


# ===========================================================================
# 4) The ontology: a meta-model (classes, permitted relations, axioms)
# ===========================================================================
@dataclass
class Ontology:
    classes: list[str]
    relations: list[dict]            # {source, target, label}
    axiomes: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path | str | None = None) -> "Ontology":
        path = Path(path) if path else CORPUS / "maintenance_ontology.json"
        d = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(d["classes"], d["relations"], d.get("axioms", []))

    # --- schema : quelles relations (source -> label -> target) are permises ?
    def relations_autorisees(self) -> set[tuple[str, str, str]]:
        return {(r["source"], r["label"], r["target"]) for r in self.relations}

    def relation_permise(self, source: str, label: str, target: str) -> bool:
        return (source, label, target) in self.relations_autorisees()

    # --- validations structurelles -----------------------------------------
    def validate(self) -> list[str]:
        """Return the list of problems detected; empty means the ontology is sound."""
        pbs: list[str] = []
        classes = set(self.classes)
        # 1) Every relation must reference declared classes
        for r in self.relations:
            for bout in ("source", "target"):
                if r[bout] not in classes:
                    pbs.append(f"Relation '{r['label']}' references an unknown class: {r[bout]}")
        # 2) not of cycle in the graph classes (hors auto-relation explicite)
        adj: dict[str, list[str]] = defaultdict(list)
        for r in self.relations:
            if r["source"] != r["target"]:
                adj[r["source"]].append(r["target"])
        if self._a_cycle(adj):
            pbs.append("A cycle was detected in the class graph (A -> ... -> A).")
        # 3) toute classe participe to at the less a relation
        impliquees = {r["source"] for r in self.relations} | {r["target"] for r in self.relations}
        for c in self.classes:
            if c not in impliquees:
                pbs.append(f"Isolated class (no relation): {c}")
        return pbs

    @staticmethod
    def _a_cycle(adj: dict[str, list[str]]) -> bool:
        couleur: dict[str, int] = {}  # 0 blanc, 1 gris, 2 noir

        def visite(n: str) -> bool:
            couleur[n] = 1
            for m in adj.get(n, []):
                if couleur.get(m, 0) == 1:
                    return True
                if couleur.get(m, 0) == 0 and visite(m):
                    return True
            couleur[n] = 2
            return False

        return any(visite(n) for n in list(adj) if couleur.get(n, 0) == 0)


# ===========================================================================
# 5) Extraction of triples (libre vs contrainte by schema)
# ===========================================================================

# Volontairement simples : the but educational is of TO COMPARE libre vs contraint,
# This is not intended to rival an LLM extractor. The LLM (Ollama) takes over when available.

# THE EXTRACTION TEMPLATES. Each is (a regex over NORMALISED text, source class,
# label, target class). The classes and labels MUST match those declared in the
# ontology of generate_corpus.py, and the regexes must match the wording of the
# reports. Break either link and the constrained extraction silently returns
# nothing: Lab 28-3 would report zero triples rather than raise.
#
# Deliberately simple: the teaching aim is to COMPARE free against constrained
# extraction, not to rival an LLM extractor. Ollama takes over when available.
# The text passes through normalise() — lower-cased, accents stripped — BEFORE
# matching.
_PMP = r"pump(?: [a-z])?(?:[- ]\d+)?"
_CIR = r"(?:\w+ )?circuit"
_TEMPLATES = [
    (rf"(?P<s>{_PMP})\s+is\s+fed\s+by\s+(?:the )?(?P<t>{_CIR})",
     "Pump", "fed_by", "HydraulicCircuit"),
    (rf"(?P<s>{_PMP})\s+carries\s+(?:the )?risk\s+of\s+(?P<t>cavitation|leak|failure\w*)",
     "Pump", "carries_risk_of", "FailureMode"),
    (rf"(?P<s>\w*\s?procedure)\s+concerns\s+(?:the )?(?P<t>{_PMP})",
     "Procedure", "concerns", "Pump"),
    (r"(?P<s>technician \w+)\s+is\s+responsible\s+for\s+(?:the )?(?P<t>\w*\s?procedure)",
     "Technician", "responsible_for", "Procedure"),
    # A trap: a plausible relation that the ontology does NOT permit.
    (rf"(?P<s>{_CIR})\s+feeds\s+(?:the )?(?P<t>technician\w*)",
     "HydraulicCircuit", "feeds", "Technician"),
]


def extract_triples(texte: str, ontologie: Ontology | None = None) -> list[dict]:
    """Extract triples (subject, relation, object).

    If `ontology` is supplied the extraction is CONSTRAINED: only triples whose
    type (source class, label, target class) is permitted by the schema are
    kept. This is "ontology-driven GraphRAG".
    """
    bruts: list[dict] = []

    # 1) LLM path (when Ollama is available): provide the schema as a safeguard
    if ontologie is not None:
        schema = "\n".join(f"- {r['source']} {r['label']} {r['target']}"
                           for r in ontologie.relations)
        rep = llm(
            "Extract the relations of the text as JSON triples "
            '[{"sujet":..., "relation":..., "objet":..., '
            '"classe_sujet":..., "classe_objet":...}].\n'
            f"Use ONLY these permitted relations:\n{schema}\n\nText:\n{texte}",
            json_attendu=True,
        )
        triplets_llm = _parse_json_liste(rep)
        if triplets_llm:
            for t in triplets_llm:
                t["source_contrainte"] = "llm"
            bruts = triplets_llm

    # 2) Deterministic template fallback (always used if the LLM produces nothing)
    if not bruts:
        bas = normaliser(texte)
        for motif, cs, label, ct in _TEMPLATES:
            for m in re.finditer(motif, bas):
                bruts.append({
                    "sujet": m.group("s").strip(),
                    "relation": label,
                    "objet": m.group("t").strip(),
                    "classe_sujet": cs,
                    "classe_objet": ct,
                    "source_contrainte": "gabarit",
                })

    # Deduplicate: two templates can catch the same relation
    vus, uniques = set(), []
    for t in bruts:
        cle = (normaliser(t["sujet"]), t["relation"], normaliser(t["objet"]))
        if cle not in vus:
            vus.add(cle)
            uniques.append(t)
    bruts = uniques

    # 3) With an ontology: filter through the schema
    if ontologie is None:
        return bruts
    gardes = []
    for t in bruts:
        cs = t.get("classe_sujet", "?")
        ct = t.get("classe_objet", "?")
        if ontologie.relation_permise(cs, t["relation"], ct):
            t["valide"] = True
            gardes.append(t)
        else:
            t["valide"] = False
    return bruts if ontologie is None else [t for t in bruts if t.get("valide")] or \
        [dict(t, rejete=True) for t in bruts]


def _parse_json_liste(rep: str) -> list[dict]:
    if not rep:
        return []
    rep = re.sub(r"^```(?:json)?|```$", "", rep.strip(), flags=re.MULTILINE).strip()
    try:
        obj = json.loads(rep)
        return obj if isinstance(obj, list) else []
    except Exception:
        return []


# ===========================================================================
# 6) Graph business : instanciation interrogeable of a ontology
# ===========================================================================
class BusinessGraph:
    """Instances linked by typed edges. Validated against the ontology."""

    def __init__(self, ontologie: Ontology | None = None):
        self.ontologie = ontologie
        self.nodes: dict[str, str] = {}          # instance -> classe
        self.aretes: list[tuple[str, str, str]] = []  # (sujet, label, objet)

    def add_instance(self, nom: str, classe: str) -> None:
        self.nodes[nom] = classe

    def add_edge(self, sujet: str, label: str, objet: str) -> bool:
        if self.ontologie is not None:
            cs = self.nodes.get(sujet, "?")
            ct = self.nodes.get(objet, "?")
            if not self.ontologie.relation_permise(cs, label, ct):
                return False
        self.aretes.append((sujet, label, objet))
        return True

    def voisins(self, instance: str, label: str | None = None) -> list[str]:
        return [o for (s, l, o) in self.aretes
                if s == instance and (label is None or l == label)]

    def __len__(self) -> int:
        return len(self.aretes)


def build_ras(fragments: list[dict], requete: str,
                   ontologie: Ontology | None = None, k: int = 3) -> BusinessGraph:
    """Retrieval-And-Structuring : on retrieves the k fragments the closest
 of the query, then we build a mini-graph ON THE FLY by extraction
    constrained to those fragments alone: no prior global indexing."""
    rech = Search(fragments)
    relevant = rech.chercher(requete, k=k)
    g = BusinessGraph(ontologie)
    for f in relevant:
        for t in extract_triples(f["text"], ontologie):
            if t.get("rejete"):
                continue
            g.add_instance(t["sujet"], t.get("classe_sujet", "?"))
            g.add_instance(t["objet"], t.get("classe_objet", "?"))
            g.aretes.append((t["sujet"], t["relation"], t["objet"]))
    return g


# ===========================================================================
# 7) Confort : accounting simple
# ===========================================================================
@dataclass
class Counter:
    appels_llm: int = 0
    fragments_lus: int = 0

    def rapport(self) -> str:
        return (f"appels LLM : {self.appels_llm} | "
                f"fragments lus : {self.fragments_lus}")


def recall(recuperes: list[str], relevant: list[str]) -> float:
    """Recall = |retrieved and relevant| / |relevant|."""
    if not relevant:
        return 0.0
    inter = set(recuperes) & set(relevant)
    return len(inter) / len(relevant)


# ===========================================================================
# 8) Access corpus
# ===========================================================================
def check_axioms(graphe: "BusinessGraph") -> list[dict]:
    """Check a few ABSOLUTE business rules over an instantiated graph.

    These rules encode the axioms of the maintenance ontology:
    A1. Every FailureMode must be linked to at least one Pump.
    A2. An intervention Procedure must be preceded by a safety Procedure
        (the lock-off).
    A3. Every Pump must be fed_by exactly one HydraulicCircuit.

 Return the list of violations (empty means the graph is compliant).
 """
    violations: list[dict] = []
    instances_par_classe: dict[str, list[str]] = defaultdict(list)
    for nom, classe in graphe.nodes.items():
        instances_par_classe[classe].append(nom)

    # A1: is each failure mode present linked to a pump?
    cibles_risque = {o for (s, l, o) in graphe.aretes if l == "carries_risk_of"}
    for mode in instances_par_classe.get("FailureMode", []):
        if mode not in cibles_risque:
            violations.append({"axiome": "A1", "instance": mode,
                               "message": f"FailureMode '{mode}' is linked to no Pump."})

    # A3: is each pump fed by exactly one circuit?
    for pompe in instances_par_classe.get("Pump", []):
        circuits = graphe.voisins(pompe, "fed_by")
        if len(circuits) == 0:
            violations.append({"axiome": "A3", "instance": pompe,
                               "message": f"Pump '{pompe}' is fed by no circuit."})
        elif len(circuits) > 1:
            violations.append({"axiome": "A3", "instance": pompe,
                               "message": f"Pump '{pompe}' is fed by {len(circuits)} circuits (>1)."})
    return violations


def load_fragments(nom: str = "maintenance_reports.json") -> list[dict]:
    return json.loads((CORPUS / nom).read_text(encoding="utf-8"))
