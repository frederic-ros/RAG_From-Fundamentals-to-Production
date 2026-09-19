# -*- coding: utf-8 -*-
"""
Lab 5-4 — Creating a business evaluation set

Learning objective
------------------
Build the "thermometer" before starting to optimise the system. This script
models an evaluation set (question -> expected answer -> source document),
checks its quality (duplicates, orphan sources, coverage), and then simulates a
measurement of recall and precision from the documents a retrieval would have
returned.

The aim is not to evaluate a real model, but to understand HOW you measure:

  - recall    : among the good sources expected, how many were found;
  - precision : among the sources found, how many were relevant;
  - coverage  : what share of the document estate the test set interrogates.

The lab runs with no API key and no external dependency.
"""

from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class TestCase:
    """One test case: a question, its expected answer, its reference source."""

    question: str
    expected_answer: str
    reference_source: str
    # The sources a retrieval actually returned (simulated).
    retrieved_sources: List[str] = field(default_factory=list)

    def recall(self) -> float:
        """1.0 if the reference source was found, 0.0 otherwise."""
        return 1.0 if self.reference_source in self.retrieved_sources else 0.0

    def precision(self) -> float:
        """The share of returned sources that match the reference."""
        if not self.retrieved_sources:
            return 0.0
        relevant = sum(1 for s in self.retrieved_sources if s == self.reference_source)
        return relevant / len(self.retrieved_sources)


def quality_checks(cases: List[TestCase]) -> List[str]:
    """Check the coherence of the evaluation set before measuring anything."""
    alerts: List[str] = []

    questions = [c.question.strip().lower() for c in cases]
    duplicates = {q for q in questions if questions.count(q) > 1}
    if duplicates:
        alerts.append(f"{len(duplicates)} duplicated question(s)")

    for c in cases:
        if not c.expected_answer.strip():
            alerts.append(f"expected answer missing: \"{c.question}\"")
        if not c.reference_source.strip():
            alerts.append(f"reference source missing: \"{c.question}\"")

    if len(cases) < 20:
        alerts.append(f"set too small: {len(cases)} questions (aim for 20 to 50)")

    return alerts


def coverage(cases: List[TestCase], estate: Set[str]) -> float:
    """The share of the estate's documents actually interrogated by the test set."""
    if not estate:
        return 0.0
    interrogated = {c.reference_source for c in cases} & estate
    return len(interrogated) / len(estate)


def report(title: str, cases: List[TestCase], estate: Set[str]) -> None:
    width = 90
    print("=" * width)
    print(title)
    print("=" * width)

    print(f"{'Question':52s} | {'Expected source':22s} | recall | prec.")
    print("-" * width)
    for c in cases:
        print(
            f"{c.question[:52]:52s} | {c.reference_source[:22]:22s} | "
            f"{c.recall():.2f}   | {c.precision():.2f}"
        )

    n = len(cases)
    mean_recall = sum(c.recall() for c in cases) / n if n else 0.0
    mean_precision = sum(c.precision() for c in cases) / n if n else 0.0

    print("-" * width)
    print(f"Mean recall     : {mean_recall:.2%}")
    print(f"Mean precision  : {mean_precision:.2%}")
    print(f"Coverage        : {coverage(cases, estate):.2%} of the estate interrogated")

    alerts = quality_checks(cases)
    if alerts:
        print("\nQuality checks:")
        for a in alerts:
            print(f"  ! {a}")


# --- The evaluation set: a local authority (a representative extract) -------
LOCAL_AUTHORITY_ESTATE = {
    "Remote work guide", "Leave guide", "Internal regulations",
    "HR procedures", "Service notes",
}

LOCAL_AUTHORITY_CASES: List[TestCase] = [
    TestCase("How many days of remote work are allowed?",
             "Two days per week at most.", "Remote work guide",
             ["Remote work guide"]),
    TestCase("What notice is needed to request exceptional leave?",
             "At least 5 working days in advance.", "Leave guide",
             ["Leave guide", "Service notes"]),
    TestCase("How do I report sick leave?",
             "Send the certificate to HR within 48 hours.", "HR procedures",
             ["HR procedures"]),
    TestCase("What flexible hours are allowed?",
             "Core hours 9.30-11.30 and 14.00-16.00.", "Internal regulations",
             ["Internal regulations"]),
    TestCase("Can remote work be combined with part-time?",
             "Yes, pro rata to the days worked.", "Remote work guide",
             ["Leave guide"]),   # a faulty retrieval: recall = 0
]


# --- The evaluation set: a multi-client HR consultancy ----------------------
# Here the reference source includes the CLIENT: a good answer for the client
# Dupont must never rest on a document belonging to the client Martin.
HR_CONSULTANCY_ESTATE = {
    "Dupont SAS agreement", "Dupont SAS company deal", "Martin agreement",
    "Martin company deal", "Statutory payroll scale",
}

HR_CONSULTANCY_CASES: List[TestCase] = [
    TestCase("Which agreement applies to the client Dupont SAS?",
             "The Syntec collective agreement.", "Dupont SAS agreement",
             ["Dupont SAS agreement"]),
    TestCase("Seniority bonus rate at the client Martin?",
             "3% after 3 years, under the company deal.", "Martin company deal",
             ["Martin company deal"]),
    TestCase("Health cover ceiling for the client Dupont SAS?",
             "As set by the Dupont deal in force.", "Dupont SAS company deal",
             ["Dupont SAS company deal"]),
    TestCase("What is the reference employer contribution?",
             "As set by the statutory scale in force.", "Statutory payroll scale",
             ["Statutory payroll scale"]),
    # The critical case: the right source is the Martin deal, but the retrieval
    # brought back a document belonging to ANOTHER client, Dupont. Recall is 0,
    # AND it is a leak between clients.
    TestCase("End-of-contract payment for the client Martin?",
             "As set by the Martin deal in force.", "Martin company deal",
             ["Dupont SAS agreement"]),
]


def main() -> None:
    print("Lab 5-4 — Creating a business evaluation set\n")
    print("Teaching extracts of 5 cases per context. On a real project, aim for 20 to 50.\n")

    report("CASE A — a local authority: the town of Val-sur-Loire",
           LOCAL_AUTHORITY_CASES, LOCAL_AUTHORITY_ESTATE)

    print("\n")
    report("CASE C — a multi-client HR consultancy: PaiePro Conseil",
           HR_CONSULTANCY_CASES, HR_CONSULTANCY_ESTATE)

    print("\n" + "=" * 90)
    print("READING THE RESULTS")
    print("=" * 90)
    print("- Local authority: the 5th question shows a retrieval failure (recall 0),")
    print("  and the 2nd a partial precision, with one source too many.")
    print("- HR consultancy: the 5th question is graver still. The retrieval brings")
    print("  back a document of the client Dupont for a question about the client")
    print("  Martin: not only is recall zero, it is a LEAK between clients.")
    print("- The quality check flags that each set is too small (5 < 20).")

    print("\nWHAT TO REMEMBER")
    print("- You build the thermometer BEFORE optimising, never after.")
    print("- Recall and precision measure two different failures: missing, and returning noise.")
    print("- Coverage tells you whether the test set really interrogates the whole estate.")


if __name__ == "__main__":
    main()
