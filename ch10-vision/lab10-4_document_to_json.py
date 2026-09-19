# -*- coding: utf-8 -*-
"""
Lab 10-4 — From the visual document to the JSON document (convergence)

Learning objective
------------------
Understand that multimodal documents must converge on the SAME canonical
structure as the textual documents of earlier chapters. The outputs of the
previous labs are assembled — OCR text from the scan, the scene description of
the plan, the chart descriptions — into a single JSON document: title, sections,
figure descriptions, metadata. For the rest of the pipeline it is
indistinguishable from a JSON produced by a Word file.

No API key. Reuses the outputs of Labs 10-1, 10-2 and 10-3, regenerating them if
needed. Run generate_sample_docs.py first.
"""

import importlib.util
import json
from pathlib import Path
from typing import Dict

DOCS = Path(__file__).resolve().parent / "sample_docs"


def _load_module(file_name: str):
    path = Path(__file__).resolve().parent / file_name
    spec = importlib.util.spec_from_file_location(file_name.replace("-", "_")[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_documentary_json() -> Dict:
    """Make the three visual sources converge on one canonical JSON."""
    doc = {
        "title": "Line 4 file — maintenance and supervision",
        "type": "multimodal document",
        "sections": [],
        "figures": [],
        "metadata": {"origin": "visual documents", "chain": "Vision-RAG"},
    }

    # 1. The clean scan -> a text section, through the OCR of Lab 10-1.
    lab1 = _load_module("lab10-1_ocr_how_far.py")
    scan_text = lab1.run_ocr("clean_scan.png")
    doc["sections"].append({
        "title": "Maintenance note (scan)",
        "text": scan_text.replace("\n", " "),
        "source": "clean_scan.png",
        "method": "OCR",
    })

    # 2. The electrical plan -> a described figure, through the vision of Lab 10-2.
    lab2 = _load_module("lab10-2_image_becomes_scene.py")
    scene = lab2.vision_offline(DOCS / "electrical_plan.png")
    doc["figures"].append({
        "title": "Line 4 electrical plan",
        "type": "drawing",
        "description": scene["description"],
        "components": scene["components"],
        "connections": scene["connections"],
        "source": "electrical_plan.png",
        "method": "vision",
    })

    # 3. The chart -> a described figure, through the analysis of Lab 10-3.
    lab3 = _load_module("lab10-3_chart_paradox.py")
    analysis = lab3.analyze_offline()
    doc["figures"].append({
        "title": "Motor M1 temperature",
        "type": "chart",
        "description": " ".join(analysis["descriptions"]),
        "peak": analysis["peak"],
        "threshold_crossings": analysis["threshold_crossings"],
        "source": "temperature_chart.png",
        "method": "vision",
    })

    return doc


def main() -> None:
    print("=" * 78)
    print("Lab 10-4 — From the visual document to the JSON document (convergence)")
    print("=" * 78)

    if not DOCS.exists():
        print("\nImages not found. Run this first: python generate_sample_docs.py")
        return

    doc = build_documentary_json()

    print(f"\nTitle: {doc['title']}")
    print(f"Text sections: {len(doc['sections'])}")
    print(f"Figures described: {len(doc['figures'])}")

    print("\n--- Sections ---")
    for s in doc["sections"]:
        print(f"  - [{s['method']}] {s['title']} ({s['source']})")
        print(f"    {s['text'][:80]}…")

    print("\n--- Figures ---")
    for f in doc["figures"]:
        print(f"  - [{f['method']}] {f['title']} — {f['type']} ({f['source']})")
        print(f"    {f['description'][:80]}…")

    out = DOCS / "multimodal_document.json"
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON document written: {out.name}")

    print("\n" + "=" * 78)
    print("THE CONVERGENCE")
    print("=" * 78)
    print("A scan (OCR), a plan and a chart (vision) all end at the SAME JSON document")
    print("as one from a Word or an Excel file. The visual is not a parallel chain: it")
    print("is another door into the canonical structure.")

    print("\nWHAT TO REMEMBER")
    print("- Extracted text and visual descriptions live together in one structure.")
    print("- The rest of the pipeline — fragments, embeddings — no longer sees the format.")
    print("- This is the coherence of the whole book: everything converges on the JSON document.")


if __name__ == "__main__":
    main()
