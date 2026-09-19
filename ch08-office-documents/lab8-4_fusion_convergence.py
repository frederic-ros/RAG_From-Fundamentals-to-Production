# -*- coding: utf-8 -*-
"""
Lab 8-4 — The convergence: merging Word, PDF and deck into one corpus

Learning objective
------------------
Put the pivot format into practice: erase the technical barriers between Word,
PDF and PowerPoint. The three pivots produced by Labs 8-1 to 8-3 are merged into
a single corpus, under a unified metadata schema — source, initial format, date
of processing, status, access rights — so that the provenance of each fragment
survives the merge.

No external dependency, no API key.
Run Labs 8-1 to 8-3 first.
"""

import json
from datetime import date
from pathlib import Path
from typing import Dict, List

DOCS = Path(__file__).resolve().parent / "sample_docs"

# Schema of provenance by format (status and droits, fil rouge governance).
PROVENANCE = {
    "pivot_word.json": {
        "source": "HR department (draft)",
        "initial_format": "docx",
        "status": "draft",
        "access_rights": "internal",
    },
    "pivot_pdf.json": {
        "source": "HR directorate (official)",
        "initial_format": "pdf",
        "status": "approved",
        "access_rights": "circulable",
    },
    "pivot_pptx.json": {
        "source": "Department meeting",
        "initial_format": "pptx",
        "status": "deck",
        "access_rights": "internal",
    },
}


def flatten_sections(sections: List[Dict]) -> List[Dict]:
    """Flatten the Word tree into a list of simple fragments."""
    fragments = []
    for s in sections:
        text = s.get("text", "")
        title = s.get("title", "")
        if text:
            fragments.append({"title": title, "text": text})
        fragments.extend(flatten_sections(s.get("subsections", [])))
    return fragments


def load_fragments(nom_fichier: str) -> List[Dict]:
    path = DOCS / nom_fichier
    pivot = json.loads(path.read_text(encoding="utf-8"))
    return flatten_sections(pivot.get("sections", []))


def merge() -> Dict:
    aujourd_hui = date.today().isoformat()
    corpus = {
        "corpus_title": "Remote work agreement — a multi-format corpus",
        "date_traitement": aujourd_hui,
        "fragments": [],
    }

    fid = 0
    for nom_fichier, provenance in PROVENANCE.items():
        path = DOCS / nom_fichier
        if not path.exists():
            print(f"  (manquant : {nom_fichier} — lancez le TP correspondant)")
            continue
        for frag in load_fragments(nom_fichier):
            fid += 1
            corpus["fragments"].append({
                "id": f"frag_{fid:03d}",
                "title": frag["title"],
                "text": frag["text"],
                "metadata": {
                    **provenance,
                    "date_traitement": aujourd_hui,
                },
            })
    return corpus


def main() -> None:
    print("=" * 78)
    print("Lab 8-4 — L'atelier de convergence : fusion multi-format")
    print("=" * 78)

    requis = list(PROVENANCE.keys())
    manquants = [n for n in requis if not (DOCS / n).exists()]
    if manquants:
        print("\nPivots manquants : " + ", ".join(manquants))
        print("Lancez d'abord Lab 8-1, Lab 8-2 et Lab 8-3.")
        if len(manquants) == len(requis):
            return

    corpus = merge()

    print(f"\nFragments merged: {len(corpus['fragments'])}")
    print(f"Date de traitement : {corpus['date_traitement']}")

    print("\n--- A preview of the fragments, provenance documented ---")
    print(f"{'id':9s} | {'format':6s} | {'status':9s} | title")
    print("-" * 78)
    for f in corpus["fragments"]:
        m = f["metadata"]
        print(f"{f['id']:9s} | {m['initial_format']:6s} | {m['status']:9s} | {f['title'][:38]}")

    # A summary by format.
    print("\n--- The split by format ---")
    par_format: Dict[str, int] = {}
    for f in corpus["fragments"]:
        fmt = f["metadata"]["initial_format"]
        par_format[fmt] = par_format.get(fmt, 0) + 1
    for fmt, n in sorted(par_format.items()):
        print(f"  {fmt} : {n} fragments")

    out_path = DOCS / "merged_corpus.json"
    out_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nCorpus written: {out_path.name}")

    # --- The merged corpus is chunked the same way, whatever the format ---
    from chunking import chunk_corpus, preview
    chunks = chunk_corpus(corpus, prefix="CHUNK")
    print(f"\n--- Corpus chunks (all sources together): {len(chunks)} ---")
    preview(chunks, limit=12)
    chunks_path = DOCS / "chunks_corpus.json"
    chunks_path.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Chunks written: {chunks_path.name}")

    print("\nA RETENIR")
    print("- The pivot erases the format: Word, PDF and deck all become fragments.")
    print("- Each fragment keeps its provenance: source, format, status, rights.")
    print("- Chunking no longer cares about the format: one cut for the whole corpus.")


if __name__ == "__main__":
    main()
