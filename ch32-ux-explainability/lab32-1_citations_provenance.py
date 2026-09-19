# -*- coding: utf-8 -*-
"""
Lab 32-1 — Citations and provenance: making an answer verifiable
"A correct answer that cannot be checked is not a usable answer"

Each block of an answer is attributed to its source fragment, with a fidelity
score — the "compass" that tells the reader how solidly the block is anchored.
Blocks below the threshold are marked "unsourced" rather than quietly attributed
to whatever came closest.

Also shown: a stable anchor address (document, page, fragment id) that survives
reindexing, and a standalone HTML demo with popover citations.

THE DOCUMENTS AND THE ANSWER BLOCKS ARE PAIRED by lexical overlap. If the two
drift apart, the fidelity collapses and this lab reports it as a quality problem.
The French baseline for the mean fidelity is 34%; the English corpus reaches 51%,
because the blocks and the documents match more closely word for word.

No API key. Run generate_corpus.py first.
"""

from pathlib import Path

from uxkit import (bandeau, ancrer_citations, provenance_narrative,
                  ancre_persistante, html_citations, load_fragments,
                  load_answers)


def main():
    bandeau("Lab 32-1 — Citations interactives et provenance narrative")
    frags = load_fragments()
    reponses = load_answers()

    # On illustre on an answer to trust high (multi-sources).
    rep = next(r for r in reponses if r["id"] == "R01")
    ancres = ancrer_citations(rep["blocs"], frags)

    # ---- 1) Ancrage bloc -> fragment + boussole of fidelity ----
    print(f"\nQuestion: \"{rep['question']}\"")
    print("\n[1] INLINE CITATIONS (anchoring plus the fidelity compass)")
    print("─" * 74)
    for i, a in enumerate(ancres, 1):
        if a["source"]:
            print(f"  [{i}] {a['bloc'][:46]:<46}")
            print(f"      -> {a['frag_id']} \"{a['frag_titre']}\" "
                  f"(fidelity {a['fidelite']:.0%})")
        else:
            print(f"  [{i}] {a['bloc'][:46]:<46}  -> UNSOURCED")

    # ---- 2) Provenance narrative ----
    print("\n[2] NARRATIVE PROVENANCE (documentary basis, before reading)")
    print("─" * 74)
    prov = provenance_narrative(ancres)
    print(f"  {prov}")

    # ---- 3) Ancres persistantes ----
    print("\n[3] PERSISTENT ANCHORING (it survives reindexing)")
    print("─" * 74)
    for a in ancres:
        if a["source"]:
            anc = ancre_persistante(a["document"], a["page"], a["frag_id"])
            print(f"  {a['frag_id']} → {anc}")
    print("  (The address is keyed on document, page and fragment id, never on the")
    print("   position in the index: a reindexing breaks nothing.)")

    # ---- 4) Verification of exactitude ----
    print("\n[4] CITATION ACCURACY")
    print("─" * 74)
    sourcees = sum(a["source"] for a in ancres)
    print(f"  Sourced blocks: {sourcees}/{len(ancres)}")
    fid_moy = sum(a["fidelite"] for a in ancres) / len(ancres)
    print(f"  Mean fidelity: {fid_moy:.0%}")

    # ---- 5) The standalone HTML demo ----
    path = Path(__file__).resolve().parent / "demo_citations.html"
    html_citations(rep["question"], ancres, prov, path)
    print("\n[5] THE INTERACTIVE DEMO")
    print("─" * 74)
    print(f"  Page generated: {path.name}")
    print("  Open it in a browser: hover the badges [1], [2]... to see")
    print("  the source fragment in a popover (colour = the fidelity compass).")

    print("\n" + "═" * 74)
    print("THE MESSAGE: an answer without a source is just one more oracle.")
    print("Explainability down to the pixel — a clickable citation, provenance at")
    print("the top, a persistent anchor — makes VERIFICATION an instant gesture,")
    print("leaving the thread of reading. It is a block of trust, not a varnish.")


if __name__ == "__main__":
    main()
