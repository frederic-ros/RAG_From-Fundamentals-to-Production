# -*- coding: utf-8 -*-
"""
contextual.py — contextualisation and the chunking "agent", offline version.

Two techniques of the chapter rely, in production, on a call to an LLM:

  - Contextual Retrieval: an LLM rewrites each chunk, adding to it a sentence of
    context drawn from the whole document;
  - the chunking agent: an LLM reads the text and decides where to cut.

So that the labs run WITHOUT an API key and with no model to download,
deterministic and explicit stand-ins are provided here:

  generate_context() — produces the context sentence of a chunk from the title
      and heading of the document. This is what an LLM would do, better; the
      function marks clearly where a real LLM would be plugged in.

  agent_chunk() — simulates an agent that places [CUT] markers according to
      simple business rules: a new article, an exception, a change of instruction.

THESE FUNCTIONS ARE NOT LLMs. They are transparent stand-ins: the teaching point
is to show the FLOW — contextualise before indexing, delegate the boundary to a
decision rather than to a length calculation — not to reproduce the finesse of a
generative model. Each function says in a comment how to replace it with a real
LLM call.
"""

from __future__ import annotations

import re
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Contextual Retrieval — generating the context sentence of a chunk
# ---------------------------------------------------------------------------
def extract_title(document: str) -> str:
    """Return the first Markdown heading of the document, its "name"."""
    for line in document.splitlines():
        if line.strip().startswith("#"):
            return line.lstrip("#").strip()
    return "technical document"


def chunk_section(chunk: str) -> str:
    """Guess the section a chunk belongs to, from its bracketed subtitle."""
    m = re.search(r"\[([^\]]+)\]", chunk)   # the form [Section title]
    if m:
        return m.group(1)
    return ""


def generate_context(chunk: str, document: str) -> str:
    """Produce the context sentence to prefix to the chunk (Contextual Retrieval).

    >>> Here a REAL system would call an LLM with a prompt of the kind:
    >>> "Here is the document: {document}. Here is a fragment: {chunk}.
    >>>  Give one sentence situating this fragment within the document."
    Our deterministic version builds that sentence from the title of the
    document and from the section, which is enough to demonstrate the
    principle: once prefixed, the fragment carries its own compass.
    """
    title = extract_title(document)
    section = chunk_section(chunk)
    if section and section.lower() not in title.lower():
        return f"[Context: {title}, section {section}.]"
    return f"[Context: {title}.]"


def contextualise(chunks: List[str], document: str) -> List[str]:
    """Prefix each chunk with its context sentence, before indexing."""
    return [f"{generate_context(c, document)} {c}" for c in chunks]


# ---------------------------------------------------------------------------
# The chunking agent — deciding boundaries by business rules
# ---------------------------------------------------------------------------
# Business markers that open a new unit of meaning in a legal or regulatory
# text (Claire's domain). A real LLM agent would generalise; these rules are
# enough to illustrate that you DECIDE, on meaning, instead of COUNTING.
_UNIT_STARTS = (
    (re.compile(r"^\s*Article\s+\d+", re.I), "new article"),
    (re.compile(r"^\s*Exception\b", re.I), "exception"),
    (re.compile(r"^\s*Clause\b", re.I), "new clause"),
)


def agent_chunk(text: str) -> List[Tuple[str, str]]:
    """Simulate an agent that segments by business logic, not by length.

    The key business rule encoded here: an EXCEPTION stays GLUED to the rule it
    qualifies, because a rule and its exception are inseparable. A new unit is
    therefore opened on "Article N", but "Exception" is ATTACHED to the unit in
    progress.

    >>> A REAL agent would receive a prompt:
    >>> "Read this text. Insert [CUT] when a new rule begins.
    >>>  Keep a rule and its exception together. Justify in three words."
    Returns a list of (segment, justification).
    """
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    segments: List[Tuple[str, str]] = []
    current: List[str] = []
    justification = "start"

    for sentence in sentences:
        start = None
        for pattern, label in _UNIT_STARTS:
            if pattern.match(sentence):
                start = label
                break

        if start == "exception":
            # An exception does NOT cut: it stays with its rule.
            current.append(sentence)
            justification = "rule + exception"
        elif start is not None and current:
            # A new article or clause: close the previous unit.
            segments.append((" ".join(current), justification))
            current = [sentence]
            justification = start
        else:
            current.append(sentence)

    if current:
        segments.append((" ".join(current), justification))
    return segments
