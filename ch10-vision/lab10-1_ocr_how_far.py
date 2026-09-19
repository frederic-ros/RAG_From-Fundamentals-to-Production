# -*- coding: utf-8 -*-
"""
Lab 10-1 — How far can OCR go? (Julien, Sophie)

Learning objective
------------------
Understand that not every document needs a vision model, and learn to spot the
frontier between OCR and visual understanding. Three documents are passed
through the same OCR:

    clean_scan.png        — plain text: OCR is enough.
    electrical_plan.png   — the meaning is in the arrangement: OCR fails.
    temperature_chart.png — the meaning is in the shape: OCR misses the point.

OCR recognises CHARACTERS, not STRUCTURE. For a simple page it is sufficient;
for a visual page, you have to change tool.

Hybrid mode: if tesseract is installed, a real OCR runs; otherwise a
deterministic simulated OCR produces the same kind of result. No API key.
Run generate_sample_docs.py first.
"""

import importlib.util
from pathlib import Path
from typing import Dict

DOCS = Path(__file__).resolve().parent / "sample_docs"

# The deterministic simulated OCR, the fallback when tesseract is absent: what an
# OCR "sees". Note how little survives of the plan and of the chart.
SIMULATED_OCR = {
    "clean_scan.png": (
        "MAINTENANCE NOTE\nReference: NOTE-2026-014\nDate: 2026-01-15\n"
        "Battery BAT005 on line 4 is critical.\nMeasured voltage: 10.9 V.\n"
        "Action: immediate replacement required.\nTechnician: Nguyen."
    ),
    "electrical_plan.png": "ELECTRICAL PLAN - LINE 4 T1 A4 V2 M1 12",
    "temperature_chart.png": (
        "Motor M1 temperature the day of 2026-01-15 80 75 70 65 60 55 50 45 Hour"
    ),
}


def ocr_available() -> bool:
    if importlib.util.find_spec("pytesseract") is None:
        return False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def run_ocr(image_name: str) -> str:
    """Run a real OCR where possible, otherwise return the simulated one."""
    if ocr_available():
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(DOCS / image_name)).strip()
    return SIMULATED_OCR.get(image_name, "")


# For each image: what the OCR would have to give up to allow an answer, and
# what it misses.
CASES = [
    {
        "image": "clean_scan.png",
        "type": "plain scanned text",
        "question": "What voltage was measured?",
        "expected_answer": "10.9",
        "expected_verdict": "OCR is enough",
    },
    {
        "image": "electrical_plan.png",
        "type": "plan / technical drawing",
        "question": "What is the temperature sensor wired to?",
        "expected_answer": "V2",  # the meaning is in the connections, not the text
        "expected_verdict": "vision required",
    },
    {
        "image": "temperature_chart.png",
        "type": "chart",
        "question": "Is there a temperature peak, and at what value?",
        "expected_answer": "80",  # the trend and peak are not in the OCR text
        "expected_verdict": "vision required",
    },
]


def evaluate(ocr_text: str, case: Dict) -> Dict:
    """Does OCR alone allow the question to be answered?

    The presence of the right token IS NOT ENOUGH: the OCR has to give the
    information back in a form that ANSWERS the question. On a chart, seeing
    "80" on an axis does not say that it is a peak; on a plan, seeing "V2" does
    not say that a sensor is wired to it. So beyond the token we also require the
    marks of interpretation — words of trend, of connection — that the OCR does
    not produce.
    """
    token_present = case["expected_answer"] in ocr_text
    t = ocr_text.lower()
    if case["image"] == "clean_scan.png":
        # Plain text: the token inside a sentence really is enough.
        answers = token_present
    elif case["image"] == "temperature_chart.png":
        # A notion of peak or trend would be needed, and is absent from the OCR.
        answers = token_present and ("peak" in t or "trend" in t or "maximum" in t)
    else:  # the plan
        # A notion of wiring or connection would be needed, and is absent.
        answers = token_present and ("sensor" in t or "wired" in t or "connect" in t)
    return {
        "ocr_answers": answers,
        "verdict": "OCR is enough" if answers else "vision required",
    }


def main() -> None:
    print("=" * 78)
    print("Lab 10-1 — How far can OCR go?")
    print("=" * 78)

    if not DOCS.exists():
        print("\nImages not found. Run this first: python generate_sample_docs.py")
        return

    real = ocr_available()
    print(f"\nOCR: {'tesseract (real)' if real else 'simulated (deterministic)'}")

    results = []
    for case in CASES:
        text = run_ocr(case["image"])
        ev = evaluate(text, case)
        results.append((case, text, ev))

        print("\n" + "=" * 78)
        print(f"DOCUMENT: {case['image']}  ({case['type']})")
        print("=" * 78)
        preview = text.replace("\n", " / ")[:120]
        print(f"OCR text: {preview}…")
        print(f"Question: {case['question']}")
        print(f"  expected answer: {case['expected_answer']}")
        print(f"  does OCR allow an answer? {'YES' if ev['ocr_answers'] else 'NO'}")
        print(f"  verdict: {ev['verdict']}")

    print("\n" + "=" * 78)
    print("THE SUMMARY TABLE: WHERE OCR STOPS")
    print("=" * 78)
    print(f"{'Document':28s} | {'Type':26s} | verdict")
    print("-" * 78)
    for case, _, ev in results:
        print(f"{case['image']:28s} | {case['type']:26s} | {ev['verdict']}")

    print("\nWHAT TO REMEMBER")
    print("- OCR recognises characters, not structure and not shapes.")
    print("- For plain scanned text it is enough: no need to reach for a vision model.")
    print("- For a plan or a chart it misses the point: that is where the frontier lies.")


if __name__ == "__main__":
    main()
