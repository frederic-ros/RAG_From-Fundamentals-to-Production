# ch08-office-documents — Office Documents: Word, PDF, Presentations

Labs for Chapter 8 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 8 of the book. It answers the concrete question: how do you bring a Word, a PDF, a presentation into the system? Each lab takes a format and brings it back to the same pivot document JSON, then to chunks. You first read the declared structure of a Word, you geometrically reconstruct the reading order of a two-column PDF, you recover the hidden notes of a presentation, then you make the three formats converge into a single corpus that you cut the same way whatever the source. The chapter culminates on a difficulty that is no longer of extraction but of governance: the same remote-work agreement exists in three divergent versions, and you must decide which one is authoritative. The test documents are synthetic and reproducible; the conflict detector works without an API key, with an optional local LLM.

## Labs

1. **Lab 8-1 — Word extraction: from native style to JSON tree**
2. **Lab 8-2 — The recalcitrant PDF: geometric reconstruction**
3. **Lab 8-3 — Slide and presenter notes**
4. **Lab 8-4 — The convergence workshop: semantic fusion**
5. **Lab 8-5 — The conflict detector: arbitrating between versions**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_sample_docs.py
python lab8-1_word_to_tree.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `chunking.py`

## Dependencies

The Python standard library only.

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
