# -*- coding: utf-8 -*-
"""
Lab 5-5 — Preparing the move to production

Learning objective
------------------
Understand that the success of a RAG project depends as much on governance as on
technology. This script builds a risk / impact / corrective action matrix,
computes a criticality level (probability times impact), and sets out a list of
Go / No-Go criteria to check before any production deployment.

Three cases are wired in as examples: a local authority, an industrial SME, and
a multi-client HR consultancy.

The lab runs with no API key and no external dependency.
"""

from dataclasses import dataclass
from typing import List


LEVEL = {1: "low", 2: "medium", 3: "high"}


@dataclass
class Risk:
    """A project risk and how it is handled."""

    label: str
    probability: int   # 1..3
    impact: int        # 1..3
    corrective_action: str
    owner: str

    def criticality(self) -> int:
        return self.probability * self.impact

    def criticality_level(self) -> str:
        c = self.criticality()
        if c >= 6:
            return "CRITICAL"
        if c >= 3:
            return "to watch"
        return "acceptable"


def show_matrix(title: str, risks: List[Risk]) -> None:
    width = 100
    print("=" * width)
    print(title)
    print("=" * width)
    print(f"{'Risk':44s} | P | I | Crit. | Level         | Owner")
    print("-" * width)

    for r in sorted(risks, key=lambda x: x.criticality(), reverse=True):
        print(
            f"{r.label[:44]:44s} | {r.probability} | {r.impact} | "
            f"{r.criticality():>4}  | {r.criticality_level():13s} | {r.owner}"
        )

    print("\nCorrective actions, in order of criticality:")
    for r in sorted(risks, key=lambda x: x.criticality(), reverse=True):
        print(f"  - {r.label} -> {r.corrective_action}")


GO_NOGO_CRITERIA: List[str] = [
    "Priority sources up to date and dated",
    "Every answer cites its source",
    "Access rights to sensitive data verified",
    "Data separation verified (multi-client or multi-department cases)",
    "Evaluation set passed, with acceptable recall and precision",
    "An owner named for keeping the system operational",
    "A procedure in place for reporting a wrong answer",
]


LOCAL_AUTHORITY_CASE: List[Risk] = [
    Risk("Obsolete regulation indexed", 2, 3,
         "Purge the expired sources, and make a validity date mandatory", "HR department"),
    Risk("Contradictory service note", 3, 2,
         "A hierarchy of sources: regulations above service notes", "General management"),
    Risk("Uncontrolled access to HR data", 2, 3,
         "Separate the access by user profile", "IT department"),
    Risk("An unsourced answer presented as certain", 2, 2,
         "A source citation mandatory in every answer", "Project team"),
]

SME_CASE: List[Risk] = [
    Risk("The wrong version of a manual served", 3, 3,
         "One reference version, and the older ones withdrawn", "Design office"),
    Risk("An expired quality procedure", 2, 3,
         "A quarterly quality review of the sources", "Quality department"),
    Risk("A wrong after-sales diagnosis", 2, 3,
         "Human validation mandatory before any field action", "Support"),
    Risk("Uncontrolled running cost", 2, 2,
         "Monthly tracking of query volume and cost", "Management"),
]


HR_CONSULTANCY_CASE: List[Risk] = [
    Risk("Information leaking between clients", 3, 3,
         "Strict separation per client, and mandatory filtering at query time", "IT / DPO"),
    Risk("An expired collective agreement served", 2, 3,
         "Legal review, plus a validity date on every document", "Legal team"),
    Risk("The wrong client tied to an answer", 2, 3,
         "A client identifier mandatory in every query and every source", "Project team"),
    Risk("Personal payroll data exposed", 2, 3,
         "Data minimisation, plus access control by profile", "DPO"),
    Risk("Liability for wrong advice given to a client", 2, 2,
         "Human validation before anything is sent to the client", "Management"),
]


def show_go_nogo() -> None:
    width = 100
    print("\n" + "=" * width)
    print("GO / NO-GO CRITERIA BEFORE GOING TO PRODUCTION")
    print("=" * width)
    for i, criterion in enumerate(GO_NOGO_CRITERIA, start=1):
        print(f"  [ ] {i}. {criterion}")
    print("\nThe rule: one criterion unmet is a NO-GO.")


def main() -> None:
    print("Lab 5-5 — Preparing the move to production\n")
    print("Criticality = probability x impact, on scales of 1 to 3.\n")

    show_matrix("CASE A — a local authority: the town of Val-sur-Loire", LOCAL_AUTHORITY_CASE)
    print("\n")
    show_matrix("CASE B — an industrial SME: MecaTech", SME_CASE)
    print("\n")
    show_matrix("CASE C — a multi-client HR consultancy: PaiePro Conseil", HR_CONSULTANCY_CASE)

    show_go_nogo()

    print("\n" + "=" * 100)
    print("WHAT TO REMEMBER")
    print("=" * 100)
    print("- A risk gets ranked: probability times impact, not by feel.")
    print("- The most critical risks are often about governance, not technique.")
    print("- The Go / No-Go protects the organisation: one missing criterion defers the launch.")


if __name__ == "__main__":
    main()
