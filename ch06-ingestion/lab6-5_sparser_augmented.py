# -*- coding: utf-8 -*-
"""
Lab 6-5 — Implementing a metadata-augmented "Sparser" (the whole pipeline)

Learning objective
------------------
Assemble the pieces of the previous labs into a Smart Parser, a Sparser: a
pipeline that ingests a document, extracts its structured text (the JSON pivot
format), and then automatically ENRICHES each section with metadata computed on
the fly:

  - the language detected;
  - the estimated level of confidentiality;
  - the classification of the section (a restrictive clause, or general
    information);
  - a small local summary of the section.

The enrichment follows the same hybrid principle as Lab 6-4:

  1. OFFLINE (the default): enrichment by deterministic heuristics, with no LLM.
     Runs anywhere.
  2. LOCAL (Ollama): a light local LLM (llama3.2, mistral) for the summary and
     the classification, activated if Ollama answers.

To force a mode: set LAB_MODE to offline or local.

A note on the word lists below: language detection, confidentiality and section
classification all rest on English word lists. They must match the language of
the corpus. Point this pipeline at a French document and the detector will
answer "other", the two classifiers will fall silent, and nothing will raise an
error.

Requires python-docx, beautifulsoup4, pypdf (it reuses Lab 6-1).
Run generate_sample_docs.py first.
"""

import importlib.util
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict

DOCS = Path(__file__).resolve().parent / "sample_docs"

# Reuse the parsers of Lab 6-1, if it sits alongside.
try:
    _lab61 = Path(__file__).resolve().parent / "lab6-1_multiformat_to_json.py"
    _spec = importlib.util.spec_from_file_location("lab61", _lab61)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    parse_docx = _mod.parse_docx
    parse_html = _mod.parse_html
    parse_pdf = _mod.parse_pdf
except Exception:  # pragma: no cover
    parse_docx = parse_html = parse_pdf = None


OLLAMA_TAGS = "http://localhost:11434/api/tags"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = os.environ.get("OLLAMA_LLM", "llama3.2")

# Reuse the un-interleaving and cleaning of Lab 6-3, if it is present.
try:
    _lab63 = Path(__file__).resolve().parent / "lab6-3_reading_order_cleaning.py"
    _spec3 = importlib.util.spec_from_file_location("lab63", _lab63)
    _mod3 = importlib.util.module_from_spec(_spec3)
    _spec3.loader.exec_module(_mod3)
    extract_by_columns = _mod3.extract_by_columns
    strip_noise = _mod3.clean
except Exception:  # pragma: no cover
    extract_by_columns = strip_noise = None


# ---------------------------------------------------------------------------
# Enrichment heuristics (offline mode)
# ---------------------------------------------------------------------------
EN_WORDS = {"the", "a", "an", "of", "to", "in", "on", "for", "by", "with",
            "and", "or", "is", "are", "be", "this", "that", "it", "as", "at",
            "from", "must", "may", "shall", "will"}

CONFIDENTIAL_WORDS = {"confidential", "secret", "personal", "hr", "salary",
                      "payroll", "termination", "penalties", "sanction"}

RESTRICTIVE_WORDS = {"prohibited", "prohibition", "must not", "obligation",
                     "mandatory", "termination", "penalties", "sanction",
                     "exclusively", "limit"}


def detect_language(text: str) -> str:
    tokens = re.findall(r"[a-z]+", text.lower())
    if not tokens:
        return "undetermined"
    ratio = sum(1 for t in tokens if t in EN_WORDS) / len(tokens)
    return "en" if ratio > 0.08 else "other"


def estimate_confidentiality(text: str) -> str:
    t = text.lower()
    score = sum(1 for word in CONFIDENTIAL_WORDS if word in t)
    if score >= 2:
        return "high"
    if score == 1:
        return "medium"
    return "low"


def classify_section(text: str) -> str:
    t = text.lower()
    if any(word in t for word in RESTRICTIVE_WORDS):
        return "restrictive clause"
    return "general information"


def summarize_offline(text: str, max_words: int = 18) -> str:
    """A small extractive summary: the first sentence, truncated."""
    sentence = re.split(r"(?<=[.!?])\s", text.strip())[0] if text.strip() else ""
    words = sentence.split()
    if len(words) <= max_words:
        return sentence
    return " ".join(words[:max_words]) + "…"


# ---------------------------------------------------------------------------
# Local enrichment through Ollama — summary and classification
# ---------------------------------------------------------------------------
def ollama_available() -> bool:
    try:
        with urllib.request.urlopen(OLLAMA_TAGS, timeout=1.5) as r:
            return r.status == 200
    except Exception:
        return False


def summarize_local(text: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"Summarise in one short sentence, in English:\n\n{text}",
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8")).get("response", "").strip()
    except Exception:
        return summarize_offline(text)


# ---------------------------------------------------------------------------
# The Sparser
# ---------------------------------------------------------------------------
def parse_public_contract(path: Path) -> Dict:
    """A parser dedicated to the two-column procurement PDF: reuses Lab 6-3.

    The columns are un-interleaved, the noise stripped, and the lines then
    grouped into sections by article ("Article 1 - ...").
    """
    if extract_by_columns is None:
        raise ValueError("Lab 6-3 absent: the two-column PDF cannot be processed.")

    lines = strip_noise(extract_by_columns(path))

    pivot = {"title": "Public contract 2025-MP-014",
             "sections": [],
             "metadata": {"source_format": "pdf-2columns"}}

    current_section = None
    article_pattern = re.compile(r"^Article\s+\d+\s*-\s*(.*)", re.IGNORECASE)
    for line in lines:
        m = article_pattern.match(line)
        if m:
            title = line.rstrip(".")
            current_section = {"title": title, "content": ""}
            pivot["sections"].append(current_section)
        elif current_section is not None:
            sep = " " if current_section["content"] else ""
            current_section["content"] += sep + line

    return pivot


def choose_mode() -> str:
    force = os.environ.get("LAB_MODE", "").lower()
    if force in {"offline", "local"}:
        return force
    return "local" if ollama_available() else "offline"


def enrich_section(section: Dict, mode: str) -> Dict:
    text = section.get("content", "")
    summary = summarize_local(text) if mode == "local" else summarize_offline(text)
    return {
        "title": section.get("title", ""),
        "content": text,
        "section_metadata": {
            "language": detect_language(text),
            "confidentiality": estimate_confidentiality(text),
            "class": classify_section(text),
            "summary": summary,
        },
    }


def sparser(path: Path) -> Dict:
    """The complete pipeline: structured extraction, then enrichment on the fly."""
    suffix = path.suffix.lower()
    if suffix == ".docx" and parse_docx:
        pivot = parse_docx(path)
    elif suffix == ".html" and parse_html:
        pivot = parse_html(path)
    elif suffix == ".pdf" and "contract" in path.stem.lower():
        # A PDF laid out in 2 columns: it goes through the Lab 6-3 pipeline.
        pivot = parse_public_contract(path)
    elif suffix == ".pdf" and parse_pdf:
        pivot = parse_pdf(path)
    else:
        raise ValueError(f"Format not handled, or Lab 6-1 absent: {suffix}")

    mode = choose_mode()
    pivot["sections"] = [enrich_section(s, mode) for s in pivot["sections"]]
    pivot["metadata"]["enrichment_mode"] = mode
    pivot["metadata"]["document_language"] = detect_language(
        " ".join(s["content"] for s in pivot["sections"]))
    return pivot


def main() -> None:
    print("=" * 78)
    print("Lab 6-5 — The Sparser: parsing augmented with metadata")
    print("=" * 78)

    if parse_docx is None:
        print("\nLab 6-1 not found alongside this script. Put both in the same folder.")
        return
    if not DOCS.exists():
        print("\nDocuments not found. Run this first: python generate_sample_docs.py")
        return

    # Two contrasting documents are enriched: the HR note and the contract.
    targets = [
        DOCS / "claire_service_note.docx",
        DOCS / "sophie_contract_2columns.pdf",
    ]

    print(f"\nEnrichment mode: {choose_mode()}")

    for path in targets:
        if not path.exists():
            print(f"\n(file missing: {path.name})")
            continue

        print("\n" + "=" * 78)
        print(f"DOCUMENT: {path.name}")
        print("=" * 78)

        try:
            pivot = sparser(path)
        except ValueError as e:
            print(f"  {e}")
            continue

        print(f"Title: {pivot['title']}")
        print(f"Document language: {pivot['metadata'].get('document_language')}")
        print(f"Sections enriched: {len(pivot['sections'])}")

        for s in pivot["sections"]:
            meta = s["section_metadata"]
            print(f"\n  - {s['title']}")
            print(f"    language={meta['language']} | confidentiality={meta['confidentiality']} "
                  f"| class={meta['class']}")
            print(f"    summary: {meta['summary']}")

        out = DOCS / f"sparser_{path.stem}.json"
        out.write_text(json.dumps(pivot, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n  Augmented JSON written: {out.name}")

    print("\n" + "=" * 78)
    print("WHAT TO REMEMBER")
    print("=" * 78)
    print("- The Sparser goes beyond conversion: it turns ingestion into semantic")
    print("  enrichment.")
    print("- Each section gains computed metadata — language, confidentiality, class,")
    print("  summary — which will serve filtering and routing inside the RAG.")
    print("- Offline mode makes everything reproducible; local mode through Ollama")
    print("  shows what a real LLM adds, with no key and no cost.")


if __name__ == "__main__":
    main()
