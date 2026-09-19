# -*- coding: utf-8 -*-
"""
Lab 11-2 — Cleaning a web page: extracting the signal, discarding the noise

Learning objective
------------------
A web page mixes signal (the useful content) with noise (menus, banners,
adverts, footers). Indexing the raw page risks bringing back a navigation menu
instead of an answer. This lab isolates the main content and carries it over to
the JSON document, with its metadata: URL or source, title, date of retrieval.

It works on deterministic local HTML fixtures; the reader can point the same
function at a real URL through requests.

No API key. Dependencies: beautifulsoup4, readability-lxml.
Run generate_fixtures.py first.
"""

import json
import re
from datetime import date
from pathlib import Path
from typing import Dict

from bs4 import BeautifulSoup

FIX = Path(__file__).resolve().parent / "fixtures"

# The residual noise patterns to cut: the breadcrumb, the repeated notices.
NOISE_PATTERNS = [
    re.compile(r"^Home\s*>\s*Texts\s*>.*$"),
    re.compile(r"^©\s*\d{4}.*$"),
]


def load_html(source: str) -> str:
    """Load the HTML from a local fixture or from a URL.

    For a real URL (http...) requests would be used; here the local file is read
    so that the lab is reproducible with no network.
    """
    if source.startswith("http"):
        import urllib.request
        with urllib.request.urlopen(source, timeout=20) as r:
            return r.read().decode("utf-8", errors="replace")
    return (FIX / source).read_text(encoding="utf-8")


def naive_raw_text(html: str) -> str:
    """What a plain .get_text() would give: everything, noise included."""
    return BeautifulSoup(html, "html.parser").get_text(" ", strip=True)


def clean_page(source: str) -> Dict:
    """Isolate the main content and carry it over to the JSON document."""
    html = load_html(source)

    # readability identifies the main content zone (article or main).
    from readability import Document
    doc = Document(html)
    title = doc.title()
    main_html = doc.summary()

    soup = BeautifulSoup(main_html, "html.parser")

    # Rebuild a simple structure: headings, paragraphs, list items.
    sections = []
    for el in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        txt = el.get_text(" ", strip=True)
        if not txt or any(m.match(txt) for m in NOISE_PATTERNS):
            continue
        sections.append({"tag": el.name, "text": txt})

    full_text = " ".join(s["text"] for s in sections)

    return {
        "title": title,
        "sections": sections,
        "text": full_text,
        "metadata": {
            "source_type": "web",
            "source": source,
            "retrieval_date": date.today().isoformat(),
            "cleaned": True,
        },
    }


def main() -> None:
    print("=" * 78)
    print("Lab 11-2 — Cleaning a web page: extracting the signal, discarding the noise")
    print("=" * 78)

    if not FIX.exists():
        print("\nFixtures not found. Run this first: python generate_fixtures.py")
        return

    source = "rule_page_v2.html"

    # Before: the naive extraction.
    raw = naive_raw_text(load_html(source))
    print("\n--- BEFORE: a naive .get_text(), signal drowned in noise ---")
    print(f"  {raw[:160]}…")
    noise_before = sum(x in raw for x in ("ADVERTISEMENT", "Home", "Site map", "Legal notice"))
    print(f"  noise elements detected: {noise_before}")

    # After: the cleaning.
    pivot = clean_page(source)
    print("\n--- AFTER: the main content isolated ---")
    print(f"  Title: {pivot['title']}")
    print(f"  Sections kept: {len(pivot['sections'])}")
    for s in pivot["sections"][:5]:
        print(f"    [{s['tag']}] {s['text'][:60]}")

    text = pivot["text"]
    noise_after = sum(x in text for x in ("ADVERTISEMENT", "Site map", "Legal notice"))
    # The rate is written "4.7%" in the English fixtures. Keep this check string
    # in step with generate_fixtures.py, or the lab reports a false failure.
    signal_present = "4.7%" in text

    print("\n" + "=" * 78)
    print("THE RESULT")
    print("=" * 78)
    print(f"Residual noise (advert, site map, notices): {noise_after}")
    print(f"Signal kept (the 4.7% rate): {'YES' if signal_present else 'NO'}")

    out = FIX / "cleaned_page.json"
    out.write_text(json.dumps(pivot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"JSON written: {out.name}")

    print("\nWHAT TO REMEMBER")
    print("- A web page is signal drowned in decoration: it has to be isolated.")
    print("- readability spots the content zone; a post-filter removes the residual noise.")
    print("- The result is a clean JSON document, with its provenance and its freshness.")


if __name__ == "__main__":
    main()
