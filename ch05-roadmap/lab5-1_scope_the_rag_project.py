# -*- coding: utf-8 -*-
"""
Lab 5-1 — Scoping a RAG project on one page

Learning objective
------------------
Turn a vague business need into a measurable project. This script does not do
the scoping for you: it supplies a rigorous structure for a scoping sheet, and
checks that no essential section has been forgotten.

A RAG is always the same technical system; what changes is the business context.
Three cases are wired in as examples:

  - a local authority (Val-sur-Loire, 25,000 inhabitants);
  - an industrial SME (MecaTech, 120 employees);
  - a payroll and HR consultancy serving many clients.

The lab runs with no API key and no external dependency.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ScopingSheet:
    """The scoping sheet of a RAG project, fitting on one page."""

    project_name: str
    organisation: str
    perimeter: str
    users: List[str] = field(default_factory=list)
    typical_questions: List[str] = field(default_factory=list)
    ranked_sources: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    def missing_fields(self) -> List[str]:
        """Return the list of sections that are empty or too thin."""
        missing: List[str] = []
        if not self.project_name.strip():
            missing.append("project name")
        if not self.organisation.strip():
            missing.append("organisation")
        if not self.perimeter.strip():
            missing.append("perimeter")
        if len(self.users) < 2:
            missing.append("at least 2 user profiles")
        if len(self.typical_questions) < 3:
            missing.append("at least 3 typical questions")
        if len(self.ranked_sources) < 2:
            missing.append("at least 2 ranked sources")
        if len(self.success_criteria) < 2:
            missing.append("at least 2 success criteria")
        return missing

    def is_complete(self) -> bool:
        return not self.missing_fields()


def show_sheet(sheet: ScopingSheet) -> None:
    """Print the scoping sheet in its one-page format."""
    width = 78
    print("=" * width)
    print(f"SCOPING SHEET — {sheet.project_name}")
    print("=" * width)
    print(f"Organisation: {sheet.organisation}")
    print(f"\nPerimeter\n  {sheet.perimeter}")

    print("\nIntended users")
    for u in sheet.users:
        print(f"  - {u}")

    print("\nTypical questions (what the users will ask)")
    for i, q in enumerate(sheet.typical_questions, start=1):
        print(f"  {i}. {q}")

    print("\nDocument sources, from the highest priority to the lowest")
    for i, s in enumerate(sheet.ranked_sources, start=1):
        print(f"  {i}. {s}")

    print("\nSuccess criteria (how you will know it works)")
    for c in sheet.success_criteria:
        print(f"  - {c}")

    print("\n" + "-" * width)
    if sheet.is_complete():
        print("Validation: sheet COMPLETE — usable by a project team.")
    else:
        print("Validation: sheet INCOMPLETE.")
        for m in sheet.missing_fields():
            print(f"  ! missing: {m}")


LOCAL_AUTHORITY_CASE = ScopingSheet(
    project_name="Internal HR and administrative assistant",
    organisation="Town of Val-sur-Loire (25,000 inhabitants)",
    perimeter=(
        "Help staff find an HR or administrative procedure without going to the "
        "HR department for every recurring question."
    ),
    users=["Staff", "Managers", "HR department"],
    typical_questions=[
        "How many days of remote work are allowed per week?",
        "What is the notice period for requesting exceptional leave?",
        "Which procedure applies for reporting sick leave?",
    ],
    ranked_sources=[
        "Internal regulations (the binding reference)",
        "Leave and remote-work guides (approved procedures)",
        "Service notes (occasional, to be dated)",
        "Works council minutes (context, not binding)",
    ],
    success_criteria=[
        "80% of recurring HR questions answered without escalation",
        "Every answer cites its source and its date",
        "No answer based on an expired service note",
    ],
)

SME_CASE = ScopingSheet(
    project_name="Document assistant for technical support",
    organisation="MecaTech (industrial SME, 120 employees)",
    perimeter=(
        "Let technicians and sales staff quickly find reliable product "
        "information instead of calling an expert."
    ),
    users=["Technicians", "Support / after-sales", "Sales"],
    typical_questions=[
        "What is the maximum pressure of the MX-200 model?",
        "What is the recommended tightening torque for the MX-200 model?",
        "Which procedure applies after a motor failure?",
    ],
    ranked_sources=[
        "Technical manuals (the product reference)",
        "Quality procedures and ISO standards (the binding framework)",
        "Product sheets (commercial)",
        "After-sales reports and internal FAQs (field experience)",
    ],
    success_criteria=[
        "A correct technical answer on 90% of the active references",
        "Always the right version of the manual, never an obsolete model",
        "Search time divided by three for the support team",
    ],
)


HR_CONSULTANCY_CASE = ScopingSheet(
    project_name="Multi-client HR assistant for payroll managers",
    organisation="PaiePro Conseil (HR and outsourced payroll consultancy)",
    perimeter=(
        "Help the managers answer their clients quickly and correctly, when each "
        "client has its own collective agreement, its own company agreements and "
        "its own payroll rules. Keeping the clients separated is an absolute "
        "requirement."
    ),
    users=["Payroll managers", "HR consultants", "Client account managers"],
    typical_questions=[
        "Which collective agreement applies to the client Dupont SAS?",
        "What is the seniority bonus rate set by the agreement of the client Martin?",
        "How is the end-of-contract payment calculated for this client?",
    ],
    ranked_sources=[
        "Collective agreements per client (binding reference, kept separate)",
        "Company agreements and amendments per client (kept separate)",
        "Payroll scales and social-security notes (the common legal framework)",
        "The consultancy's internal procedures (working method)",
        "FAQs and the history of client tickets (field experience)",
    ],
    success_criteria=[
        "No information leaks from one client to another (strict separation)",
        "The agreement cited always belongs to the right client",
        "Reduced response time on recurring client questions",
    ],
)


def main() -> None:
    print("Lab 5-1 — Scoping a RAG project on one page\n")
    print("Three use cases are shown. Adapt the sheet to your own context afterwards.\n")

    show_sheet(LOCAL_AUTHORITY_CASE)
    print("\n")
    show_sheet(SME_CASE)
    print("\n")
    show_sheet(HR_CONSULTANCY_CASE)

    print("\n" + "=" * 78)
    print("WHAT TO REMEMBER")
    print("=" * 78)
    print("- A scoping sheet makes a vague need measurable and open to discussion.")
    print("- Ranking the sources is already a business decision, before any technique.")
    print("- With no success criterion, you will never know whether the RAG works.")


if __name__ == "__main__":
    main()
