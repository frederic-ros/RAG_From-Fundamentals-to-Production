# -*- coding: utf-8 -*-
"""
Lab 5-2 — Mapping the document estate

Learning objective
------------------
Understand that the quality of an assistant depends first on the quality of its
sources. This script inventories the documents, computes a business priority
from their importance, their reliability and how recently they were updated, and
then sorts them, to bring out what should be indexed first.

Three cases are wired in as examples: a local authority, an industrial SME, and
an HR consultancy.

The lab runs with no API key and no external dependency.
"""

from dataclasses import dataclass
from typing import List


# Qualitative scales mapped to numeric values, centralised and tunable.
IMPORTANCE = {"low": 1, "medium": 2, "high": 3}
RELIABILITY = {"low": 1, "medium": 2, "high": 3}
FRESHNESS = {"obsolete": 0, "old": 1, "up_to_date": 2, "recent": 3}


@dataclass
class Source:
    """A document source and its quality metadata."""

    name: str
    importance: str    # low | medium | high
    reliability: str   # low | medium | high
    freshness: str     # obsolete | old | up_to_date | recent
    owner: str

    def priority(self) -> float:
        """The indexing priority score, normalised to [0, 1].

        Importance weighs the most, since it is what serves the business;
        reliability comes next, being what you can trust; freshness last.
        """
        imp = IMPORTANCE.get(self.importance, 0)
        rel = RELIABILITY.get(self.reliability, 0)
        fre = FRESHNESS.get(self.freshness, 0)
        # Weights 0.5 / 0.3 / 0.2, after each scale has been normalised.
        score = 0.5 * (imp / 3) + 0.3 * (rel / 3) + 0.2 * (fre / 3)
        return round(score, 3)

    def alert(self) -> str:
        """Flag an obvious risk: an important source that is unreliable or stale."""
        if self.importance == "high" and self.reliability == "low":
            return "IMPORTANT but UNRELIABLE — make it dependable before indexing"
        if self.freshness == "obsolete":
            return "OBSOLETE — exclude it, or bring it up to date"
        return ""


def show_map(title: str, sources: List[Source]) -> None:
    """Print the inventory, sorted by decreasing priority."""
    width = 100
    print("=" * width)
    print(title)
    print("=" * width)
    print(f"{'Source':38s} | {'Import.':8s} | {'Relia.':7s} | {'Updated':11s} | {'Prio':5s} | Owner")
    print("-" * width)

    for s in sorted(sources, key=lambda x: x.priority(), reverse=True):
        print(
            f"{s.name[:38]:38s} | {s.importance:8s} | {s.reliability:7s} | "
            f"{s.freshness:11s} | {s.priority():.3f} | {s.owner}"
        )

    alerts = [(s.name, s.alert()) for s in sources if s.alert()]
    if alerts:
        print("\nQuality alerts:")
        for name, a in alerts:
            print(f"  ! {name}: {a}")


LOCAL_AUTHORITY_CASE: List[Source] = [
    Source("Internal regulations", "high", "high", "up_to_date", "HR department"),
    Source("Remote work guide", "high", "high", "recent", "HR department"),
    Source("Leave guide", "high", "high", "up_to_date", "HR department"),
    Source("HR procedures", "high", "medium", "up_to_date", "HR department"),
    Source("Service notes", "medium", "medium", "old", "General management"),
    Source("Works council minutes", "low", "medium", "old", "Council secretariat"),
]

SME_CASE: List[Source] = [
    Source("Technical manuals", "high", "high", "recent", "Design office"),
    Source("Quality procedures", "high", "high", "up_to_date", "Quality department"),
    Source("ISO standards", "high", "high", "up_to_date", "Quality department"),
    Source("Product sheets", "medium", "high", "recent", "Marketing"),
    Source("After-sales reports", "medium", "medium", "recent", "Support"),
    Source("Internal FAQs", "medium", "low", "old", "Support"),
    Source("Old 2019 catalogue", "high", "low", "obsolete", "Marketing"),
]


HR_CONSULTANCY_CASE: List[Source] = [
    Source("Collective agreements per client", "high", "high", "up_to_date", "Legal team"),
    Source("Company agreements per client", "high", "high", "recent", "HR consultants"),
    Source("Payroll scales / statutory notes", "high", "high", "recent", "Payroll team"),
    Source("The consultancy's internal procedures", "medium", "high", "up_to_date", "Management"),
    Source("FAQs and client tickets", "medium", "medium", "recent", "Support"),
    Source("An old agreement, never revised", "high", "low", "obsolete", "Legal team"),
]


def main() -> None:
    print("Lab 5-2 — Mapping the document estate\n")
    print("The priority combines importance (0.5), reliability (0.3) and freshness (0.2).\n")

    show_map("CASE A — a local authority: the town of Val-sur-Loire", LOCAL_AUTHORITY_CASE)
    print("\n")
    show_map("CASE B — an industrial SME: MecaTech", SME_CASE)
    print("\n")
    show_map("CASE C — an HR and payroll consultancy: PaiePro Conseil", HR_CONSULTANCY_CASE)

    print("\n" + "=" * 100)
    print("WHAT TO REMEMBER")
    print("=" * 100)
    print("- Not all sources are equal: a map ranks them objectively.")
    print("- An important but unreliable source is a risk, not an asset.")
    print("- The inventory comes BEFORE choosing an indexing technology.")


if __name__ == "__main__":
    main()
