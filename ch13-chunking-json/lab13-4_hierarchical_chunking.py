# -*- coding: utf-8 -*-
"""
Lab 13-4 — Hierarchical structural chunking (optional)

Learning objective
------------------
So far, one pivot block has been one fragment. But what do you do with a section
TOO LONG to fit a token budget? Two steps are chained, in this order — and the
order matters:

  1. STRUCTURAL chunking: cut first at the heading boundaries (structure
     commands);
  2. RECURSIVE chunking: if a section exceeds the budget, bound it by size
     WITHOUT crossing the boundaries already laid down (size adjusts).

And to each sub-fragment the hierarchical path is RE-ATTACHED: no piece becomes
an orphan, even when it had to be subdivided.

    Splitting on the structure does not only preserve meaning.
    It attaches to each fragment the trace of its origin — the metadata.

This lab builds a slightly larger Markdown document (with #, ## and ###
headings), chunks it while respecting the hierarchy, and shows that each fragment
keeps its full breadcrumb trail.

A NOTE ON THE BUDGET. BUDGET_TOKENS is set so that exactly one section — the
"Hours" section — overflows and gets subdivided. If you edit the Markdown, check
that one section still overflows, or the lab demonstrates nothing.

No API key. Uses tokenizer.py.
"""

from typing import List, Dict
import tokenizer as tk

BUDGET_TOKENS = 40   # beyond this, a section is subdivided by sentences

# A Markdown document, deliberately structured AND holding one long section.
MARKDOWN = """\
# Staff rules

## Working time

### Hours
The reference hours run from nine in the morning to five in the afternoon. \
A compulsory presence window applies from ten in the morning to four. \
Individual arrangements are possible with the manager's agreement, \
respecting the continuity of the service and the needs of the team.

### On-call duty
On-call duty is a period during which the member of staff stays reachable. \
It gives entitlement to compensation under the scale in force.

## Remote work
Remote work is authorised up to a limit of two days per week, \
in agreement with the line manager.
"""


def parse_markdown(md: str) -> List[Dict]:
    """Turn Markdown into blocks {path, text}, following the headings.

    Step 1: STRUCTURAL chunking on the headings (#, ##, ###). A stack of
    headings is kept, to rebuild the hierarchical path of each block.
    """
    blocks: List[Dict] = []
    stack: List[str] = []         # the current headings, by level
    levels: List[int] = []        # the depth attached to each heading on the stack
    buffer: List[str] = []

    def flush_buffer():
        if buffer:
            text = " ".join(l.strip() for l in buffer).strip()
            if text:
                blocks.append({"path": list(stack), "text": text})
            buffer.clear()

    for line in md.splitlines():
        if line.startswith("#"):
            flush_buffer()
            level = len(line) - len(line.lstrip("#"))
            title = line.lstrip("#").strip()
            # Pop the headings of equal or lower level.
            while levels and levels[-1] >= level:
                stack.pop()
                levels.pop()
            stack.append(title)
            levels.append(level)
        else:
            buffer.append(line)
    flush_buffer()
    return blocks


def split_recursive(text: str, budget: int) -> List[str]:
    """Step 2: if a block exceeds the budget, bound it BY SENTENCES.

    No heading boundary is crossed — we are already working inside a single
    structural block. Here size adjusts; structure has already commanded.
    """
    if tk.count(text) <= budget:
        return [text]
    sentences = [p.strip() for p in text.replace(". ", ".\n").split("\n") if p.strip()]
    pieces: List[str] = []
    current = ""
    for s in sentences:
        candidate = (current + " " + s).strip()
        if current and tk.count(candidate) > budget:
            pieces.append(current.strip())
            current = s
        else:
            current = candidate
    if current.strip():
        pieces.append(current.strip())
    return pieces


def hierarchical_chunk(md: str, budget: int) -> List[Dict]:
    """The full pipeline: structural first, recursive next, the path preserved."""
    fragments: List[Dict] = []
    for block in parse_markdown(md):
        for part in split_recursive(block["text"], budget):
            fragments.append({"path": block["path"], "text": part})
    return fragments


def trail(path: List[str]) -> str:
    return " > ".join(path) or "(root)"


def main() -> None:
    print("=" * 78)
    print("Lab 13-4 — Hierarchical structural chunking (optional)")
    print("=" * 78)
    print(f"\nTokenizer: {tk.mode()}   |   budget = {BUDGET_TOKENS} tokens")

    struct_blocks = parse_markdown(MARKDOWN)
    fragments = hierarchical_chunk(MARKDOWN, BUDGET_TOKENS)

    print("\n" + "=" * 78)
    print("STEP 1 — STRUCTURAL SPLITTING, BY HEADINGS")
    print("=" * 78)
    for i, b in enumerate(struct_blocks, start=1):
        print(f"  [{i}] {trail(b['path'])}   ({tk.count(b['text'])} tokens)")

    print("\n" + "=" * 78)
    print("STEP 2 — RECURSIVE SPLITTING OF THE OVERLONG SECTIONS")
    print("=" * 78)
    subdivided = 0
    for i, f in enumerate(fragments, start=1):
        n = tk.count(f["text"])
        mark = ""
        # Spot the sections that had to be subdivided.
        same_path = [x for x in fragments if x["path"] == f["path"]]
        if len(same_path) > 1:
            mark = "  (section subdivided)"
            subdivided += 1
        head = f["text"][:70].replace("\n", " ")
        print(f"  [{i}] {trail(f['path'])}   ({n} tokens){mark}")
        print(f"       \"{head}…\"")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print(f"  - {len(struct_blocks)} structural blocks -> {len(fragments)} final fragments.")
    print("  - Structure commanded: no cut crossed a heading boundary.")
    print("  - Size adjusted: only the overlong sections were subdivided.")
    print("  - Each fragment, even subdivided, KEPT its full hierarchical path.")

    print("\nWHAT TO REMEMBER")
    print("- The order of gestures: structure first, size second. Never the reverse.")
    print("- A subdivided fragment is not an orphan fragment: it keeps its address.")
    print("- This breadcrumb attached to each fragment prepares the Parent-Child chapter.")


if __name__ == "__main__":
    main()
