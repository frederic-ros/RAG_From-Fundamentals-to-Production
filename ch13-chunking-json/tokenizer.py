# -*- coding: utf-8 -*-
"""
tokenizer.py — the shared token counting used by the Chapter 13 labs.

The chapter insists on one point: the size of a fragment is measured in TOKENS,
not in characters. This module supplies a single tokenisation function, reused by
every lab, with two implementations:

  1. tiktoken, if available and downloadable: the real tokenizer of the OpenAI
     models, the one you would use in production.
  2. a deterministic fallback otherwise: a split on words and punctuation that
     approximates the token count well enough for the labs, and works entirely
     offline.

The lab code depends ONLY on this module: it runs anywhere, and a reader who
installs tiktoken automatically gets the real count.
"""

import re
from typing import List

_ENCODER = None
_MODE = None


def _load_tiktoken():
    global _ENCODER, _MODE
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        # Actually test the encoding: it can fail at the download step.
        enc.encode("test")
        _ENCODER = enc
        _MODE = "tiktoken"
        return True
    except Exception:
        return False


# The fallback split: words, numbers and punctuation each count as ~1 token.
_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def _init():
    global _MODE
    if _MODE is not None:
        return
    if not _load_tiktoken():
        _MODE = "approx"


def mode() -> str:
    """Return the active mode: 'tiktoken' or 'approx'."""
    _init()
    return _MODE


def encoder(text: str) -> List:
    """Return the list of tokens: tiktoken integers, or substrings in fallback."""
    _init()
    if _MODE == "tiktoken":
        return _ENCODER.encode(text)
    return _PATTERN.findall(text)


def decoder(tokens: List) -> str:
    """Rebuild a text from a list of tokens."""
    _init()
    if _MODE == "tiktoken":
        return _ENCODER.decode(tokens)
    # In fallback, rejoin by putting a space before words but not before
    # clinging punctuation. A readable reconstruction, not the exact original.
    out = []
    for i, token in enumerate(tokens):
        if i > 0 and re.match(r"\w", token):
            out.append(" ")
        out.append(token)
    return "".join(out)


def count(text: str) -> int:
    """The number of tokens in a text."""
    return len(encoder(text))
