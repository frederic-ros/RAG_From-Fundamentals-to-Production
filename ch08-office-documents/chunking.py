# -*- coding: utf-8 -*-
"""
chunking.py — the shared chunking module of Chapter 8.

The key idea of the chapter: once a document has been brought back to the JSON
document pivot, cutting it into chunks NO LONGER CARES about the source format.
Word, PDF or a slide deck all end at the same kind of chunk:

    {
      "chunk_id": "...",
      "content": "<the text to vectorise>",
      "metadata": { ... provenance and structure ... }
    }

The module is deliberately simple and deterministic. It is reused by Labs 8-1 to
8-3 (chunking a pivot), and it shows, in Labs 8-4 and 8-5, that the merged
corpus is chunked in the same way whatever the source.

No external dependency, no API key.
"""

from typing import Dict, List


def _add_chunk(chunks: List[Dict], prefix: str, content: str,
                   metadata: Dict) -> None:
    content = (content or "").strip()
    if not content:
        return
    chunks.append({
        "chunk_id": f"{prefix}_{len(chunks) + 1:03d}",
        "content": content,
        "metadata": metadata,
    })


def _walk_sections(sections: List[Dict], chunks: List[Dict],
                        prefix: str, base_meta: Dict,
                        title_path: List[str]) -> None:
    """Walk the tree recursively, producing one chunk per section.

    The path of the parent headings is kept in the metadata, so a chunk knows
    "where" it sits in the document — a breadcrumb trail.
    """
    for s in sections:
        title = s.get("title", "")
        # A section's text may be under "text" (Labs 8-1 and 8-2) or "content".
        text = s.get("text", s.get("content", ""))
        path = title_path + ([title] if title else [])

        meta = dict(base_meta)
        meta["section_title"] = title
        meta["section_path"] = " > ".join(path) if path else ""
        if "level" in s:
            meta["level"] = s["level"]
        if "position" in s:
            meta["position"] = s["position"]
        # Slide decks carry notes: they are folded into the content.
        if s.get("presenter_notes"):
            text = (text + " " + s["presenter_notes"]).strip()
            meta["has_presenter_notes"] = True

        _add_chunk(chunks, prefix, text, meta)

        # Subsections, from the Word tree.
        _walk_sections(s.get("subsections", []), chunks, prefix, base_meta, path)


def chunk_pivot(pivot: Dict, prefix: str = "CHUNK") -> List[Dict]:
    """Cut a document pivot into chunks, one per section or subsection.

    A deliberately simple strategy: one section is one chunk. Finer chunking, by
    size or by sentence, belongs to later chapters. What matters here is that
    the chunk inherits the structure and the provenance cleanly.
    """
    base_meta = {
        "document_titre": pivot.get("title", ""),
        "source_format": pivot.get("metadata", {}).get("source_format", ""),
    }
    # Copy across the useful provenance metadata, where present.
    for key in ("status", "date", "version", "source"):
        value = pivot.get("metadata", {}).get(key)
        if value is not None:
            base_meta[key] = value

    chunks: List[Dict] = []
    _walk_sections(pivot.get("sections", []), chunks, prefix, base_meta, [])
    return chunks


def chunk_corpus(corpus: Dict, prefix: str = "CHUNK") -> List[Dict]:
    """Cut a merged corpus, a list of fragments, into chunks.

    Each fragment of the corpus — already flattened in Lab 8-4 — becomes a
    chunk, keeping the whole of its provenance metadata.
    """
    chunks: List[Dict] = []
    for frag in corpus.get("fragments", []):
        meta = dict(frag.get("metadata", {}))
        meta["fragment_id"] = frag.get("id", "")
        meta["section_title"] = frag.get("title", "")
        _add_chunk(chunks, prefix, frag.get("text", ""), meta)
    return chunks


def preview(chunks: List[Dict], limit: int = 6) -> None:
    """Print a readable preview of the chunks produced."""
    print(f"{'chunk_id':16s} | {'format':6s} | content (start)")
    print("-" * 78)
    for c in chunks[:limit]:
        meta = c["metadata"]
        fmt = meta.get("source_format") or meta.get("initial_format") or "?"
        excerpt = c["content"][:46].replace("\n", " ")
        print(f"{c['chunk_id']:16s} | {fmt:6s} | {excerpt}…")
    if len(chunks) > limit:
        print(f"... ({len(chunks) - limit} further chunks)")
