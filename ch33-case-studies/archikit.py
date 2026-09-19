# -*- coding: utf-8 -*-
"""
archikit.py — the shared module of the Chapter 33 labs
(case studies by domain: design matrices and architecture patterns).

The module supplies a "conceptual test bench": a catalogue of building blocks
with their cost, quality and latency profiles; an evaluator that scores an
architecture against a specification; and the tools to make an architecture
evolve as the business need changes. Everything is deterministic and
reproducible, with no API key.

The chapter's thesis: *the right architecture is not the richest, it is the one
that solves the specification at the best trade-off.* You start from the need and
work back to the blocks.

What this module supplies:

  - BRIQUES           : the catalogue of blocks, one storey at a time
  - CAHIERS           : three reference business specifications
  - Architecture      : one choice of block per storey
  - evaluate          : the weighted score against a specification, with caps
  - grille_soutenance : the criteria and marking scheme for a design review

The mechanism here is NUMERIC — weights, profiles, caps — so it survives
translation untouched. The strings are display labels.

The running threads: Julien (maintenance), Claire (HR), Sophie (public sector and
regulation), plus the guests of the chapter.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"


def bandeau(titre: str) -> None:
    print("=" * 74)
    print(titre)
    print("  A conceptual test bench — deterministic, no API key")
    print("=" * 74)


# ===========================================================================
# 1) Catalogue of briques by stage of the pipeline
# Profiles scored on [0..1]: quality (the contribution to relevance),
# cost (consumption of resources and money), latency (the time added).
# cout and latency : MORE it IS HAUT, MORE it IS CHER / LENT.
# ===========================================================================
@dataclass
class Profile:
    qualite: float
    cout: float
    latence: float
    securite: float = 0.0   # the security contribution (0 if neutral)
    note: str = ""


# Each storey offers several competing blocks. The `note` strings are display
# labels; the numbers are the mechanism and survive translation untouched.
BRIQUES: dict[str, dict[str, Profile]] = {
    "chunking": {
        "fixe": Profile(0.45, 0.10, 0.10, note="fixed-size splitting"),
        "semantique": Profile(0.70, 0.30, 0.25, note="semantic splitting"),
        "hierarchique": Profile(0.82, 0.45, 0.35, note="parent/child, multi-level"),
    },
    "parsing": {
        "texte_simple": Profile(0.40, 0.10, 0.10, note="raw text extraction"),
        "layout_ocr": Profile(0.78, 0.55, 0.55, note="layout plus OCR (scans)"),
        "multimodal": Profile(0.88, 0.75, 0.70, note="vision, tables and diagrams"),
    },
    "retrieval": {
        "vectoriel": Profile(0.60, 0.30, 0.25, note="dense only"),
        "hybride": Profile(0.80, 0.45, 0.40, note="BM25 plus vectors"),
        "hybride_graphe": Profile(0.90, 0.70, 0.60,
                                 note="hybrid plus graph (interdependencies)"),
    },
    "reranking": {
        "aucun": Profile(0.00, 0.00, 0.00, note="no reranking"),
        "cross_encoder": Profile(0.65, 0.40, 0.45, note="a cross-encoder reranker"),
        "llm_juge": Profile(0.75, 0.65, 0.70, note="reranking by an LLM"),
    },
    "generation": {
        "petit_modele": Profile(0.50, 0.20, 0.20, note="a light or local LLM"),
        "grand_modele": Profile(0.85, 0.70, 0.55, note="a strong general LLM"),
        "modele_specialise": Profile(0.80, 0.50, 0.40,
                                    note="a domain fine-tuned LLM"),
    },
    "securite": {
        "minimale": Profile(0.00, 0.05, 0.05, securite=0.30,
                           note="basic input filtering"),
        "abac_audit": Profile(0.00, 0.25, 0.20, securite=0.80,
                             note="ABAC plus audit (ch31)"),
        "souverain": Profile(0.00, 0.45, 0.30, securite=0.95,
                            note="ABAC, audit and sovereign hosting"),
    },
    "ux": {
        "basique": Profile(0.20, 0.05, 0.05, note="an answer plus a list of sources"),
        "citations_confiance": Profile(0.55, 0.20, 0.15,
                                      note="citations plus trust states (ch32)"),
        "streaming_split": Profile(0.65, 0.30, 0.10,
                                  note="plus streaming and split-screen"),
    },
}


# ===========================================================================
# 2) The reference business specifications
# Weights on the axes (summing to 1), plus hard constraints (caps).
# ===========================================================================
@dataclass
class Spec:
    nom: str
    domaine: str
    poids: dict          # {quality, cost, latency, security}, summing to about 1
    latence_max: float   # the latency cap tolerated [0..1] (0 = instant, 1 = slow)
    securite_min: float  # the minimum security requirement [0..1]
    multimodal: bool     # scanned documents, images, tables?
    interdependances: bool  # does the meaning depend on links between documents?
    note: str = ""


CAHIERS = {
    "banque": Spec(
        nom="Banking compliance assistant", domaine="banking/legal",
        poids={"qualite": 0.40, "cout": 0.15, "latence": 0.10, "securite": 0.35},
        latence_max=0.7, securite_min=0.80, multimodal=False,
        interdependances=True,
        note="a very low tolerance for error; strongly interdependent "
             "regulatory documents; high confidentiality."),
    "aeronautique": Spec(
        nom="Aerospace industrial documentation base",
        domaine="industry/maintenance",
        poids={"qualite": 0.45, "cout": 0.20, "latence": 0.15, "securite": 0.20},
        latence_max=0.8, securite_min=0.55, multimodal=True,
        interdependances=False,
        note="scanned diagrams and plans (1985 onwards); technical precision is "
             "critical; latency tolerated because it is workshop use."),
    "ecommerce": Spec(
        nom="E-commerce customer support", domaine="e-commerce/support",
        poids={"qualite": 0.30, "cout": 0.25, "latence": 0.35, "securite": 0.10},
        latence_max=0.30, securite_min=0.30, multimodal=False,
        interdependances=False,
        note="very high frequency; freshness and latency are king; cost per "
             "query is decisive; an error is cheap."),
}


# ===========================================================================
# 3) An architecture is one choice of block per storey
# ===========================================================================
ETAGES = list(BRIQUES.keys())


@dataclass
class Architecture:
    nom: str
    choix: dict             # {etage: nom_brique}
    justification: dict = field(default_factory=dict)

    def profils(self) -> dict:
        return {e: BRIQUES[e][self.choix[e]] for e in self.choix}

    def validate(self) -> None:
        for e in ETAGES:
            if e not in self.choix:
                raise ValueError(f"missing storey: {e}")
            if self.choix[e] not in BRIQUES[e]:
                raise ValueError(f"unknown component for {e}: {self.choix[e]}")


def _agg(archi: Architecture) -> dict:
    """Aggregate the block profiles into an overall architecture profile."""
    profs = archi.profils()
    # Quality: an implicit weighted mean over chunking, parsing, retrieval,
    # reranking, generation and UX.
    q_etages = ["parsing", "chunking", "retrieval", "reranking", "generation", "ux"]
    qualite = sum(profs[e].qualite for e in q_etages) / len(q_etages)
    cout = sum(p.cout for p in profs.values())
    latence = sum(p.latence for p in profs.values())
    securite = max(profs["securite"].securite,
                   profs.get("ux", Profile(0, 0, 0)).securite)
    # normalisation douce of the cumul cost/latency on [0..1]
    cout = min(1.0, cout / len(profs))
    latence = min(1.0, latence / len(profs))
    return {"qualite": round(qualite, 3), "cout": round(cout, 3),
            "latence": round(latence, 3), "securite": round(securite, 3)}


# ===========================================================================
# 4) Evaluation of a architecture contre a specification
# ===========================================================================
def evaluate(archi: Architecture, cahier: Spec) -> dict:
    """Note a architecture (0..100) contre a specification, and signale
 the violations of contraintes dures (latency_max, securite_min, multimodal,
 interDependencies)."""
    archi.validate()
    prof = _agg(archi)
    poids = cahier.poids

    # The weighted score: quality and security pull UP, cost and latency pull
    # DOWN, so low cost and low latency are rewarded.
    score = (poids["qualite"] * prof["qualite"]
             + poids["securite"] * prof["securite"]
             + poids["cout"] * (1.0 - prof["cout"])
             + poids["latence"] * (1.0 - prof["latence"]))
    score = round(100 * score, 1)

    violations = []
    if prof["latence"] > cahier.latence_max:
        violations.append(
            f"latence {prof['latence']:.2f} > plafond {cahier.latence_max:.2f}")
    if prof["securite"] < cahier.securite_min:
        violations.append(
            f"security {prof['securite']:.2f} < minimum {cahier.securite_min:.2f}")
    if cahier.multimodal and archi.choix["parsing"] == "texte_simple":
        violations.append("plain-text parsing although the corpus is multimodal")
    if cahier.interdependances and archi.choix["retrieval"] != "hybride_graphe":
        violations.append(
            "strong interdependencies but a retrieval with no graph")

    # A score penalty for each hard constraint violated.
    score_final = round(max(0.0, score - 12 * len(violations)), 1)
    return {"score_brut": score, "score_final": score_final,
            "profil": prof, "violations": violations,
            "conforme": len(violations) == 0}


# ===========================================================================
# 5) Comparaison of deux architectures
# ===========================================================================
def compare(a: Architecture, b: Architecture, cahier: Spec) -> dict:
    ea, eb = evaluate(a, cahier), evaluate(b, cahier)
    gagnant = a.nom if ea["score_final"] >= eb["score_final"] else b.nom
    return {"a": {"nom": a.nom, **ea}, "b": {"nom": b.nom, **eb},
            "gagnant": gagnant,
            "ecart": round(abs(ea["score_final"] - eb["score_final"]), 1)}


# ===========================================================================
# 6) Analyse of impact of a changement business
# ===========================================================================
def analyze_impact(archi: Architecture, cahier_avant: Spec,
                    cahier_apres: Spec,
                    modifs: dict | None = None) -> dict:
    """Measures the effet of a changement business (new specification) on
 an architecture, before and after applying the `modifs` changes
 ({etage: new_brique})."""
    av = evaluate(archi, cahier_apres)  # the architecture unchanged, a new context
    base_avant = evaluate(archi, cahier_avant)
    archi_modifiee = Architecture(
        nom=archi.nom + " (adapted)",
        choix={**archi.choix, **(modifs or {})},
        justification=archi.justification)
    ap = evaluate(archi_modifiee, cahier_apres)
    return {
        "score_origine_contexte_origine": base_avant["score_final"],
        "score_origine_contexte_nouveau": av["score_final"],
        "score_adapte_contexte_nouveau": ap["score_final"],
        "regression_sans_adaptation": round(
            base_avant["score_final"] - av["score_final"], 1),
        "gain_adaptation": round(ap["score_final"] - av["score_final"], 1),
        "violations_avant_adaptation": av["violations"],
        "violations_apres_adaptation": ap["violations"],
        "modifs": modifs or {}}


# ===========================================================================
# 7) Grille of soutenance (Lab 33-4)
# ===========================================================================
def grille_soutenance() -> list[dict]:
    """The marking scheme for an architecture design review, summing to 100."""
    return [
        {"critere": "Fit to the specification", "points": 25,
         "question": "Does the architecture solve the real business need?"},
        {"critere": "Justification of the choices (cost/quality/latency)", "points": 20,
         "question": "Is each block justified by an explicit trade-off?"},
        {"critere": "Security and governance", "points": 15,
         "question": "Are ABAC, audit and the tiers of autonomy handled (ch31)?"},
        {"critere": "User experience", "points": 15,
         "question": "Are citations, uncertainty and perceived latency thought through (ch32)?"},
        {"critere": "Evaluation strategy", "points": 15,
         "question": "Does the validation protocol measure the failures (ch29)?"},
        {"critere": "Clarity and oral defence", "points": 10,
         "question": "Is the review clear, and honest about its limits?"},
    ]


# ===========================================================================
# 8) Chargement of the corpus (cahiers + architectures of reference)
# ===========================================================================
def load_specs() -> dict:
    data = json.loads((CORPUS / "cahiers.json").read_text(encoding="utf-8"))
    return data


def load_architectures() -> dict:
    data = json.loads((CORPUS / "architectures.json").read_text(encoding="utf-8"))
    return {nom: Architecture(nom=nom, choix=d["choix"],
                              justification=d.get("justification", {}))
            for nom, d in data.items()}
