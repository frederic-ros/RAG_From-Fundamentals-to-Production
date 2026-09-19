# -*- coding: utf-8 -*-
"""
Lab 6-4 — Julien's challenge: multimodal parsing by vision (VLM)

Learning objective
------------------
Turn a non-textual source — here an equipment nameplate — into a textual,
structured fragment of knowledge (JSON), using a vision-language model. This is
Level 4 parsing.

Three modes, from the simplest to the most committed. The script chooses
automatically:

  1. OFFLINE (the default): a simulated, deterministic VLM. Nothing to install,
     no key. The pipeline runs anywhere, and shows the shape of the result.
  2. LOCAL (Ollama): a real local vision model, free (llava, moondream, and so
     on). Activated if Ollama answers on localhost. No data leaves the machine.
  3. API (cloud): a compatible provider, activated if the VLM_API_KEY
     environment variable is set. Optional.

To force a mode: set the environment variable LAB_MODE to offline, local or api.

Requires Pillow. For local mode: Ollama installed with a vision model.
Run generate_sample_docs.py first.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Optional

DOCS = Path(__file__).resolve().parent / "sample_docs"
IMAGE = DOCS / "julien_nameplate.png"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_VLM", "llava")

SYSTEM_PROMPT = (
    "You are a specialised document parser. From the image of an industrial "
    "equipment nameplate, extract the technical information as a strict JSON "
    "object with the keys: equipment_type, reference, serial_number, parameters "
    "(a key/value object), conformity (a list), description (a short text). "
    "Answer with the JSON alone, with no commentary."
)


# ---------------------------------------------------------------------------
# Mode 1 — a simulated, deterministic VLM (offline)
# ---------------------------------------------------------------------------
def vlm_offline(_image: Path) -> Dict:
    """A hard-coded, realistic answer matching the image that was generated.

    It lets the whole pipeline run with no external dependency. The content
    corresponds to the nameplate produced by generate_sample_docs.py.
    """
    return {
        "equipment_type": "Industrial compressor",
        "reference": "MX-200-400V",
        "serial_number": "MT2025-018342",
        "parameters": {
            "max_pressure_bar": "12.5",
            "flow_m3_h": "180",
            "voltage_v": "400 (three-phase)",
            "power_kw": "15",
            "year": "2025",
        },
        "conformity": ["CE", "ISO 1217"],
        "description": (
            "Nameplate of the MecaTech MX-200 compressor, 400 V three-phase, "
            "maximum pressure 12.5 bar, flow 180 m3/h."
        ),
    }


# ---------------------------------------------------------------------------
# Mode 2 — a local Ollama (a real VLM, free)
# ---------------------------------------------------------------------------
def ollama_available() -> bool:
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def vlm_local(image: Path) -> Optional[Dict]:
    """Query a local vision model through Ollama."""
    image_b64 = base64.b64encode(image.read_bytes()).decode("ascii")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": SYSTEM_PROMPT,
        "images": [image_b64],
        "stream": False,
        "format": "json",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = json.loads(r.read().decode("utf-8"))
        return json.loads(raw.get("response", "{}"))
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
        print(f"  (local mode unavailable: {e})")
        return None


# ---------------------------------------------------------------------------
# Mode 3 — a cloud API (optional)
# ---------------------------------------------------------------------------
def api_available() -> bool:
    return bool(os.environ.get("VLM_API_KEY"))


def vlm_api(_image: Path) -> Optional[Dict]:
    """An extension point for a compatible cloud provider.

    No provider is hard-coded here, deliberately: the offers and the formats
    change. Plug in the call of your choice, reading the key from VLM_API_KEY.
    With no implementation, None is returned.
    """
    print("  (API mode: plug your provider in here; not implemented by default)")
    return None


# ---------------------------------------------------------------------------
# Choosing the mode
# ---------------------------------------------------------------------------
def choose_mode() -> str:
    force = os.environ.get("LAB_MODE", "").lower()
    if force in {"offline", "local", "api"}:
        return force
    if ollama_available():
        return "local"
    if api_available():
        return "api"
    return "offline"


def parse_image(image: Path) -> Dict:
    mode = choose_mode()
    print(f"VLM mode selected: {mode}")

    result: Optional[Dict] = None
    if mode == "local":
        result = vlm_local(image)
    elif mode == "api":
        result = vlm_api(image)

    if result is None:
        if mode != "offline":
            print("  falling back automatically to offline mode.")
        result = vlm_offline(image)

    return result


def main() -> None:
    print("=" * 78)
    print("Lab 6-4 — Multimodal parsing by vision (Julien)")
    print("=" * 78)

    if not IMAGE.exists():
        print("\nImage not found. Run this first: python generate_sample_docs.py")
        return

    print(f"\nImage analysed: {IMAGE.name}")
    print("\nThe parsing system prompt:")
    print("  " + SYSTEM_PROMPT[:120] + "...")

    print()
    pivot = parse_image(IMAGE)

    print("\n--- The document JSON produced ---")
    print(json.dumps(pivot, ensure_ascii=False, indent=2))

    out = DOCS / "pivot_nameplate.json"
    out.write_text(json.dumps(pivot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out.name}")

    # A minimal completeness check.
    expected_keys = {"equipment_type", "reference", "parameters", "description"}
    missing = expected_keys - set(pivot)
    print(f"Completeness: {'OK' if not missing else 'missing ' + ', '.join(missing)}")

    print("\nWHAT TO REMEMBER")
    print("- A VLM turns a purely visual component into an indexable fragment.")
    print("- The prompt imposes a JSON schema: the output becomes usable by the RAG.")
    print("- The same pipeline runs offline, locally through Ollama, or through an API:")
    print("  you can learn without paying anything, then plug in a real model.")


if __name__ == "__main__":
    main()
