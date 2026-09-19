# -*- coding: utf-8 -*-
"""
Lab 7-4 — The sparser in action: automatic correction (Claire)

Learning objective
------------------
Show that a Smart Parser does more than extract: it repairs. Telegraphic style
rewritten into full sentences, acronyms spelled out, metadata injected — status,
estimated date — and all of it on the fly, at ingestion time.

Two modes:

  1. OFFLINE (the default): correction by deterministic rules. Runs anywhere.
  2. LOCAL (Ollama): a real local LLM rewrites the fragment.

To force a mode: set LAB_MODE to offline or local.

A note on the acronyms. The French edition used TT, SIRH, N+1 and CHSCT. They
have been replaced by the abbreviations an English-speaking workplace actually
uses — WFH, HRIS, LM, HSC — rather than translated literally. An acronym only
teaches this lesson if the reader has plausibly met it.

No API key required.
"""

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict

DOCS = Path(__file__).resolve().parent / "sample_docs"

OLLAMA_TAGS = "http://localhost:11434/api/tags"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_LLM", "llama3.2")

SYSTEM_PROMPT = (
    "You are a sparser: a document sanitiser. Rewrite the fragment supplied so "
    "that a machine can use it, without changing its meaning: spell out each "
    "acronym at its first occurrence, write complete sentences, and invent "
    "nothing. Answer with the corrected text alone."
)

# Claire's hostile fragment: raw text, acronyms, telegraphic style.
FRAGMENT = (
    "WFH 2d/wk max. Request via HRIS. LM sign-off mandatory. "
    "See HSC for special cases. HR decides if disputed."
)

# The spelling-out dictionary, for offline mode.
ACRONYMS = {
    "WFH": "work from home (WFH)",
    "HRIS": "Human Resources Information System (HRIS)",
    "LM": "line manager (LM)",
    "HSC": "Health and Safety Committee (HSC)",
    "HR": "Human Resources (HR)",
}


# ---------------------------------------------------------------------------
# Offline mode: correction by rules
# ---------------------------------------------------------------------------
def correct_offline(fragment: str) -> str:
    text = fragment
    # 1) Rewrite the telegraphic style into sentences, before spelling out.
    replacements = {
        "WFH 2d/wk max": "Working from home is authorised up to two days per week",
        "Request via HRIS": "The request is made through the HRIS",
        "LM sign-off mandatory": "Sign-off by the LM is mandatory",
        "See HSC for special cases": "Refer to the HSC for special cases",
        "HR decides if disputed": "HR decides in the event of a dispute",
    }
    for before, after in replacements.items():
        text = text.replace(before, after)
    # 2) Spell out the acronyms, once each, at the first occurrence.
    for abbrev, full in ACRONYMS.items():
        pattern = re.compile(r"\b" + re.escape(abbrev) + r"\b")
        m = pattern.search(text)
        if m:
            text = text[:m.start()] + full + text[m.end():]
    return text


# ---------------------------------------------------------------------------
# Local mode: Ollama
# ---------------------------------------------------------------------------
def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def correct_local(fragment: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": SYSTEM_PROMPT + "\n\nFragment:\n" + fragment,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("response", "").strip()
    except Exception as e:
        print(f"  (local mode unavailable: {e}) — falling back to offline")
        return correct_offline(fragment)


def deduce_metadata(fragment: str) -> Dict[str, str]:
    """The metadata injected on the fly by the sparser."""
    return {
        "theme": "remote work" if re.search(r"\bWFH\b|work from home", fragment, re.I) else "HR",
        "status": "to_be_approved",     # the sparser flags that the source was raw
        "confidentiality": "internal",
        "acronyms_spelled_out": True,
    }


def choose_mode() -> str:
    force = os.environ.get("LAB_MODE", "").lower()
    if force in {"offline", "local"}:
        return force
    return "local" if ollama_available() else "offline"


def main() -> None:
    print("=" * 78)
    print("Lab 7-4 — The sparser in action: automatic correction (Claire)")
    print("=" * 78)

    mode = choose_mode()
    print(f"\nCorrection mode: {mode}")

    print("\n--- BEFORE (the hostile fragment) ---")
    print(FRAGMENT)

    corrected = correct_local(FRAGMENT) if mode == "local" else correct_offline(FRAGMENT)

    print("\n--- AFTER (sanitised by the sparser) ---")
    print(corrected)

    meta = deduce_metadata(FRAGMENT)
    print("\n--- Metadata injected on the fly ---")
    for k, v in meta.items():
        print(f"  {k}: {v}")

    # The comparison: were the acronyms spelled out?
    print("\n--- Spelling-out comparison ---")
    for abbrev in ACRONYMS:
        before = bool(re.search(r"\b" + re.escape(abbrev) + r"\b", FRAGMENT))
        after_spelled = abbrev in corrected and "(" + abbrev + ")" in corrected
        if before:
            state = "spelled out" if after_spelled else "present (check it)"
            print(f"  {abbrev:6s}: {state}")

    DOCS.mkdir(parents=True, exist_ok=True)
    out = DOCS / "sparser_claire_fragment.json"
    out.write_text(json.dumps(
        {"before": FRAGMENT, "after": corrected, "metadata": meta},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResult written: {out.name}")

    print("\nWHAT TO REMEMBER")
    print("- The sparser does more than extract: it normalises and enriches on the fly.")
    print("- Spelling out acronyms and injecting metadata improves the search.")
    print("- Offline mode makes the mechanics visible; a local LLM goes further, for free.")


if __name__ == "__main__":
    main()
