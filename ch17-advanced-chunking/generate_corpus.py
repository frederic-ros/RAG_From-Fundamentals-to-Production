# -*- coding: utf-8 -*-
"""
generate_corpus.py — test corpus for Chapter 17 (advanced chunking).

The examples are the ones used in the chapter itself, so that the labs stay
close to the text:

  motor_M18_manual.md — Julien's maintenance manual. It holds the critical
      sentence "...inspected every 100 hours...", the one a fixed-size cut
      breaks in two. In Markdown (# and ## headings) for structural chunking.

  inspection_report.txt — raw text with NO structure: three subjects one after
      the other (pump P-42, motor M-18, storage tank). Used for semantic
      chunking: similarity drops at each change of subject.

  hr_agreement.txt — an extract from a company agreement (Claire): a rule, its
      exception, then another article. Used by the chunking agent and by
      semi-supervised chunking, where rule and exception are inseparable.

  long_manual.md — a longer, mostly off-topic document, holding one isolated
      fact (a screw reference) and one dispersed context (P-42 on line L-5).
      Used to contrast Late Chunking with Contextual Retrieval.

Note on the wording: the critical sentence of the M-18 manual is calibrated so
that a 50-character cut falls inside "100 hours". Lab 17-1 rests entirely on
that. Do not reword it without re-checking the lab.

Deterministic. Run before the labs: python generate_corpus.py
"""

from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent / "corpus"


MOTOR_M18_MANUAL = """\
# Maintenance of the M-18 motor

This manual gathers the operating and servicing instructions for the equipment installed on line L-5. It is intended for the maintenance teams and is updated at each revision.

## Inspection frequency
The M-18 drive motor must be inspected every 100 hours in cruising mode. This instruction is critical for the P-42 pump it drives. Any overrun exposes the bearings to premature wear.

## Start-up procedure
Check the oil level before any start-up. Run the motor unloaded for five minutes. Check that there is no abnormal vibration before applying load.

## Safety instructions
Wear personal protective equipment. Isolate the electrical installation before any work on the motor.
"""

INSPECTION_REPORT = """\
The P-42 pump was inspected yesterday morning. The P-42 pump shows no major defect on its body. The flow rate of the P-42 pump remains within specification. \
The M-18 motor shows signs of wear on its bearings. The M-18 motor must be replaced within thirty days. An order of parts for the M-18 motor has been placed. \
The storage tank will be inspected next week. The internal corrosion of the storage tank will be measured by ultrasound. The storage tank had been drained last month.
"""

HR_AGREEMENT = """\
Article 5: Employees may take two days of remote work per week. The request is made through the internal leave management tool. \
Exception: during peaks of activity, this entitlement is temporarily suspended. An internal note will be published to announce it to the teams concerned. \
Article 6: Leave must be requested with a minimum of fifteen working days' notice. The employer has seven days to answer the request.
"""

LONG_MANUAL = """\
# H-300 hydraulic power unit

## General presentation
The H-300 hydraulic power unit supplies several machines in the workshop. It was installed during the refurbishment of the line. It works on a closed pressurised circuit. The general documentation describes its history and its place in the plant.

## Context of use
The P-42 pump is used on production line L-5. It transfers the fluid to the packaging stations. Line L-5 runs on three shifts. The operators take over from one another to keep production continuous.

## Preventive maintenance
The filters must be cleaned every week. The M-18 motor must be inspected every 100 hours to protect the P-42 pump. The oil level is checked daily. A reading is entered in the maintenance log.

## Spare parts
The casing fixing screw carries the reference VF-2207. The sealing O-ring carries the reference JT-118. These parts are held in the central store. The lead time for resupply is two weeks.
"""


def main() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "motor_M18_manual.md").write_text(MOTOR_M18_MANUAL, encoding="utf-8")
    (BASE / "inspection_report.txt").write_text(INSPECTION_REPORT, encoding="utf-8")
    (BASE / "hr_agreement.txt").write_text(HR_AGREEMENT, encoding="utf-8")
    (BASE / "long_manual.md").write_text(LONG_MANUAL, encoding="utf-8")

    print("Chapter 17 corpus generated in:", BASE)
    print("  - motor_M18_manual.md   (Markdown: structural)")
    print("  - inspection_report.txt (raw text: semantic)")
    print("  - hr_agreement.txt      (rule + exception: agent / semi-supervised)")
    print("  - long_manual.md        (isolated fact + dispersed context: Late vs Contextual)")
    print("\nKey point: the sentence \"inspected every 100 hours\" in the M-18 manual")
    print("is the one a fixed-size cut breaks in two.")


if __name__ == "__main__":
    main()
