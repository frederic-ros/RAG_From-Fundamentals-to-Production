# -*- coding: utf-8 -*-
"""
interface.py — Streamlit interface for semi-supervised chunking (Lab 17-6).

Shows the cut proposed by the system and lets the expert VALIDATE, MERGE or
SPLIT each chunk in a few clicks. Every action is recorded in corrections.csv:
the first harvest of expert judgements for the calibration.

    streamlit run interface.py

(If streamlit is not installed: pip install streamlit. The console version,
lab17-6_semi_supervised.py, runs everywhere without it.)
"""

from __future__ import annotations

import csv
from pathlib import Path

try:
    import streamlit as st
except ImportError:  # pragma: no cover
    print("streamlit is not installed. Run: pip install streamlit")
    print("Ou lancez la version console : python lab17-6_semi_supervised.py")
    raise SystemExit(0)

import corpus

OUTPUT_CSV = Path(__file__).resolve().parent / "corrections.csv"


def initial_proposal(texte: str):
    import re
    phrases = [p.strip() for p in re.split(r"(?<=[.!?])\s+", texte.strip()) if p.strip()]
    chunks, tampon = [], []
    for ph in phrases:
        if ph.lower().startswith("exception") or re.match(r"Article\s+\d+", ph):
            if tampon:
                chunks.append(" ".join(tampon)); tampon = []
        tampon.append(ph)
    if tampon:
        chunks.append(" ".join(tampon))
    return chunks


def enregistrer(corrections):
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["original_chunk", "action", "justification"])
        w.writeheader()
        for c in corrections:
            w.writerow(c)


def main():
    st.set_page_config(page_title="Semi-supervised chunking", layout="wide")
    st.title("Semi-supervised chunking — the expert validates, the system learns")
    st.caption("Lab 17-6 · Chapter 17 — Advanced chunking")

    if not corpus.corpus_ready():
        st.error("Corpus not found. Run this first : python generate_corpus.py")
        return

    texte = corpus.load("hr_agreement.txt")

    if "chunks" not in st.session_state:
        st.session_state.chunks = initial_proposal(texte)
        st.session_state.corrections = []

    st.subheader("Document : accord d'entreprise (RH)")
    st.info("A business tip: a rule and its exception are often inseparable. "
            "Merge them if the system has split them.")

    chunks = st.session_state.chunks
    a_supprimer = None
    a_mergener = None

    for i, chunk in enumerate(chunks):
        with st.container(border=True):
            st.markdown(f"**Chunk {i + 1}**")
            st.write(chunk)
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Valider", key=f"val{i}"):
                st.session_state.corrections.append({
                    "original_chunk": chunk[:50], "action": "validate",
                    "justification": "fragment coherent"})
                st.toast(f"Chunk {i+1} validated")
            if i > 0 and c2.button("⬆️ Merge with the previous one", key=f"merge{i}"):
                a_mergener = i
            if c3.button("✂️ Split by sentence", key=f"sci{i}"):
                a_supprimer = i

    if a_mergener is not None:
        i = a_mergener
        mergene = chunks[i - 1] + " " + chunks[i]
        st.session_state.corrections.append({
            "original_chunk": chunks[i][:50], "action": "merge",
            "justification": "regle et exception inseparables"})
        chunks[i - 1] = mergene
        chunks.pop(i)
        st.rerun()

    if a_supprimer is not None:
        i = a_supprimer
        import re
        phrases = [p.strip() for p in re.split(r"(?<=[.!?])\s+", chunks[i]) if p.strip()]
        if len(phrases) > 1:
            st.session_state.corrections.append({
                "original_chunk": chunks[i][:50], "action": "scinder",
                "justification": "deux sujets distincts"})
            chunks[i:i + 1] = phrases
            st.rerun()

    st.divider()
    if st.button("💾 Save corrections for calibration"):
        enregistrer(st.session_state.corrections)
        st.success(f"{len(st.session_state.corrections)} decisions written to "
                   f"{OUTPUT_CSV.name} — the first material of domain calibration.")
        st.dataframe(st.session_state.corrections)


if __name__ == "__main__":
    main()
