# -*- coding: utf-8 -*-
"""
Lab 31-2 — ABAC and governance metadata
"The security of a RAG is not decided at the output, but at the source"

Access control is applied AT THE RETRIEVAL, attribute by attribute: a document
outside the subject's clearance or outside their business scope never enters the
LLM's context at all.

Five things are shown:

  - the same query run by five different profiles, returning five different sets;
  - the business scope, which is orthogonal to the clearance level;
  - governance by status: an obsolete or expired document is set aside;
  - the parallel defence clearance scale (Jean-Claude);
  - reranking by confidence: at equal similarity, a document under review is
    demoted beneath a valid one.

No API key. Run generate_corpus.py first.
"""

from secukit import (bandeau, Search, politique_abac,
                     load_documents, load_subjects)


def main():
    bandeau("Lab 31-2 — ABAC and governance metadata")
    docs = load_documents()
    sujets = load_subjects()
    rech = Search(docs)
    AUJ = "2026-06-26"

    # ---- 1) A same question, several habilitations ----
    print("\n[1] THE SAME QUESTION, DIFFERENT RESULTS BY CLEARANCE")
    print("Question: \"Which documents mention salaries, mergers or budget?\"")
    print("─" * 74)
    question = "salary scale merger budget strategy investment"
    for cle in ["visiteur_public", "karim_technicien", "claire_drh",
                "julien_architecte"]:
        sujet = sujets[cle]
        res = rech.chercher(question, sujet=sujet, k=4, aujourdhui=AUJ)
        ids = [f"{f['id']}({f['niveau']})" for f in res]
        print(f"  {sujet['nom']:<34} → {ids}")

    # ---- 2) Proof: no forbidden document EVER surfaces ----
    print("\n[2] PROOF OF NON-LEAKAGE (over the whole corpus)")
    print("─" * 74)
    fuites = 0
    for cle, sujet in sujets.items():
        # Ask for the WHOLE corpus (a very large k), filtered by ABAC
        res = rech.chercher("document procedure information data",
                            sujet=sujet, k=len(docs), aujourdhui=AUJ)
        for f in res:
            decision = politique_abac(f, sujet, AUJ)
            if not decision["accorde"]:
                fuites += 1
                print(f"  !! LEAK: {sujet['nom']} received {f['id']} "
                      f"({decision['motif']})")
    if fuites == 0:
        print("  No forbidden document was returned, for any profile.")
        print("    The ABAC filter applies BEFORE generation: complete sealing.")

    # ---- 3) Governance: the obsolete and the expired are excluded ----
    print("\n[3] ACTIVE GOVERNANCE — obsolete and expired set aside")
    print("─" * 74)
    julien = sujets["julien_architecte"]
    # D12 obsolete (the 2019 purge), D13 expired (the regulatory threshold)
    res = rech.chercher("hydraulic purge procedure discharge threshold",
                        sujet=julien, k=6, aujourdhui=AUJ)
    ids = [f["id"] for f in res]
    print(f"  Results (Julien): {ids}")
    print(f"  D12 (obsolete) present? {'yes !!' if 'D12' in ids else 'no'}")
    print(f"  D13 (expired 2026-01-01) present? "
          f"{'yes !!' if 'D13' in ids else 'no'}")
    # The explainable detail on D12 and D13
    for did in ("D12", "D13"):
        frag = next(d for d in docs if d["id"] == did)
        dec = politique_abac(frag, julien, AUJ)
        print(f"     {did} -> granted={dec['accorde']} ({dec['motif']})")

    # ---- 4) Scale defense (Jean-Claude) ----
    print("\n[4] DEFENCE CLEARANCE (Jean-Claude)")
    print("─" * 74)
    q_def = "radar surveillance perimeter access sensitive zone"
    for cle in ["jc_diffusion_restreinte", "jc_secret"]:
        sujet = sujets[cle]
        res = rech.chercher(q_def, sujet=sujet, k=4, aujourdhui=AUJ)
        ids = [f"{f['id']}({f['niveau']})" for f in res]
        print(f"  {sujet['nom']:<40} → {ids}")
    print("  (Top secret D17 only surfaces for a subject cleared to 'tres_secret'.)")

    # ---- Reranking by trust ----
    print("\n[5] TRUST-BASED RERANKING (qualitative governance)")
    print("─" * 74)
    res = rech.chercher("hydraulic purge procedure", sujet=julien, k=3,
                        aujourdhui=AUJ, reranking_confiance=True)
    for f in res:
        print(f"  {f['id']} sim={f['score']:.2f} conf={f['confiance']:.2f} "
              f"→ score_final={f['score_final']:.2f}  {f['titre'][:30]}")

    print("\n" + "═" * 74)
    print("THE MESSAGE: the security of a RAG is not decided at the output but AT")
    print("SOURCE. ABAC filters during retrieval: a document outside the user's clearance or")
    print("outside the scope never enters the LLM context at all. Governance")
    print("(status, expiry, confidence) sets aside the stale and prioritises the safe.")


if __name__ == "__main__":
    main()
