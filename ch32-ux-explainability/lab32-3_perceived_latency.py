# -*- coding: utf-8 -*-
"""
Lab 32-3 — Perceived latency: the time before useful reading
"What counts is not when the answer finishes, but when the reading can start"

Three modes are compared on the same pipeline:

    classic     — nothing appears until the answer is complete;
    streaming   — reading starts at the first token;
    split-screen— the sources appear as soon as the reranking ends, so there is
                  something to read while the answer is still being written.

BASELINE (French edition, reproduced here): a reduction in perceived latency of
83%, 88% and 90% on a simple, a medium and a complex query.

No API key. Run generate_corpus.py first.
"""

from pathlib import Path

from uxkit import (bandeau, LatencyProfile, mesurer_latence_percue,
                  ancrer_citations, etat_confiance, message_operationnel,
                  html_stream, load_fragments, load_answers)


PROFILS = {
    "Simple query": LatencyProfile(t_retrieval=0.6, t_premier_token=1.4,
                                    n_tokens=40, debit_tokens=18),
    "Medium query": LatencyProfile(t_retrieval=1.1, t_premier_token=2.6,
                                     n_tokens=90, debit_tokens=14),
    "Complex query": LatencyProfile(t_retrieval=2.0, t_premier_token=4.3,
                                      n_tokens=160, debit_tokens=10),
}


def main():
    bandeau("Lab 32-3 — Perceived latency: streaming and split-screen")

    # ---- 1) and 2) Measure the perceived latency per mode ----
    print("\n[1] PERCEIVED LATENCY BY MODE (time to the first USEFUL information)")
    print("─" * 74)
    print(f"  {'profil':<18}{'classique':>11}{'streaming':>11}"
          f"{'split-scr.':>11}{'gain split':>12}")
    print("  " + "─" * 70)
    for nom, p in PROFILS.items():
        m = mesurer_latence_percue(p)
        print(f"  {nom:<18}"
              f"{m['classique']['premier_utile']:>9.1f}s"
              f"{m['streaming']['premier_utile']:>9.1f}s"
              f"{m['split_screen']['premier_utile']:>9.1f}s"
              f"{m['gain_percu_vs_classique']:>11.0%}")
    print("\n  Reading: in classic mode the user waits for the WHOLE generation")
    print("  before seeing anything at all. In split-screen, they see the sources")
    print("  as soon as the reranking ends — often 3 to 5 times earlier.")

    # ---- 3) One case in detail ----
    print("\n[2] IN DETAIL — a complex query")
    print("─" * 74)
    p = PROFILS["Complex query"]
    m = mesurer_latence_percue(p)
    print(f"  End of reranking (sources ready): {p.t_retrieval:.1f}s")
    print(f"  First token of the answer       : {p.t_premier_token:.1f}s")
    print(f"  Complete answer                 : {m['classique']['total']:.1f}s")
    print("  -> The user checks the sources while the answer is still being")
    print(f"     generated: {m['classique']['total'] - p.t_retrieval:.1f}s of")
    print("     \"free\" active verification.")

    # ---- 4) The split-screen HTML demo ----
    frags = load_fragments()
    rep = next(r for r in load_answers() if r["id"] == "R02")
    ancres = ancrer_citations(rep["blocs"], frags)
    etat = etat_confiance(rep["score_retrieval"], rep["score_generation"],
                          rep["n_sources"], rep["contradiction"])
    msg = message_operationnel(etat, rep["n_sources"], rep["fraicheur"])
    path = Path(__file__).resolve().parent / "demo_stream.html"
    html_stream(rep["question"], ancres, msg,
                {"debit_tokens": PROFILS["Medium query"].debit_tokens}, path)
    print("\n[3] THE INTERACTIVE DEMO (split-screen)")
    print("─" * 74)
    print(f"  Page generated: {path.name}")
    print("  Open it: the answer streams on the left, the sources are already there")
    print("  on the right. The coloured banner carries the trust state (Lab 32-2).")

    print("\n" + "═" * 74)
    print("THE MESSAGE: optimise the EXPERIENCE, not just the raw performance.")
    print("Separating answer from sources turns waiting into verification.")
    print("The first token is no longer the first useful moment: the sources")
    print("come first. Felt latency drops without touching real latency.")


if __name__ == "__main__":
    main()
