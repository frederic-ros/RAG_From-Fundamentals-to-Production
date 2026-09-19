# -*- coding: utf-8 -*-
"""
Lab 29-3 — LLM-as-a-Judge and its biases

A judge that has not been checked against a human is an opinion disguised as a
metric. This lab looks at three things:

    the position test  — does the verdict change when A and B are swapped?
    the panel          — where do two judges of different strictness diverge?
    Cohen's kappa      — a numeric verdict on the judge's reliability.

BASELINE (French edition, reproduced here): the faithful answer scores 0.50 and
the hallucinated one 0.00; raw agreement is 80% and kappa 0.60.

The faithful and hallucinated answers, and the ten labelled statements, are
compared against the context by lexical overlap. In the wrong language they all
score 0.00 and the contrast disappears — with no error raised. If the fidelity
of the faithful answer is not clearly above the hallucinated one, that is the
first thing to check.

No API key. Run generate_corpus.py first.
"""

from evalkit import (juge_fidelite, load_fragments, bandeau, _mots, _phrases,
                      cohen_kappa)


def juge_binaire_compare(rep_a, rep_b, contexte, ordre="AB"):
    """A deterministic COMPARISON judge: it prefers the more faithful answer.

    A SLIGHT position bias is simulated — the fallback marginally favours the
    answer presented first, at equal fidelity — to make the phenomenon
    observable and open to discussion.
 """
    fa = juge_fidelite(rep_a, contexte)
    fb = juge_fidelite(rep_b, contexte)
    # The simulated position bias: +0.02 to whichever is presented first
    if ordre == "AB":
        fa_eff, fb_eff = fa + 0.02, fb
    else:
        fa_eff, fb_eff = fa, fb + 0.02
    gagnant = "A" if fa_eff >= fb_eff else "B"
    return gagnant, round(fa, 2), round(fb, 2)


def main():
    bandeau("Lab 29-3 — LLM-as-a-Judge et ses biais")
    docs = load_fragments()
    contexte = next(d["texte"] for d in docs if d["id"] == "D03") + " " + \
        next(d["texte"] for d in docs if d["id"] == "D04")

    # === 1) judging faithful against hallucinated =========================
    # THE WORDING OF THESE TWO IS THE MEASUREMENT. The faithful answer must be
    # supported almost sentence by sentence by the context (D03 + D04), the
    # hallucinated one must not be. Both are compared against the context by
    # lexical overlap, so a French answer against an English context scores 0.00
    # on BOTH and the contrast disappears with no error raised.
    rep_fidele = ("Cavitation is recognised by a gravel-like noise and by "
                  "pitting on the vanes. It is corrected by raising the "
                  "pressure at the suction.")
    rep_hallucinee = ("Cavitation is corrected by adding an anti-foam additive "
                      "to the circuit and by doubling the pump speed.")

    print("\nTHE FIDELITY JUDGE (binary, sentence by sentence):")
    print(f"  faithful answer     : fidelity = {juge_fidelite(rep_fidele, contexte):.2f}")
    print(f"  hallucinated answer : fidelity = {juge_fidelite(rep_hallucinee, contexte):.2f}")
    print("  -> fidelity collapses on the invented answer: each assertion")
    print("    unsupported by the context brings the score down.")

    # === 2) position bias ===============================================
    print("\n" + "─" * 70)
    print("TEST DE POSITION BIAS — on compare (A,B) puis (B,A) :")
    g1, fa, fb = juge_binaire_compare(rep_fidele, rep_hallucinee, contexte, "AB")
    g2, _, _ = juge_binaire_compare(rep_hallucinee, rep_fidele, contexte, "AB")
    print(f"  order (faithful, hallucinated) -> winner: {g1}")
    print(f"  order (hallucinated, faithful) -> winner: "
          f"{'faithful' if g2 == 'B' else 'hallucinated'}")
    print("  -> a robust judge gives the SAME verdict whatever the order.")
    print("     Mitigation: swap the positions and average the two passes.")

    # === 3) panel of juges ==============================================
    print("\n" + "─" * 70)
    print("A PANEL OF TWO JUDGES (different families):")

    def juge_strict(rep, ctx):    # exige 0.7 of recouvrement
        ph = _phrases(rep); mc = _mots(ctx)
        if not ph:
            return 0.0
        ok = sum(1 for p in ph if _mots(p) and
                 len(_mots(p) & mc) / len(_mots(p)) >= 0.7)
        return ok / len(ph)

    for nom, rep in [("faithful", rep_fidele), ("hallucinated", rep_hallucinee)]:
        j1 = juge_fidelite(rep, contexte)      # juge standard (threshold 0.6)
        j2 = juge_strict(rep, contexte)        # juge strict (threshold 0.7)
        ecart = abs(j1 - j2)
        flag = "  DISAGREEMENT" if ecart >= 0.25 else ""
        print(f"  {nom:<13} answer: judge1 = {j1:.2f}  judge2 = {j2:.2f}"
              f"  gap = {ecart:.2f}{flag}")
    print("  -> the gap between judges reveals the zone of uncertainty. A strong")
    print("     disagreement is a case for a human to settle.")

    print("\n" + "─" * 70)
    print("CALIBRATING THE JUDGE AGAINST A HUMAN-LABELLED SAMPLE:")
    print("(the most structuring practice of the chapter: a judge that has")
    print(" checked against a human is only an opinion disguised as a metric)")

    # A small "hand-labelled" sample: ten short statements,
    # each with its context and the verdict a human expert would give.
    # In real use: 50 to 100 examples, labelled by the business.
    echantillon = [
        ("Cavitation produces a gravel-like noise.", contexte, "supported"),
        ("Cavitation is corrected by raising the pressure at the suction.",
         contexte, "supported"),
        ("Cavitation is repaired with an anti-foam additive.",
         contexte, "unsupported"),
        ("Doubling the pump speed corrects cavitation.",
         contexte, "unsupported"),
        ("The vanes show characteristic pitting.",
         contexte, "supported"),
        ("Cavitation has no effect on the vanes.",
         contexte, "unsupported"),
        ("The gravel-like noise is a classic symptom of cavitation.",
         contexte, "supported"),
        ("The motor must be replaced in the event of cavitation.",
         contexte, "unsupported"),
        ("The pressure at the suction influences cavitation.",
         contexte, "supported"),
        ("Cavitation only occurs in summer.",
         contexte, "unsupported"),
    ]

    labels_humain, labels_juge = [], []
    desaccords = []
    for affirmation, ctx, verdict_humain in echantillon:
        score = juge_fidelite(affirmation, ctx)
        verdict_juge = "supported" if score >= 0.6 else "unsupported"
        labels_humain.append(verdict_humain)
        labels_juge.append(verdict_juge)
        if verdict_juge != verdict_humain:
            desaccords.append((affirmation, verdict_humain, verdict_juge))

    kappa = cohen_kappa(labels_humain, labels_juge)
    accord_brut = sum(1 for h, j in zip(labels_humain, labels_juge) if h == j) \
        / len(echantillon)
    print(f"\n  raw agreement       : {accord_brut:.0%} ({len(echantillon)} cas)")
    print(f"  Cohen's kappa       : {kappa:.2f}")
    if kappa >= 0.8:
        verdict = "strong agreement -> the judge is calibrated and can be trusted"
    elif kappa >= 0.6:
        verdict = "fair agreement -> still improvable, worth watching"
    else:
        verdict = "weak agreement -> do NOT deploy this judge without reworking its prompt"
    print(f"  verdict             : {verdict}")
    if desaccords:
        print("\n  Disagreements (judge against human), to examine first:")
        for affirmation, h, j in desaccords:
            print(f"    \"{affirmation}\" — human: {h} / judge: {j}")

    print("\n" + "═" * 70)
    print("THE MESSAGE: the LLM judge has become the standard, but it has biases")
    print("(self-preference, position, a weakness on technical nuance). You do not")
    print("abandon it: you frame it. Force the reasoning before the score,")
    print("THE MESSAGE: an LLM judge is a measuring instrument, and an instrument")
    print("is calibrated before it is trusted. Prefer binary scales, swap the")
    print("positions, use a panel, and CALIBRATE against a human sample before")
    print("deploying — that is what makes automatic judgement trustworthy.")


if __name__ == "__main__":
    main()
