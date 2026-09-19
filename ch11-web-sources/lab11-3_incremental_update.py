# -*- coding: utf-8 -*-
"""
Lab 11-3 — Incremental web updating: reprocess only what changed (Sophie)

Learning objective
------------------
Re-indexing everything all the time is expensive; never re-indexing condemns the
corpus to grow stale. The right road runs between the two: detect what has
really changed since the last ingestion — a page modified, added, removed — and
reprocess only that.

    Re-indexing everything is too expensive. Re-indexing nothing is dangerous.
    Only what changed is reprocessed.

A fingerprint (a hash of the cleaned content) is stored per page. At each pass
they are compared: unchanged -> skip; modified -> re-index; absent -> archive,
without deleting.

No API key. Reuses Lab 11-2 for the cleaning.
Run generate_fixtures.py first.
"""

import hashlib
import importlib.util
import json
from datetime import date
from pathlib import Path
from typing import Dict, List

FIX = Path(__file__).resolve().parent / "fixtures"
CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)
STATE = CACHE / "corpus_state.json"


def _load_lab(file_name: str):
    path = Path(__file__).resolve().parent / file_name
    spec = importlib.util.spec_from_file_location(file_name[:-3].replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fingerprint(text: str) -> str:
    """A hash of the CLEANED content, not of the raw HTML: blind to decoration."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_state() -> Dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"pages": {}}


def save_state(state: Dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def detect_changes(pages: List[tuple], state: Dict) -> Dict:
    """Compare the current state of the pages against the last known state.

    `pages` is a list of (logical_key, html_source) pairs. The logical key
    identifies the page in a stable way — its URL in production — while the
    source may point at a different snapshot from one pass to the next.
    """
    lab2 = _load_lab("lab11-2_clean_web_page.py")
    known = state["pages"]
    seen = set()
    report = {"unchanged": [], "modified": [], "added": [], "removed": []}
    new_state = {"pages": {}}

    for key, source in pages:
        seen.add(key)
        try:
            pivot = lab2.clean_page(source)
        except Exception:
            continue
        h = fingerprint(pivot["text"])
        new_state["pages"][key] = {
            "hash": h, "title": pivot["title"], "source": source,
            "last_ingestion": date.today().isoformat(),
            "status": "active",
        }
        if key not in known:
            report["added"].append(key)
        elif known[key]["hash"] != h:
            report["modified"].append(key)
        else:
            report["unchanged"].append(key)
            new_state["pages"][key]["last_ingestion"] = \
                known[key].get("last_ingestion", date.today().isoformat())

    # Pages known but absent this time -> archived, not deleted.
    for key in known:
        if key not in seen:
            report["removed"].append(key)
            new_state["pages"][key] = dict(known[key], status="archived")

    return {"report": report, "new_state": new_state}


def show_report(report: Dict) -> None:
    for key, label in [("added", "added"), ("modified", "modified"),
                       ("unchanged", "unchanged"), ("removed", "archived")]:
        items = report[key]
        print(f"  {label:12s}: {len(items)}" + (f"  -> {', '.join(items)}" if items else ""))


def main() -> None:
    print("=" * 78)
    print("Lab 11-3 — Incremental web updating (Sophie)")
    print("=" * 78)

    if not FIX.exists():
        print("\nFixtures not found. Run this first: python generate_fixtures.py")
        return

    # Start from a blank state, so the demonstration is reproducible.
    if STATE.exists():
        STATE.unlink()

    # --- Pass 1: the first ingestion, everything is new ---
    # A stable logical key (the URL in production) -> the initial snapshot.
    print("\n--- PASS 1: the first ingestion ---")
    state = load_state()
    pages_1 = [
        ("/rule", "rule_page_v1.html"),
        ("/datasheet", "datasheet_page.html"),
    ]
    res1 = detect_changes(pages_1, state)
    show_report(res1["report"])
    save_state(res1["new_state"])
    reindexed_1 = len(res1["report"]["added"]) + len(res1["report"]["modified"])
    print(f"  => pages to (re)index: {reindexed_1}")

    # --- Pass 2: the rule was updated (v1 -> v2), the datasheet disappears ---
    print("\n--- PASS 2: the rule changes (v2), the datasheet disappears ---")
    state = load_state()
    pages_2 = [
        ("/rule", "rule_page_v2.html"),  # the same key, the content modified
        # "/datasheet" is absent => archived
    ]
    res2 = detect_changes(pages_2, state)
    show_report(res2["report"])
    save_state(res2["new_state"])
    reindexed_2 = len(res2["report"]["added"]) + len(res2["report"]["modified"])
    print(f"  => pages to (re)index: {reindexed_2}, and not the whole corpus")

    # --- Pass 3: nothing changes, everything is skipped ---
    print("\n--- PASS 3: no change at all ---")
    state = load_state()
    res3 = detect_changes(pages_2, state)
    show_report(res3["report"])
    save_state(res3["new_state"])
    reindexed_3 = len(res3["report"]["added"]) + len(res3["report"]["modified"])
    print(f"  => pages to (re)index: {reindexed_3}, the corpus is already current")

    print("\n" + "=" * 78)
    print("WHAT INCREMENTAL UPDATING SHOWS")
    print("=" * 78)
    print("- At pass 2, one page changed: ONLY THAT ONE is re-indexed.")
    print("- The vanished datasheet is archived, not erased: the trace is kept, in")
    print("  keeping with the \"one truth\" principle of Chapter 7.")
    print("- The fingerprint covers the cleaned content: a mere change of decoration,")
    print("  a menu or an advert, does not trigger a pointless re-index.")

    print("\nWHAT TO REMEMBER")
    print("- Date and fingerprint each page: comparing costs less than redoing everything.")
    print("- Modified -> re-indexed; absent -> archived; unchanged -> skipped.")
    print("- This is what keeps a corpus alive without the effort exploding.")


if __name__ == "__main__":
    main()
