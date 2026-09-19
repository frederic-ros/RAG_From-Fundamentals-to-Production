# -*- coding: utf-8 -*-
"""
Lab 15-4 — Building a trust policy (Sophie)

Learning objective
------------------
Here the reader leaves technique behind and becomes an ARCHITECT. A piece of
metadata is not a neutral attribute: it is the expression of a business policy.
"Official beats blog", "recent beats old", "approved beats draft" — those rules
are not in the documents, they are a decision of the organisation.

  Metadata is a business policy, not just a set of attributes.

A trust policy is defined in levels, implemented two ways (a strict exclusion
filter, then a weighted trust score), and its effect measured: a ranking by pure
similarity against a ranking governed by the policy.

Search backend: sentence-transformers if available, TF-IDF otherwise.
No API key. Run generate_corpus.py first.
"""

import corpus as C
import embeddings as E

QUESTION = "What is the remote work procedure?"

# --- The trust policy, expressed as data ------------------------------------
# Each rule attributes a weight to a combination of metadata. THAT is the
# policy: a business judgement, changeable without touching the engine.
EXCLUDED = {"repealed", "obsolete"}        # never kept, whatever the score

SOURCE_WEIGHT = {                          # trust priority by source
    "regulatory": 1.5,
    "official": 1.4,
    "supplier": 1.3,
    "internal": 1.1,
    "blog": 0.8,
}
STATUS_WEIGHT = {
    "in force": 1.5,
    "approved": 1.3,
    "published": 1.0,
    "historical": 0.9,
    "draft": 0.7,
}


def trust_score(doc) -> float:
    """Multiply the priority of the source by that of the status: the policy."""
    return (SOURCE_WEIGHT.get(doc.meta("source"), 1.0)
            * STATUS_WEIGHT.get(doc.meta("status"), 1.0))


def main() -> None:
    print("=" * 78)
    print("Lab 15-4 — Building a trust policy (Sophie)")
    print("=" * 78)

    try:
        docs = C.load()
    except FileNotFoundError as e:
        print(f"\n{e}")
        return

    library = [d for d in docs if d.id.startswith("remote-work-")]
    print(f"\nSearch backend: {E.mode()}")
    print(f"Question: \"{QUESTION}\"")

    engine = E.SimilarityEngine([d.text for d in library])
    sims = {library[i].id: s for i, s in engine.rank(QUESTION)}

    print("\n" + "=" * 78)
    print("THE TRUST POLICY (expressed as data)")
    print("=" * 78)
    print("  Excluded outright: " + ", ".join(sorted(EXCLUDED)) + ".")
    print("  Source priority: " + ", ".join(f"{k}={v}" for k, v in SOURCE_WEIGHT.items()))
    print("  Status priority: " + ", ".join(f"{k}={v}" for k, v in STATUS_WEIGHT.items()))

    # --- Ranking A: pure similarity -----------------------------------------
    print("\n" + "=" * 78)
    print("RANKING A — PURE SIMILARITY (no policy)")
    print("=" * 78)
    sim_order = sorted(library, key=lambda d: sims[d.id], reverse=True)
    for rank, d in enumerate(sim_order, start=1):
        print(f"  {rank}. sim {sims[d.id]:.3f} — {d.id} "
              f"(status {d.meta('status')}, source {d.meta('source')})")

    # --- Ranking B: governed by the policy ----------------------------------
    print("\n" + "=" * 78)
    print("RANKING B — GOVERNED BY THE POLICY")
    print("=" * 78)
    print("  Step 1 — strict filter: the forbidden statuses are excluded.")
    kept = [d for d in library if d.meta("status") not in EXCLUDED]
    for d in library:
        if d.meta("status") in EXCLUDED:
            print(f"     excluded: {d.id} (status \"{d.meta('status')}\")")

    print("\n  Step 2 — final score = similarity x trust score.")

    def final_score(d):
        return sims[d.id] * trust_score(d)

    policy_order = sorted(kept, key=final_score, reverse=True)
    for rank, d in enumerate(policy_order, start=1):
        print(f"  {rank}. final {final_score(d):.3f} "
              f"(sim {sims[d.id]:.3f} x trust {trust_score(d):.2f}) — {d.id}")

    # --- Comparison ---------------------------------------------------------
    print("\n" + "=" * 78)
    print("WHAT CHANGED")
    print("=" * 78)
    sim_leader = sim_order[0]
    policy_leader = policy_order[0]
    print(f"  Leader without policy: {sim_leader.id} (status {sim_leader.meta('status')}).")
    print(f"  Leader with policy:    {policy_leader.id} (status {policy_leader.meta('status')}).")
    if sim_leader.id != policy_leader.id:
        print("  The policy demoted a better-scored but less reliable document.")
    print("  The search engine did not change: only the policy decided.")

    print("\nWHAT TO REMEMBER")
    print("- A trust policy is defined in data, not hard-coded in the engine.")
    print("- A strict filter (exclude) and a weighted score (rank) complement each other.")
    print("- Metadata is a business policy — the first step towards calibration.")
    print("\n  In the next lab: the other side of the coin — a filter can hide the truth.")


if __name__ == "__main__":
    main()
