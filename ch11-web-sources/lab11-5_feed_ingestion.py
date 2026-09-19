# -*- coding: utf-8 -*-
"""
Lab 11-5 — Ingesting RSS feeds and APIs: normalising dynamic sources

Learning objective
------------------
Feeds — RSS, Atom, APIs — bring a continuous flow of new items. They are ingested
to complete the corpus with sources that are always current, while respecting the
same JSON document structure, and without creating duplicates.

    A feed is easier to ingest than a page: it is already structured.
    But it has to be normalised, deduplicated, and judged on its freshness.

A local, deterministic RSS feed is read here; the reader can point feedparser at
a real URL. Each entry becomes a fragment with source_type="rss", a link, a date.

No API key. Dependencies: feedparser.
Run generate_fixtures.py first.
"""

import json
from pathlib import Path
from typing import Dict

import feedparser

FIX = Path(__file__).resolve().parent / "fixtures"
CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)
SEEN_IDS = CACHE / "feed_seen_ids.json"


def normalize_entry(entry, feed_url: str) -> Dict:
    """Map an RSS or Atom entry onto the JSON document."""
    # feedparser already harmonises RSS 2.0 and Atom: title, link, summary, published.
    identifier = getattr(entry, "id", None) or getattr(entry, "link", "")
    return {
        "id": identifier,
        "content": f"{entry.get('title', '')}. {entry.get('summary', '')}",
        "metadata": {
            "source_type": "rss",
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "publication_date": entry.get("published", ""),
            "feed_url": feed_url,
        },
    }


def load_seen_ids() -> set:
    if SEEN_IDS.exists():
        return set(json.loads(SEEN_IDS.read_text(encoding="utf-8")))
    return set()


def save_seen_ids(ids: set) -> None:
    SEEN_IDS.write_text(json.dumps(sorted(ids), ensure_ascii=False), encoding="utf-8")


def ingest_feed(source: str, feed_url: str) -> Dict:
    """Parse the feed, normalise it, and deduplicate by identifier."""
    # feedparser accepts a URL, a file path or a string.
    path = FIX / source if not source.startswith("http") else source
    feed = feedparser.parse(str(path))

    seen = load_seen_ids()
    new, skipped = [], []
    for entry in feed.entries:
        frag = normalize_entry(entry, feed_url)
        if frag["id"] in seen:
            skipped.append(frag)
        else:
            new.append(frag)
            seen.add(frag["id"])

    save_seen_ids(seen)
    return {"feed_title": feed.feed.get("title", ""), "new": new, "skipped": skipped}


def validate(frag: Dict) -> bool:
    """A minimal validation: a title, and content long enough to be worth it."""
    return bool(frag["metadata"]["title"]) and len(frag["content"]) > 15


def main() -> None:
    print("=" * 78)
    print("Lab 11-5 — Ingesting RSS feeds and APIs: normalising dynamic sources")
    print("=" * 78)

    if not FIX.exists():
        print("\nFixtures not found. Run this first: python generate_fixtures.py")
        return

    # Start from a blank cache, so the demonstration is reproducible.
    if SEEN_IDS.exists():
        SEEN_IDS.unlink()

    feed_url = "https://portal.example/news"

    # --- The first ingestion: everything is new ---
    print("\n--- PASS 1: the first ingestion of the feed ---")
    res1 = ingest_feed("news_feed.xml", feed_url)
    print(f"Feed: {res1['feed_title']}")
    print(f"New articles: {len(res1['new'])}, skipped as duplicates: {len(res1['skipped'])}")
    for frag in res1["new"]:
        valid = "ok" if validate(frag) else "rejected"
        print(f"  [{valid}] {frag['metadata']['publication_date']} — "
              f"{frag['metadata']['title']}")

    # --- The second ingestion: the same items have already been seen ---
    print("\n--- PASS 2: re-reading the same feed ---")
    res2 = ingest_feed("news_feed.xml", feed_url)
    print(f"New articles: {len(res2['new'])}, "
          f"skipped as duplicates: {len(res2['skipped'])}")
    print("  => no duplicate reinserted: deduplication by identifier works.")

    # Write the normalised fragments.
    out = FIX / "normalised_feed.json"
    out.write_text(json.dumps(res1["new"], ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON written: {out.name}")

    print("\n" + "=" * 78)
    print("WHAT FEED INGESTION DOES")
    print("=" * 78)
    print("- feedparser harmonises RSS 2.0 and Atom: one piece of code reads both.")
    print("- Each entry becomes a dated fragment, with its link and its source feed.")
    print("- Deduplication by identifier avoids reinserting articles already seen.")

    print("\nWHAT TO REMEMBER")
    print("- A feed is already structured: title, date, link — the mapping is direct.")
    print("- Deduplicate by id or link: a feed read twice does not pollute the corpus.")
    print("- A minimal validation, on title and length, discards empty or junk entries.")


if __name__ == "__main__":
    main()
