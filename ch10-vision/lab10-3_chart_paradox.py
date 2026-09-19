# -*- coding: utf-8 -*-
"""
Lab 10-3 — The paradox of the chart (Julien)

Learning objective
------------------
Discover that an important piece of information can be present in a document
without ever being written explicitly. A chart holds LESS text than a paragraph,
but carries MORE information: its meaning is in the shapes — the slope, the
peak, the gap — not in its few characters. The chart is turned into textual
descriptions (trends, peaks, threshold crossings) that a semantic search can
work with.

Hybrid mode:

  1. OFFLINE (the default): a deterministic analysis of the curve, from the
     known data.
  2. LOCAL (Ollama): a vision model describes the chart.

To force a mode: set LAB_MODE to offline or local.

No API key. Run generate_sample_docs.py first.
"""

import base64
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

DOCS = Path(__file__).resolve().parent / "sample_docs"
IMAGE = DOCS / "temperature_chart.png"

OLLAMA_TAGS = "http://localhost:11434/api/tags"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_VLM = os.environ.get("OLLAMA_VLM", "llava")

# The curve data: the same values used to generate the image.
HOURS = [8, 9, 10, 11, 12, 13, 14, 15, 16]
TEMPERATURES = [42, 48, 55, 63, 72, 80, 78, 70, 60]
THRESHOLD = 75


# ---------------------------------------------------------------------------
# Offline mode — a deterministic analysis of the curve's shape
# ---------------------------------------------------------------------------
def analyze_offline() -> Dict:
    peak = max(TEMPERATURES)
    peak_hour = HOURS[TEMPERATURES.index(peak)]
    start, end = TEMPERATURES[0], TEMPERATURES[-1]
    trend = "rising then falling" if peak not in (start, end) else "monotonic"
    # The threshold crossings.
    above = [HOURS[i] for i, v in enumerate(TEMPERATURES) if v > THRESHOLD]
    descriptions = [
        f"The temperature is broadly {trend} across the day.",
        f"It starts at {start} C at {HOURS[0]}:00 and reaches a peak of {peak} C "
        f"at {peak_hour}:00.",
        f"It then falls back to {end} C by {HOURS[-1]}:00.",
    ]
    if above:
        descriptions.append(
            f"It crosses the {THRESHOLD} C threshold between {min(above)}:00 "
            f"and {max(above)}:00.")
    return {
        "document_type": "temperature chart (motor M1)",
        "peak": {"value": peak, "hour": peak_hour},
        "trend": trend,
        "threshold_crossings": above,
        "descriptions": descriptions,
    }


# ---------------------------------------------------------------------------
# Mode local — Ollama (llava)
# ---------------------------------------------------------------------------
def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def analyze_local(image: Path) -> Optional[Dict]:
    prompt = (
        "Analyse this chart. Give a JSON object with: trend (text), peak "
        "({value, hour}), and descriptions (a list of sentences describing the "
        "curve, the peaks and the threshold crossings). JSON only."
    )
    image_b64 = base64.b64encode(image.read_bytes()).decode("ascii")
    payload = {"model": OLLAMA_VLM, "prompt": prompt, "images": [image_b64],
               "stream": False, "format": "json"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = json.loads(r.read().decode("utf-8"))
        return json.loads(raw.get("response", "{}"))
    except Exception as e:
        print(f"  (local mode unavailable: {e})")
        return None


def choose_mode() -> str:
    force = os.environ.get("LAB_MODE", "").lower()
    if force in {"offline", "local"}:
        return force
    return "local" if ollama_available() else "offline"


def analyze(image: Path) -> Dict:
    mode = choose_mode()
    print(f"Analysis mode: {mode}")
    if mode == "local":
        res = analyze_local(image)
        if res is not None:
            return res
        print("  falling back to offline mode.")
    return analyze_offline()


def compare_ocr_vs_vision(descriptions: List[str]) -> None:
    # What an OCR recovers from the chart: axis numbers, without the meaning.
    ocr_text = "80 75 70 65 60 55 50 45 Hour Temperature"
    print("\n--- What the OCR recovers (the labels) ---")
    print(f"  \"{ocr_text}\"")
    print("  -> no trend, no peak: just isolated numbers.")
    print("\n--- What the vision produces (the meaning) ---")
    for d in descriptions:
        print(f"  - {d}")


def main() -> None:
    print("=" * 78)
    print("Lab 10-3 — The paradox of the chart (Julien)")
    print("=" * 78)

    if not IMAGE.exists():
        print("\nImage not found. Run this first: python generate_sample_docs.py")
        return

    print(f"\nImage analysed: {IMAGE.name}")
    analysis = analyze(IMAGE)

    compare_ocr_vs_vision(analysis.get("descriptions", []))

    out = DOCS / "chart_descriptions.json"
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out.name}")

    print("\n" + "=" * 78)
    print("THE PARADOX")
    print("=" * 78)
    print("The chart holds less text than a paragraph, but more information. Its")
    print("meaning is not in its words but in its shapes: the slope, the height of")
    print("the peak, the gap to the threshold. Extracting its characters means")
    print("keeping the label and throwing away the content.")

    print("\nWHAT TO REMEMBER")
    print("- A key piece of information may be written nowhere: it is in the shape.")
    print("- Vision verbalises trends, peaks and thresholds into indexable sentences.")
    print("- Those sentences enter the map of meaning: the chart becomes findable.")


if __name__ == "__main__":
    main()
