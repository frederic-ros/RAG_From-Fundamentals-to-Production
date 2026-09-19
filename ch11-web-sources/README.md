# ch11-web-sources — Ingesting the Web & Living Sources

Labs for Chapter 11 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 11, which closes the ingestion part. You leave the frozen files for the living sources: web pages, feeds, emails. The six labs form a progression. You first fuse heterogeneous sources while arbitrating the versions, because the noise is not only visual but also logical: an outdated information. You then clean a web page to isolate the signal, then you update the corpus incrementally, without reindexing everything. You build a router that chooses between internal corpus and web — the first step toward the agentic. You ingest RSS feeds, then emails, the most precious and the most informal living source of the enterprise. All the labs work on deterministic local sources, without an API key or a network; the reader will be able to plug the same logic onto real URLs, real feeds, and real mailboxes.

## Labs

1. **Lab 11-1 — Multi-source fusion and version arbitration**
2. **Lab 11-2 — Cleaning a web page**
3. **Lab 11-3 — Incremental web update**
4. **Lab 11-4 — Local / web router**
5. **Lab 11-5 — Ingestion of RSS feeds and API**
6. **Lab 11-6 — The email funnel**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_fixtures.py
python lab11-1_source_arbitration.py
```

## Dependencies

```
beautifulsoup4>=4.12.0    # parsing HTML et e-mails (Lab 11-2, 11-6)
readability-lxml>=0.8.1   # extraction of a page's main content (Lab 11-2)
feedparser>=6.0.0         # flux RSS / Atom (Lab 11-5)
scikit-learn>=1.3.0       # recherche transverse (Lab 11-1)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
