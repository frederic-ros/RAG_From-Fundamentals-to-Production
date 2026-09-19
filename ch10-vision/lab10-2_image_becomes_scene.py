# -*- coding: utf-8 -*-
"""
Lab 10-2 — When an image becomes a scene (Julien)

Learning objective
------------------
Understand that a multimodal model interprets spatial relations and objects, and
does not stop at reading text. Julien's electrical plan is submitted to a vision
model, which produces a structured description of it: components, connections,
markers. The information "what is the temperature sensor wired to?" — written
nowhere — finally becomes available.

Hybrid mode, as in Chapter 6:

  1. OFFLINE (the default): a deterministic simulated description, faithful to
     the generated plan.
  2. LOCAL (Ollama): a real vision model (llava) describes the image.

To force a mode: set LAB_MODE to offline or local.

No API key. Run generate_sample_docs.py first.
"""

import base64
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, Optional

DOCS = Path(__file__).resolve().parent / "sample_docs"
IMAGE = DOCS / "electrical_plan.png"

OLLAMA_TAGS = "http://localhost:11434/api/tags"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_VLM = os.environ.get("OLLAMA_VLM", "llava")

PROMPT = (
    "Describe this electrical plan as a JSON object with the keys: "
    "document_type, components (a list of {marker, role}), connections (a list "
    "of {from, to}), and description (text). Answer with the JSON alone."
)


# ---------------------------------------------------------------------------
# Offline mode — a deterministic description, faithful to the generated plan
# ---------------------------------------------------------------------------
def vision_offline(_image: Path) -> Dict:
    return {
        "document_type": "building electrical plan (line 4)",
        "components": [
            {"marker": "T1", "role": "main distribution board"},
            {"marker": "A4", "role": "cabinet"},
            {"marker": "V2", "role": "variable-speed drive"},
            {"marker": "M1", "role": "motor"},
            {"marker": "C", "role": "temperature sensor"},
        ],
        "connections": [
            {"from": "T1", "to": "A4"},
            {"from": "T1", "to": "V2"},
            {"from": "T1", "to": "M1"},
            {"from": "C", "to": "V2"},
        ],
        "description": (
            "Board T1 feeds cabinet A4, drive V2 and motor M1. A temperature "
            "sensor (C) is wired to drive V2."
        ),
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


def vision_local(image: Path) -> Optional[Dict]:
    image_b64 = base64.b64encode(image.read_bytes()).decode("ascii")
    payload = {"model": OLLAMA_VLM, "prompt": PROMPT, "images": [image_b64],
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


def describe(image: Path) -> Dict:
    mode = choose_mode()
    print(f"Vision mode: {mode}")
    if mode == "local":
        res = vision_local(image)
        if res is not None:
            return res
        print("  falling back to offline mode.")
    return vision_offline(image)


def answer_wiring(description: Dict) -> str:
    """Use the description to answer the question about the sensor."""
    for conn in description.get("connections", []):
        source = str(conn.get("from", "")).lower()
        if source == "c" or "sensor" in source:
            return conn.get("to", "?")
    # The fallback: search the text.
    text = description.get("description", "").lower()
    if "v2" in text and "sensor" in text:
        return "V2"
    return "undetermined"


def main() -> None:
    print("=" * 78)
    print("Lab 10-2 — When an image becomes a scene (Julien)")
    print("=" * 78)

    if not IMAGE.exists():
        print("\nImage not found. Run this first: python generate_sample_docs.py")
        return

    print(f"\nImage analysed: {IMAGE.name}")
    description = describe(IMAGE)

    print("\n--- The structured description, from the vision model ---")
    print(json.dumps(description, ensure_ascii=False, indent=2))

    out = DOCS / "plan_scene.json"
    out.write_text(json.dumps(description, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out.name}")

    print("\n" + "=" * 78)
    print("THE INFORMATION THAT WAS NEVER WRITTEN")
    print("=" * 78)
    print("Question: \"What is the temperature sensor wired to?\"")
    to = answer_wiring(description)
    print(f"Answer, from the interpreted scene: the sensor is wired to {to}.")
    print("This information appears nowhere in words: it is carried by the spatial")
    print("arrangement, which only a global reading gives back.")

    print("\nWHAT TO REMEMBER")
    print("- A vision model does not transcribe: it describes and interprets a scene.")
    print("- Components, connections and markers become usable JSON.")
    print("- A question with no written answer finds one at last in the visual structure.")


if __name__ == "__main__":
    main()
