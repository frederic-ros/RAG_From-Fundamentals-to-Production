# -*- coding: utf-8 -*-
"""
tokenizer.py — token counting, shared by the labs of Chapter 12.

The chapter insists on one point: a fragment is measured in TOKENS, not in
characters. This module provides a single tokenisation function, reused by
every lab, with two implementations:

  1. tiktoken, if it is available and can be downloaded: the real tokenizer of
     the OpenAI models, the one you would use in production.
  2. a deterministic fallback otherwise: a split on words and punctuation that
     approximates the token count closely enough for the labs, and works fully
     offline.

The lab code depends only on this module: it runs anywhere, and a reader who
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
        # Actually exercise the encoding: it can fail while downloading.
        enc.encode("test")
        _ENCODER = enc
        _MODE = "tiktoken"
        return True
    except Exception:
        return False


# Fallback split: words, numbers and punctuation each count as about one token.
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


def encode(text: str) -> List:
    """Return the list of tokens (tiktoken integers, or substrings in fallback)."""
    _init()
    if _MODE == "tiktoken":
        return _ENCODER.encode(text)
    return _PATTERN.findall(text)


def decode(tokens: List) -> str:
    """Rebuild a text from a list of tokens."""
    _init()
    if _MODE == "tiktoken":
        return _ENCODER.decode(tokens)
    # In fallback mode we rejoin by reinserting a space before words, but not
    # before clinging punctuation. This is a readable reconstruction, not the
    # exact original.
    out = []
    for i, token in enumerate(tokens):
        if i > 0 and re.match(r"\w", token):
            out.append(" ")
        out.append(token)
    return "".join(out)


def count(text: str) -> int:
    """Number of tokens in a text."""
    return len(encode(text))
