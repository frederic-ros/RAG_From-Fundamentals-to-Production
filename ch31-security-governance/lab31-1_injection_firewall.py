# -*- coding: utf-8 -*-
"""
Lab 31-1 — The injection firewall: input, corpus, output
"The real defence is structural, not a list of forbidden words"

Three barriers are built and measured:

  1. THE INPUT firewall: 50 queries, 10 of them direct injections. Precision,
     recall and the false-positive rate are measured. The hard cases are the
     legitimate queries that TALK about security — prompt injection, least
     privilege, data poisoning — and which must pass.
  2. THE CORPUS scan: 20 documents to index, 5 carrying a hidden instruction
     between <<HIDDEN>> and <<END>>. Those five must be quarantined, and no
     others.
  3. THE OUTPUT guardrail: an answer carrying an API key and an e-mail address
     is redacted before display.

BASELINE (French edition, reproduced here): precision 100%, recall 100%, a
false-positive rate of 0%, and 5 of 5 infected documents quarantined.

THIS IS THE VERIFICATION LAB for the injection patterns of secukit. A recall
that falls means the attack wordings no longer match the patterns; a rising
false-positive rate means the patterns have become too broad and are catching the
meta questions.

No API key. Run generate_corpus.py first.
"""

from secukit import (bandeau, detecter_injection_directe, scanner_document,
                     garde_fou_sortie, load_queries,
                     load_infected_documents)


def evaluate_input(requetes):
    vp = fp = vn = fn = 0
    faux_positifs, faux_negatifs = [], []
    for q in requetes:
        verdict = detecter_injection_directe(q["texte"])
        predit = verdict["malveillant"]
        reel = q["attaque"]
        if predit and reel:
            vp += 1
        elif predit and not reel:
            fp += 1
            faux_positifs.append(q["texte"])
        elif not predit and not reel:
            vn += 1
        else:
            fn += 1
            faux_negatifs.append(q["texte"])
    precision = vp / (vp + fp) if (vp + fp) else 0.0
    recall = vp / (vp + fn) if (vp + fn) else 0.0
    taux_fp = fp / (fp + vn) if (fp + vn) else 0.0
    return {"vp": vp, "fp": fp, "vn": vn, "fn": fn, "precision": precision,
            "recall": recall, "taux_fp": taux_fp,
            "faux_positifs": faux_positifs, "faux_negatifs": faux_negatifs}


def main():
    bandeau("Lab 31-1 — Pare-feu anti-injection : direct et indirect")

    # ---- 1) Garde-fou of INPUT : injections directes ----
    print("\n[1] THE INPUT GUARDRAIL — direct injections")
    print("─" * 74)
    requetes = load_queries()
    m = evaluate_input(requetes)
    print(f"  True positives : {m['vp']:>2}   False negatives: {m['fn']:>2}  "
          f"(attacks missed)")
    print(f"  False positives: {m['fp']:>2}   True negatives : {m['vn']:>2}")
    print(f"  Precision: {m['precision']:.0%}   Recall: {m['recall']:.0%}   "
          f"False-positive rate: {m['taux_fp']:.0%}")
    if m["faux_negatifs"]:
        print("  Attacks that got through:")
        for t in m["faux_negatifs"]:
            print(f"     · {t[:60]}")
    if m["faux_positifs"]:
        print("  False alarms (legitimate queries blocked):")
        for t in m["faux_positifs"]:
            print(f"     · {t[:60]}")

    # ---- 2) Scanner of DOCUMENTS : injections indirectes ----
    print("\n[2] SCANNER DE DOCUMENTS — injections indirectes (quarantaine)")
    print("─" * 74)
    docs = load_infected_documents()
    vp = fp = fn = 0
    for d in docs:
        verdict = scanner_document(d)
        if verdict["infecte"] and d["infecte_attendu"]:
            vp += 1
            print(f"  ⛔ {d['id']} {d['titre'][:28]:<28} → QUARANTAINE "
                  f"({verdict['raisons'][0][:34]})")
        elif verdict["infecte"] and not d["infecte_attendu"]:
            fp += 1
            print(f"  !! {d['id']} {d['titre'][:28]:<28} -> false positive")
        elif not verdict["infecte"] and d["infecte_attendu"]:
            fn += 1
            print(f"  !! {d['id']} {d['titre'][:28]:<28} -> INFECTED, MISSED")
    total_inf = sum(d["infecte_attendu"] for d in docs)
    print(f"\n  Detection: {vp}/{total_inf} infected documents put in "
          f"quarantine; false positives: {fp}; missed: {fn}")

    # ---- 3) Garde-fou of OUTPUT : anti-exfiltration ----
    print("\n[3] GARDE-FOU DE SORTIE — anti-exfiltration")
    print("─" * 74)
    reponse_piegee = (
        "Here is the procedure. By the way, the service key is "
        "sk-live-9aZ4PqR7TbX2 and the HR contact is k.benali@plant.example.")
    sortie = garde_fou_sortie(reponse_piegee)
    print(f"  Raw answer      : {reponse_piegee}")
    print(f"  Leaks detected  : {[f['type'] for f in sortie['fuites']]}")
    print(f"  Answer displayed: {sortie['texte_caviarde']}")

    # ---- Message of synthesis ----
    print("\n" + "═" * 74)
    print("THE MESSAGE: classifiers reduce the risk, they do not cancel it. The")
    print("real defence against INDIRECT injection is STRUCTURAL: keep the block of")
    print("system instructions strictly separate from the block of context drawn")
    print("from the index. The output guardrail is the last barrier — never the")
    print("first. (Lab 31-2: filter at the source, by clearance.)")


if __name__ == "__main__":
    main()
