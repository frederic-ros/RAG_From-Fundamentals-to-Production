# -*- coding: utf-8 -*-
"""
Lab 8-5 — The conflict detector: arbitrating between competing versions

Learning objective
------------------
Go beyond pure parsing, and touch the reconciliation of documentary truth across
formats. Starting from the merged corpus of Lab 8-4, the fragments describing
the SAME rule — the number of days, eligibility, dates — are compared, and the
contradictions identified. The system raises a governance alert and names the
version that carries authority, from the status metadata.

Two modes, chosen automatically:

  1. OFFLINE (the default): detection by deterministic rules. Nothing to install.
  2. LOCAL (Ollama): a local LLM explains the divergences in natural language.
     Activated if Ollama answers. No data leaves the machine.

To force a mode: set LAB_MODE to offline or local.

No API key. Reuses merged_corpus.json from Lab 8-4.
"""

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

DOCS = Path(__file__).resolve().parent / "sample_docs"
CORPUS = DOCS / "merged_corpus.json"

OLLAMA_TAGS = "http://localhost:11434/api/tags"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_LLM", "llama3.2")

# Status priority: which version carries authority in a conflict.
STATUS_PRIORITY = {"approved": 3, "draft": 1, "deck": 0}


def load_corpus() -> Dict:
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def extract_days(text: str) -> Optional[str]:
    """Spot the number of remote-work days mentioned in a fragment.

    Both spellings are handled: the digit ("3 days") and the word ("three
    days"), because the three source formats do not write it the same way.
    """
    number_words = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    }
    t = text.lower()
    m = re.search(r"(\d+)\s+days?", t)
    if m:
        return m.group(1)
    for word, digit in number_words.items():
        if re.search(rf"\b{word}\s+days?", t):
            return digit
    if "several days" in t or "still being approved" in t:
        return "not stated"
    return None


def detect_day_conflict(corpus: Dict) -> List[Dict]:
    """Gather the fragments that speak of the number of days, and their values."""
    found = []
    for f in corpus["fragments"]:
        days = extract_days(f["text"])
        if days is not None and ("day" in f["text"].lower()):
            found.append({
                "id": f["id"],
                "format": f["metadata"]["initial_format"],
                "status": f["metadata"]["status"],
                "days": days,
                "title": f["title"],
            })
    return found


def arbitrate(conflicting: List[Dict]) -> Optional[Dict]:
    """Name the fragment that carries authority: the highest status."""
    candidates = [f for f in conflicting if f["days"] not in (None, "not stated")]
    if not candidates:
        return None
    return max(candidates, key=lambda f: STATUS_PRIORITY.get(f["status"], 0))


# ---------------------------------------------------------------------------
# Explanation by a local LLM (optional)
# ---------------------------------------------------------------------------
def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def explain_local(conflicting: List[Dict], authoritative: Dict) -> str:
    summary = "; ".join(
        f"{f['format']} ({f['status']}): {f['days']} day(s)"
        for f in conflicting)
    prompt = (
        "You are a document auditor. Here are several versions of the same "
        "remote-work rule, with their format and their status:\n" + summary + "\n"
        f"The version that carries authority is: {authoritative['format']} "
        f"({authoritative['status']}), {authoritative['days']} days.\n"
        "Explain the divergence in two sentences, and why this version prevails.")
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("response", "").strip()
    except Exception:
        return ""


def choose_mode() -> str:
    force = os.environ.get("LAB_MODE", "").lower()
    if force in {"offline", "local"}:
        return force
    return "local" if ollama_available() else "offline"


def main() -> None:
    print("=" * 78)
    print("Lab 8-5 — The conflict detector: arbitrating between versions")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run Labs 8-1 to 8-4 first.")
        return

    corpus = load_corpus()
    mode = choose_mode()
    print(f"\nAnalysis mode: {mode}")

    conflict = detect_day_conflict(corpus)

    print("\n--- Fragments describing the NUMBER OF DAYS ---")
    print(f"{'id':9s} | {'format':6s} | {'status':9s} | days")
    print("-" * 60)
    for f in conflict:
        print(f"{f['id']:9s} | {f['format']:6s} | {f['status']:9s} | {f['days']}")

    values = {f["days"] for f in conflict if f["days"] not in (None, "not stated")}

    print("\n" + "=" * 78)
    print("THE GOVERNANCE AUDIT REPORT")
    print("=" * 78)

    if len(values) > 1:
        print(f"CONFLICT DETECTED: divergent values for the number of days: "
              f"{', '.join(sorted(values))}.")
        winner = arbitrate(conflict)
        if winner:
            print(f"\nThe version that carries authority: {winner['format'].upper()} "
                  f"(status \"{winner['status']}\") -> {winner['days']} days.")
            print("\nFragments to set aside, obsolete or unofficial:")
            for f in conflict:
                if f["id"] != winner["id"] and f["days"] not in (None, "not stated"):
                    print(f"  - {f['id']} ({f['format']}, {f['status']}): "
                          f"{f['days']} days -> set aside")
                elif f["days"] == "not stated":
                    print(f"  - {f['id']} ({f['format']}, {f['status']}): "
                          f"not stated -> informative only")

            if mode == "local":
                explanation = explain_local(conflict, winner)
                if explanation:
                    print("\nExplanation (local LLM):")
                    print("  " + explanation.replace("\n", "\n  "))
    else:
        print("No conflict: a single reference value.")

    print("\nWHAT TO REMEMBER")
    print("- The difficulty is not always extracting: it is reconciling.")
    print("- The status metadata settles it: the approved document carries authority.")
    print("- A conflict detector turns a corpus into a governed source of truth.")


if __name__ == "__main__":
    main()
