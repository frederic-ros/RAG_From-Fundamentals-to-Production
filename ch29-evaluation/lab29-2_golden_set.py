# -*- coding: utf-8 -*-
"""
Lab 29-2 — Making the thermometer: a synthetic golden set plus expert validation
"A 100% synthetic golden set measures the agreement between two errors"

The aim: generate a golden set synthetically (an "LLM" walks the fragments and
produces questions plus reference answers), then show why HUMAN VALIDATION is
not negotiable. A business-term error is injected into the generator, and the
evaluation is seen validating a system that is wrong "consistently with the
generator".

The steps: generate (question, reference) pairs from the fragments; simulate a
bias in the generator, confusing the emergency stop with the cold stop; show
that without validation the evaluation is blind to that error; then apply an
"expert filter" that corrects it, and measure the difference.

No API key. Run generate_corpus.py first.
"""

from evalkit import load_fragments, llm, _phrases, bandeau


def generate_pair(fragment):
    """Generate a (question, reference answer) pair for a fragment.
 With Ollama : true LLM. Sinon : gabarit deterministic (1re sentence -> Q/R)."""
    rep = llm("From the text, propose ONE factual question and its answer, "
              'au format "Q: ... | R: ...".\nTexte : ' + fragment["texte"])
    if rep and "Q:" in rep and "R:" in rep:
        q = rep.split("Q:")[1].split("R:")[0].strip(" |\n")
        r = rep.split("R:")[1].strip()
        return {"question": q, "reference": r}
    # repli : question gabarit on the title, answer = 1re sentence
    phrases = _phrases(fragment["texte"])
    return {"question": f"What does the documentation say about: {fragment['titre']}?",
            "reference": phrases[0] if phrases else fragment["texte"]}


def main():
    bandeau("Lab 29-2 — A synthetic golden set plus expert validation")
    docs = load_fragments()

    # === 1) the raw synthetic generation ==================================
    sous_corpus = [d for d in docs if d["id"] in ("D01", "D02", "D03", "D07")]
    golden_brut = []
    for d in sous_corpus:
        paire = generate_pair(d)
        paire["fragment"] = d["id"]
        golden_brut.append(paire)

    print("\nTHE RAW SYNTHETIC GOLDEN SET:")
    for g in golden_brut:
        print(f"  [{g['fragment']}] Q: {g['question'][:60]}")
        print(f"          R: {g['reference'][:70]}")

    # === 2) the generator bias (simulated, reproducible) ==================
    # A generator is simulated that CONFUSES the emergency stop with the cold
    # stop: for D01 (emergency) it produces a reference drawn from D02 (cold).
    biais = {
        "fragment": "D01",
        "question": "What is the emergency stop procedure for the pump?",
        "reference": "The stop follows a gradual fifteen-minute procedure "
                     "with thermal stabilisation.",  # FALSE for the emergency procedure!
    }
    print("\n" + "─" * 70)
    print("THE GENERATOR BIAS (injected):")
    print(f"  Q: {biais['question']}")
    print(f"  R (generated, WRONG): {biais['reference']}")
    print("  -> that reference describes the COLD stop, not the EMERGENCY stop.")
    print("     A system answering \"cold stop\" would be marked CORRECT")
    print("    by this golden set: you measure the agreement between two errors.")

    # === 3) filtre expert ===============================================
    d01 = next(d for d in docs if d["id"] == "D01")
    correction = {
        "fragment": "D01",
        "question": biais["question"],
        "reference": "The emergency stop cuts the supply in under two "
                     "seconds, only in the event of immediate danger.",
        "source_correction": d01["texte"][:60] + "…",
    }
    print("\n" + "─" * 70)
    print("FILTRE EXPERT (validation humaine) :")
    print(f"  R (corrected by the expert): {correction['reference']}")
    print(f"  supported by source fragment D01: \"{correction['source_correction']}\"")

    print("\n" + "═" * 70)
    print("THE MESSAGE: generating the golden set is an enormous saving of time,")
    print("but a 100% synthetic set inherits the biases of the generating model.")
    print("Expert validation — checking and correcting, far quicker than creating")
    print("— is the only rampart: without it you measure agreement with another")
    print("model, not business correctness. On a safety instruction, the")
    print("distinction stops the plant, or fails to.")
    print("\nWHAT TO REMEMBER: the golden set is ALIVE. The real questions from")
    print("production (shadow traffic, feedback) l'enrichissent en continu.")


if __name__ == "__main__":
    main()
