# -*- coding: utf-8 -*-
"""
generate_corpus.py — generates the Chapter 33 corpus (case studies).

Written to corpus/:
  - cahiers.json       : the reference business specifications, with their
                         weights on quality, cost, latency and security, and
                         their hard constraints;
  - architectures.json : the reference architectures, one choice of block per
                         storey, with the justification of each choice.

The mechanism of this chapter is numeric — weights, profiles and caps in
archikit — so it survives translation untouched. The strings here are labels and
justifications, read by a human.

Two of the architectures are deliberate counter-examples: "Rich (everything on)"
and "E-commerce (over-secured)". They must score BADLY against the specifications
they do not fit; that is the whole point of Lab 33-2.

Run before the labs: python generate_corpus.py
"""

import json
from dataclasses import asdict
from pathlib import Path

from archikit import CAHIERS

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


# --- Reference architectures: one choice of block per storey ---
ARCHITECTURES = {
    "Minimal (low-cost)": {
        "choix": {
            "chunking": "fixe", "parsing": "texte_simple",
            "retrieval": "vectoriel", "reranking": "aucun",
            "generation": "petit_modele", "securite": "minimale",
            "ux": "basique"},
        "justification": {
            "global": "As cheap as possible. Suits a non-critical internal use, with "
                      "low stakes in security and accuracy."}},

    "Rich (everything on)": {
        "choix": {
            "chunking": "hierarchique", "parsing": "multimodal",
            "retrieval": "hybride_graphe", "reranking": "llm_juge",
            "generation": "grand_modele", "securite": "souverain",
            "ux": "streaming_split"},
        "justification": {
            "global": "Every block at maximum. Maximum quality and security, but "
                      "high cost and latency — often oversized for the real "
                      "need."}},

    "Banking (compliance)": {
        "choix": {
            "chunking": "hierarchique", "parsing": "texte_simple",
            "retrieval": "hybride_graphe", "reranking": "cross_encoder",
            "generation": "grand_modele", "securite": "souverain",
            "ux": "citations_confiance"},
        "justification": {
            "retrieval": "interdependent regulatory documents -> a graph.",
            "securite": "confidentiality and sovereignty are required.",
            "ux": "a low tolerance for error -> citations plus trust states."}},

    "Aerospace (maintenance)": {
        "choix": {
            "chunking": "hierarchique", "parsing": "multimodal",
            "retrieval": "hybride", "reranking": "cross_encoder",
            "generation": "modele_specialise", "securite": "abac_audit",
            "ux": "citations_confiance"},
        "justification": {
            "parsing": "scanned plans and diagrams -> multimodal parsing and OCR.",
            "generation": "technical vocabulary -> a specialised model.",
            "ux": "workshop use -> citations plus trust; latency tolerated."}},

    "E-commerce (support)": {
        "choix": {
            "chunking": "semantique", "parsing": "texte_simple",
            "retrieval": "hybride", "reranking": "aucun",
            "generation": "petit_modele", "securite": "minimale",
            "ux": "streaming_split"},
        "justification": {
            "generation": "high frequency -> a small model, low cost per query.",
            "reranking": "latency is king -> the reranking is dropped.",
            "ux": "streaming for perceived latency; an error is cheap."}},

    "E-commerce (over-secured)": {
        "choix": {
            "chunking": "semantique", "parsing": "texte_simple",
            "retrieval": "hybride", "reranking": "llm_juge",
            "generation": "grand_modele", "securite": "souverain",
            "ux": "streaming_split"},
        "justification": {
            "global": "A counter-example: sovereign security and LLM reranking are "
                      "useless for consumer support -> cost and latency sink."}},
}


def main():
    cahiers_export = {cle: asdict(c) for cle, c in CAHIERS.items()}
    (CORPUS / "cahiers.json").write_text(
        json.dumps(cahiers_export, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (CORPUS / "architectures.json").write_text(
        json.dumps(ARCHITECTURES, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"Corpus written to {CORPUS}/:")
    print(f"  cahiers.json       : {len(cahiers_export)} specifications")
    print(f"  architectures.json : {len(ARCHITECTURES)} reference architectures")


if __name__ == "__main__":
    main()
