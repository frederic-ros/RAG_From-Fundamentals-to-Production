# -*- coding: utf-8 -*-
"""
generate_sample_data.py — the test data of Chapter 9.

Three businesses, three tables — the "three grids" of the chapter:

    Julien (industry): data/Maintenance_Batteries.xlsx
        Sheets: Batteries (equipment, voltage, status, ...) and Interventions.
        Used for the calculations and for Table-RAG: joins, aggregations.

    Sophie (local authority): data/road_budget.csv
        The budget by line item and by year. One row per spending item, one
        COLUMN per financial year (2024, 2025, 2026). Ideal for illustrating
        the "chunk by column" and verbalisation.

    Claire (HR): data/hr_leave.csv
        Leave entitlement by member of staff. One row is one staff record:
        department, leave, length of service.

A NOTE ON THE WORKBOOK. In the French edition, Maintenance_Batteries.xlsx was
assumed to be already present in data/, and was not shipped with the labs. It
was in fact absent, which left Labs 9-1, 9-4, 9-5 and 9-6 inert: each printed
"file not found" and exited cleanly, so nothing failed and nothing ran. The
workbook is now BUILT here, deterministically, so that the six labs work from a
clean checkout.

The figures are wired to the exercises and should not be edited casually:

  - BAT002 is the ONLY equipment at 11.4 V. Lab 9-1 asks which equipment runs at
    11.4 volts, and needs that answer to be unique.
  - Two units are "To replace" and two are "Critical", which Lab 9-4 counts.
  - Three sites, so the GROUP BY of Lab 9-4 returns something worth reading.
  - Eight columns, because Lab 9-1 and Lab 9-5 cut the flattened values into
    chunks of five: the misalignment against the row width is what breaks the
    row-by-column relation, and the demonstration needs it.
  - The average voltage is 11.82 and the maximum temperature 45.3, both checked
    by the benchmark of Lab 9-5. BAT005 and BAT008 carry the "Shutdown and
    replacement" action, and BAT003 sits in the Assembly workshop; Lab 9-5 asks
    about all three.

Everything is deterministic and reproducible.
Run before the labs: python generate_sample_data.py

Dependencies: openpyxl (for the workbook).
"""

import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
DATA.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Julien — the battery maintenance workbook
# ---------------------------------------------------------------------------
BATTERIES = [
    ["Equipment", "Site", "Workshop", "Voltage_V", "Temperature_C",
     "Capacity_Ah", "Status", "Action"],
    ["BAT001", "Northfield", "Machining", 12.6, 22.5, 100, "OK", "None"],
    ["BAT002", "Northfield", "Assembly", 11.4, 31.2, 100, "To replace",
     "Order a replacement"],
    ["BAT003", "Northfield", "Assembly", 12.4, 24.0, 80, "OK", "None"],
    ["BAT004", "Eastgate", "Finishing", 12.1, 28.7, 120, "Monitor",
     "Inspect next quarter"],
    ["BAT005", "Eastgate", "Machining", 10.9, 38.4, 120, "Critical",
     "Shutdown and replacement"],
    ["BAT006", "Eastgate", "Finishing", 12.7, 21.8, 100, "OK", "None"],
    ["BAT007", "Southbank", "Assembly", 11.8, 29.3, 80, "Monitor",
     "Inspect next quarter"],
    ["BAT008", "Southbank", "Machining", 10.6, 45.3, 80, "Critical",
     "Shutdown and replacement"],
    ["BAT009", "Southbank", "Finishing", 12.5, 23.4, 100, "OK", "None"],
    ["BAT010", "Northfield", "Machining", 11.2, 30.8, 120, "To replace",
     "Order a replacement"],
]


INTERVENTIONS = [
    ["Ticket", "Equipment", "Date", "Type", "Duration_h", "Technician"],
    ["INT-2025-001", "BAT002", "2025-01-14", "Inspection", 1.5, "J. Bauer"],
    ["INT-2025-002", "BAT005", "2025-01-22", "Replacement", 3.0, "M. Doyle"],
    ["INT-2025-003", "BAT008", "2025-02-03", "Inspection", 1.0, "J. Bauer"],
    ["INT-2025-004", "BAT002", "2025-02-18", "Repair", 2.5, "M. Doyle"],
    ["INT-2025-005", "BAT010", "2025-03-05", "Inspection", 1.5, "A. Whitfield"],
    ["INT-2025-006", "BAT005", "2025-03-19", "Inspection", 1.0, "J. Bauer"],
    ["INT-2025-007", "BAT004", "2025-04-02", "Calibration", 2.0, "A. Whitfield"],
    ["INT-2025-008", "BAT008", "2025-04-16", "Repair", 4.0, "M. Doyle"],
]


# ---------------------------------------------------------------------------
# Sophie — the road budget: rows are line items, columns are financial years
# ---------------------------------------------------------------------------
ROAD_BUDGET = [
    ["Item", "Budget_2024_k", "Budget_2025_k", "Budget_2026_k"],
    ["Roadway", "120", "135", "150"],
    ["Street lighting", "60", "62", "70"],
    ["Green spaces", "45", "48", "52"],
    ["Signage", "20", "22", "25"],
    ["Street furniture", "15", "18", "20"],
]


# ---------------------------------------------------------------------------
# Claire — HR leave: one row is one staff record
# ---------------------------------------------------------------------------
HR_LEAVE = [
    ["Staff", "Department", "Leave_days", "Service_years", "Training_days"],
    ["Alice", "HR", "25", "6", "3"],
    ["Bruno", "Finance", "28", "12", "5"],
    ["Chloe", "Technical", "27", "9", "4"],
    ["David", "HR", "32", "15", "2"],
    ["Emma", "Technical", "30", "11", "6"],
    ["Farid", "Finance", "26", "7", "3"],
]


def write_csv(name: str, rows) -> None:
    path = DATA / name
    with open(path, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(rows)
    print(f"  + {name}")


def write_xlsx(name: str) -> None:
    """Build Julien's workbook: two sheets, no formatting, plain values."""
    try:
        from openpyxl import Workbook
    except ImportError:
        print(f"  ! {name} not built: openpyxl is missing (pip install openpyxl)")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Batteries"
    for row in BATTERIES:
        ws.append(row)

    ws2 = wb.create_sheet("Interventions")
    for row in INTERVENTIONS:
        ws2.append(row)

    wb.save(DATA / name)
    print(f"  + {name}")


def main() -> None:
    print("Generating the Chapter 9 test data:")
    write_xlsx("Maintenance_Batteries.xlsx")
    write_csv("road_budget.csv", ROAD_BUDGET)
    write_csv("hr_leave.csv", HR_LEAVE)
    print(f"\nDone. Data available in: {DATA}")


if __name__ == "__main__":
    main()
