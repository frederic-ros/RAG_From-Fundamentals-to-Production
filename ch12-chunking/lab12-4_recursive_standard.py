# -*- coding: utf-8 -*-
"""
Lab 12-4 — Why recursive chunking became the standard (the good default)

Learning objective
------------------
The chapter calls recursive chunking "the good default". This lab shows WHY: it
respects the structure of the text — paragraphs, then sentences, then words only
if necessary — combined with a light overlap. You see what makes it the best
starting point, and where it remains imperfect.

  Cut while respecting a hierarchy of natural separators: paragraphs first,
  then sentences, then words, and only if necessary.

Recursive chunking is compared with a fixed cut on the same texts, looking at:
  - respect for sentence boundaries (few mid-sentence cuts);
  - regularity of the sizes (bounded fragments);
  - the case where it stays imperfect (an idea straddling two paragraphs).

No API key. Uses tokenizer.py and the local corpus.
Run generate_corpus.py first.
"""

from pathlib import Path
from typing import Dict, List

import tokenizer as tk

CORPUS = Path(__file__).resolve().parent / "corpus"

SEPARATORS = ["\n\n", ". ", " "]  # hierarchy: paragraph, sentence, word


def split_recursive(text: str, size: int = 70, overlap: int = 12,
                    separators: List[str] = None) -> List[str]:
    """Recursive chunking: try the coarsest separator first, and go down the
    hierarchy as long as a piece exceeds the target size. A light overlap is
    added between consecutive fragments."""
    if separators is None:
        separators = SEPARATORS

    def _split(txt: str, level: int) -> List[str]:
        if tk.count(txt) <= size:
            return [txt.strip()]
        if level >= len(separators):
            # No separator left: a hard cut in tokens, as a last resort.
            tokens = tk.encode(txt)
            return [tk.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]
        sep = separators[level]
        pieces = [p for p in txt.split(sep) if p.strip()]
        # Group the pieces up to the target size.
        groups, current = [], ""
        for p in pieces:
            candidate = (current + sep + p).strip(sep) if current else p
            if tk.count(candidate) > size and current:
                groups.append(current)
                current = p
            else:
                current = candidate
        if current:
            groups.append(current)
        # If a group still exceeds the size, go down one level.
        result = []
        for g in groups:
            if tk.count(g) > size:
                result.extend(_split(g, level + 1))
            else:
                result.append(g.strip())
        return result

    chunks = _split(text, 0)

    # Overlap: prefix each fragment with the last tokens of the previous one.
    if overlap > 0 and len(chunks) > 1:
        with_overlap = [chunks[0]]
        for i in range(1, len(chunks)):
            tail = tk.encode(chunks[i - 1])[-overlap:]
            with_overlap.append((tk.decode(tail) + " " + chunks[i]).strip())
        chunks = with_overlap
    return chunks


def split_fixed(text: str, size: int = 70) -> List[str]:
    tokens = tk.encode(text)
    return [tk.decode(tokens[i:i + size]) for i in range(0, len(tokens), size)]


def mid_sentence_cuts(chunks: List[str]) -> int:
    n = 0
    for c in chunks:
        c = c.strip()
        if c and c[-1] not in ".!?:":
            n += 1
    return n


def stats(chunks: List[str]) -> Dict:
    sizes = [tk.count(c) for c in chunks]
    return {
        "n": len(chunks),
        "cuts": mid_sentence_cuts(chunks),
        "size_min": min(sizes) if sizes else 0,
        "size_max": max(sizes) if sizes else 0,
    }


def main() -> None:
    print("=" * 78)
    print("Lab 12-4 — Why recursive chunking became the standard")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}")

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    text = (CORPUS / "technical_manual.txt").read_text(encoding="utf-8")

    fixed = split_fixed(text, 70)
    recursive = split_recursive(text, 70, overlap=12)

    s_fixed = stats(fixed)
    s_rec = stats(recursive)

    print("\n" + "=" * 78)
    print("COMPARISON ON THE TECHNICAL MANUAL")
    print("=" * 78)
    print(f"{'criterion':32s} | {'fixed size':>12s} | {'recursive':>10s}")
    print("-" * 78)
    print(f"{'fragments':32s} | {s_fixed['n']:>12d} | {s_rec['n']:>10d}")
    print(f"{'mid-sentence cuts':32s} | {s_fixed['cuts']:>12d} | {s_rec['cuts']:>10d}")
    print(f"{'size min / max (tokens)':32s} | "
          f"{str(s_fixed['size_min'])+'/'+str(s_fixed['size_max']):>12s} | "
          f"{str(s_rec['size_min'])+'/'+str(s_rec['size_max']):>10s}")

    print("\n--- A recursive fragment (it matches the natural cut) ---")
    # Show a representative fragment: the one closest to a maintenance section.
    candidate = next((c for c in recursive if "aintenance" in c),
                     recursive[0] if recursive else "")
    print(f"  \"{candidate[:120].strip()}…\"")

    print("\n" + "=" * 78)
    print("WHY IT IS THE RIGHT DEFAULT")
    print("=" * 78)
    print("- It respects the natural boundaries: markedly fewer mid-sentence cuts.")
    print("- It keeps fragments bounded: neither the isolated sentence nor the whole page.")
    print("- It costs almost nothing: no vectorisation, just separators.")
    print("- The light overlap catches the ideas that straddle two paragraphs.")

    print("\n--- Where it stays imperfect ---")
    print("Recursive chunking does not understand MEANING: if an idea stretches across two")
    print("distant paragraphs, it can still separate them. That is the limit semantic")
    print("chunking claims to overcome — at a high price, as Lab 12-5 shows.")

    print("\nWHAT TO REMEMBER")
    print("- Recursive means respecting the structure of the text, going down the separators as needed.")
    print("- It is the best starting point: simple, robust, cheap, structured.")
    print("- Add a light overlap; go further only when measurement justifies it.")


if __name__ == "__main__":
    main()
