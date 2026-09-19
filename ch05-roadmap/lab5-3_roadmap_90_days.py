# -*- coding: utf-8 -*-
"""
Lab 5-3 — Building a 90-day roadmap

Learning objective
------------------
Turn an idea into a realistic deployment trajectory. This script breaks a RAG
project into four phases (scoping, document preparation, prototype, business
validation), checks that the durations fit inside 90 days, and checks that each
phase really carries its deliverables, risks, indicators and owner.

The lab runs with no API key and no external dependency.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Phase:
    """One phase of the roadmap."""

    name: str
    duration_days: int
    owner: str
    deliverables: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    indicators: List[str] = field(default_factory=list)

    def problems(self) -> List[str]:
        """Check that a phase has been filled in properly."""
        p: List[str] = []
        if self.duration_days <= 0:
            p.append("duration not positive")
        if not self.owner.strip():
            p.append("owner missing")
        if not self.deliverables:
            p.append("no deliverable")
        if not self.indicators:
            p.append("no indicator")
        return p


PHASES: List[Phase] = [
    Phase(
        name="Phase 1 — Scoping",
        duration_days=15,
        owner="Business project manager",
        deliverables=["Approved scoping sheet (Lab 5-1)", "List of target users"],
        risks=["Perimeter too broad", "Business sponsor not engaged"],
        indicators=["Scoping sheet signed", "Priority use case chosen"],
    ),
    Phase(
        name="Phase 2 — Document preparation",
        duration_days=30,
        owner="Document lead",
        deliverables=["Map of the estate (Lab 5-2)", "Priority sources cleaned up"],
        risks=["Obsolete documents", "Access rights not clarified"],
        indicators=["% of priority sources ready", "An owner identified per source"],
    ),
    Phase(
        name="Phase 3 — Prototype",
        duration_days=30,
        owner="Technical team",
        deliverables=["A RAG prototype on the priority case", "First answers traced"],
        risks=["Over-engineering", "Answers with no sources"],
        indicators=["A demonstrable prototype", "Every answer cites its source"],
    ),
    Phase(
        name="Phase 4 — Business validation",
        duration_days=15,
        owner="Reference users",
        deliverables=["Evaluation set completed (Lab 5-4)", "Validation report"],
        risks=["Vague success criteria", "Validation by technicians alone"],
        indicators=["Recall and precision measured", "Go / No-Go documented"],
    ),
]

DAY_BUDGET = 90


def show_roadmap(phases: List[Phase]) -> None:
    width = 78
    running = 0
    print("=" * width)
    print("A 90-DAY ROADMAP — RAG project")
    print("=" * width)

    for phase in phases:
        start = running + 1
        running += phase.duration_days
        print(f"\n{phase.name}  (days {start} to {running} — {phase.duration_days} d)")
        print(f"  Owner: {phase.owner}")
        print("  Deliverables:")
        for d in phase.deliverables:
            print(f"    - {d}")
        print("  Risks:")
        for r in phase.risks:
            print(f"    - {r}")
        print("  Indicators:")
        for i in phase.indicators:
            print(f"    - {i}")

        problems = phase.problems()
        if problems:
            print("  ! Phase incomplete: " + ", ".join(problems))

    print("\n" + "-" * width)
    total = sum(p.duration_days for p in phases)
    print(f"Total planned duration: {total} days (budget: {DAY_BUDGET} days)")
    if total <= DAY_BUDGET:
        print(f"Validation: the roadmap FITS inside {DAY_BUDGET} days.")
    else:
        overrun = total - DAY_BUDGET
        print(f"Validation: OVERRUN of {overrun} days — tighten one phase.")


def main() -> None:
    print("Lab 5-3 — Building a 90-day roadmap\n")
    print("Prerequisites: Lab 5-1 (scoping) and Lab 5-2 (the document estate).\n")

    show_roadmap(PHASES)

    print("\n" + "=" * 78)
    print("WHAT TO REMEMBER")
    print("=" * 78)
    print("- A roadmap ties the need to dated, measurable deliverables.")
    print("- The prototype only arrives in phase 3: document preparation comes first.")
    print("- Every phase has an owner: with no owner, a task does not move.")
    print("- Depending on the context, one phase carries a hard constraint: for a")
    print("  multi-client HR consultancy, keeping client data separated is a phase 2")
    print("  deliverable, not an end-of-project option.")


if __name__ == "__main__":
    main()
