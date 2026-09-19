# -*- coding: utf-8 -*-
"""
Lab 7-5 — The ROI dashboard: quantifying the document effort (Sophie)

Learning objective
------------------
Take on the stance of a project manager: defend a budget decision oriented
towards data quality rather than towards algorithmic escalation. The script
compares two strategies for Sophie's organisation:

  Strategy A — Optimise the pipeline with code (reranking, agents): a high and
      recurring development cost, a real gain but one that plateaus if the
      documents stay hostile.

  Strategy B — Apply an AI-ready charter to the critical procedures: a cost in
      human rewriting time, and a strong gain, because it attacks the cause.

The model computes a total cost, an estimated quality gain, and a tipping point:
the number of documents beyond which one strategy becomes more economical.

No external dependency, no API key. The assumptions are explicit and can be
changed at the top of the file.
"""

from dataclasses import dataclass
from typing import List

# ---------------------------------------------------------------------------
# Assumptions, all changeable. Illustrative values, not truths.
# ---------------------------------------------------------------------------
N_CRITICAL_DOCUMENTS = 100          # Sophie's most critical procedures

# Strategy A — code
INITIAL_DEV_COST = 25000.0          # euros: developing reranking plus agents
DEV_MAINTENANCE_PER_YEAR = 8000.0   # euros a year: maintaining the pipeline
CODE_QUALITY_GAIN = 0.20            # +20% answer quality, and it plateaus

# Strategy B — the AI-ready charter
REWRITE_HOURS_PER_DOC = 1.5         # hours per document rewritten
HOURLY_COST = 45.0                  # euros an hour (human time)
AI_READY_QUALITY_GAIN = 0.45        # +45% quality, because it attacks the cause


@dataclass
class Strategy:
    name: str
    total_cost: float
    quality_gain: float

    def ratio(self) -> float:
        """The quality gain per thousand euros invested."""
        if self.total_cost == 0:
            return 0.0
        return self.quality_gain / (self.total_cost / 1000.0)


def code_strategy_cost(years: int) -> float:
    return INITIAL_DEV_COST + DEV_MAINTENANCE_PER_YEAR * years


def ai_ready_strategy_cost(n_documents: int) -> float:
    return n_documents * REWRITE_HOURS_PER_DOC * HOURLY_COST


def effort_impact_matrix() -> List[tuple]:
    """The matrix from the chapter: action -> effort -> impact."""
    return [
        ("Apply heading styles", "low", "very strong"),
        ("Spell out the acronyms", "low", "strong"),
        ("Fill in the metadata", "medium", "very strong"),
        ("Archive the obsolete versions", "high", "very strong"),
        ("Rework the documents entirely", "very high", "maximal"),
    ]


def tipping_point() -> int:
    """The number of documents beyond which the charter costs more than the code,
    over one year.

    Below it, the AI-ready charter is cheaper; above it, the code becomes
    competitive on cost alone — though not on the quality gain.
    """
    code_cost_1yr = code_strategy_cost(1)
    unit_cost_per_doc = REWRITE_HOURS_PER_DOC * HOURLY_COST
    return int(code_cost_1yr / unit_cost_per_doc)


def main() -> None:
    print("=" * 78)
    print("Lab 7-5 — The ROI dashboard: the document effort (Sophie)")
    print("=" * 78)

    # 1) The effort / impact matrix, recalled from the chapter.
    print("\nTHE EFFORT / IMPACT MATRIX")
    print("-" * 78)
    print(f"{'Action':42s} | {'Effort':12s} | Impact")
    print("-" * 78)
    for action, effort, impact in effort_impact_matrix():
        print(f"{action:42s} | {effort:12s} | {impact}")

    # 2) The two strategies compared in figures, over one year.
    code_cost = code_strategy_cost(1)
    ai_cost = ai_ready_strategy_cost(N_CRITICAL_DOCUMENTS)

    strat_a = Strategy("A — code (reranking, agents)", code_cost, CODE_QUALITY_GAIN)
    strat_b = Strategy("B — AI-ready charter (100 procedures)", ai_cost, AI_READY_QUALITY_GAIN)

    print("\n" + "=" * 78)
    print("THE STRATEGIES COMPARED (over one year)")
    print("=" * 78)
    print(f"{'Strategy':40s} | {'Cost (EUR)':>10s} | {'Quality gain':>12s} | ratio")
    print("-" * 78)
    for s in (strat_a, strat_b):
        print(f"{s.name:40s} | {s.total_cost:>10.0f} | {s.quality_gain:>11.0%} | {s.ratio():.3f}")

    best = max((strat_a, strat_b), key=lambda s: s.ratio())
    print(f"\nBest gain-to-cost ratio: {best.name}")

    # 3) The tipping point.
    tipping = tipping_point()
    print("\n" + "=" * 78)
    print("THE TIPPING POINT")
    print("=" * 78)
    print(f"As long as fewer than {tipping} documents are rewritten, the AI-ready")
    print("charter costs less than developing the pipeline, over one year.")
    print(f"Sophie is targeting {N_CRITICAL_DOCUMENTS} critical procedures: "
          f"{'below' if N_CRITICAL_DOCUMENTS < tipping else 'above'} the threshold.")

    # 4) A three-year projection: maintaining the code weighs over time.
    print("\n" + "=" * 78)
    print("A THREE-YEAR PROJECTION")
    print("=" * 78)
    print(f"{'Year':>6s} | {'Cumulative code cost':>22s} | {'Charter cost (one-off)':>24s}")
    print("-" * 78)
    for year in (1, 2, 3):
        cc = code_strategy_cost(year)
        print(f"{year:>6d} | {cc:>20.0f} EUR | {ai_cost:>22.0f} EUR")

    print("\nWHAT TO REMEMBER")
    print("- The AI-ready charter attacks the cause: its quality gain is the stronger one.")
    print("- Code is paid for every year, in maintenance; rewriting is a one-off cost.")
    print("- Above the tipping point, reserve the code for the corpora that deserve it.")
    print("- These figures are illustrative: adjust the assumptions to your own context.")


if __name__ == "__main__":
    main()
