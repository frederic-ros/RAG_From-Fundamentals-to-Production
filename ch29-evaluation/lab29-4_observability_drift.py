# -*- coding: utf-8 -*-
"""
Lab 29-4 — Online observability and silent drift
"The danger is not the failure that rings, it is the one that does not"

The aim: show the difference between OFFLINE evaluation (a frozen golden set)
and ONLINE observability (production traces). A production stream over several
days is simulated, and a SILENT DRIFT detected: the technical metrics stay good
while relevance to the user degrades, because the corpus has aged and new
questions have appeared.

The steps: simulate time windows of traffic (day 1 to day 5); on each window
measure fidelity (technical) AND a proxy for user satisfaction (coverage of the
questions actually asked); then detect the divergence — fidelity flat, coverage
falling.

That divergence is the signature of the drift.

No API key. Run generate_corpus.py first.
"""

from evalkit import RAGPipeline, load_fragments, juge_fidelite, bandeau


# Flux of production simulated : to partir of the jour 3, the users posent 
# questions on a sujet ABSENT of the corpus (new pompe P-77 mise in service).
# THE TRAFFIC QUESTIONS ARE THE MEASUREMENT. Days 1 and 2 must be fully covered
# by the corpus; from day 3 the users start asking about pump P-77, which is
# ABSENT from it. That is what makes the coverage fall while the technical
# fidelity stays flat — the signature of the drift.
#
# In the wrong language none of these match the corpus, coverage is already low
# on day 1, and the drift signal fires from the first window: the lab still runs
# and still prints a table, but it no longer shows a drift.
TRAFIC = {
    "Day 1": ["How is cavitation diagnosed in the pump casing?",
              "What are the steps of electrical lock-off?"],
    "Day 2": ["How often are the bearings greased?",
              "What vibration threshold requires an intervention?"],
    "Day 3": ["How is cavitation corrected?",
              "What is the maintenance procedure for pump P-77?"],   # P-77 absent
    "Day 4": ["What is the tightening torque for the flanges?",
              "What are the spare parts for pump P-77?"],            # P-77 absent
    "Day 5": ["What is the minimum tank level?",
              "How often is pump P-77 overhauled?"],                 # P-77 absent
}



def main():
    bandeau("Lab 29-4 — Online observability and silent drift")
    docs = load_fragments()
    pipe = RAGPipeline(docs, k=3)

    print(f"\n{'Window':<10}{'tech. fidelity':>16}{'user coverage':>16}  signal")
    print("─" * 60)

    # Proxy of satisfaction user : the answer mentionne-t-it the entity
    # the key of the question? P-77 asked but P-42 found means dissatisfaction, even
    # even if the retrieval score is high). This is exactly the blind spot 
    # metrics techniques.
    import re as _re

    def entite_cle(q):
        m = _re.search(r"p[\- ]?\d+", q.lower())
        return m.group().replace(" ", "-") if m else None

    historique = []
    for jour, questions in TRAFIC.items():
        fids, couvs = [], []
        for q in questions:
            rep = pipe.repondre(q)
            ctx = " ".join(f["texte"] for f in rep.fragments)
            fids.append(juge_fidelite(rep.reponse, ctx))
            # Satisfaction: if the question targets a precise entity, the answer
            # must the contenir ; sinon on retombe on the relevance of the score.
            ent = entite_cle(q)
            if ent:
                couvs.append(1.0 if ent.replace("-", "") in
                             ctx.lower().replace("-", "").replace(" ", "")
                             else 0.0)
            else:
                couvs.append(1.0 if rep.fragments and
                             rep.fragments[0]["score"] > 0.15 else 0.0)
        fid = sum(fids) / len(fids)
        couv = sum(couvs) / len(couvs)
        historique.append((jour, fid, couv))

        signal = ""
        if couv < 0.6 <= fid:
            signal = "SILENT DRIFT"
        print(f"{jour:<10}{fid:>15.0%}{couv:>17.0%}  {signal}")

    print("─" * 60)
    print("\nREADING: the TECHNICAL fidelity stays high — the system always")
    print("answers \"correctly\" on what it finds — but the COVERAGE of the real")
    print("questions collapses from day 3, when the")
    print("users are asking about a pump absent from the corpus.")
    print("\nAn alarm based on fidelity alone would NEVER have sounded. That is")
    print("what makes silent drift dangerous: you have to watch the indicators on")
    print("the USER SIDE — coverage, abstention, feedback — not only the")
    print("technical metrics.")

    print("\n" + "═" * 60)
    print("THE MESSAGE: offline evaluation proves a system is good on the day it")
    print("is deployed. Online observability proves it STAYS good. The two are")
    print("complementary: the living golden set absorbs the new questions detected")
    print("in production, so the drift becomes visible.")


if __name__ == "__main__":
    main()
