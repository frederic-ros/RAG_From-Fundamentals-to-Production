# ch13-chunking-json — Chunking from a Canonical JSON

Labs for Chapter 13 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 13, the hinge of the structuring part. It does not introduce a new technique: it anchors a discipline, a single but decisive one — you never cut the raw file, you cut what you have reconstructed from it. The four labs form a tightened progression around a same document. You start from the gesture that fails: unleashing a fixed-size cutter on a flattened text, riddled with repeated headers, parasitic page numbers, and a crushed table. You repair by starting from the reconstructed document JSON, where the fragment becomes clean and situated again. You then put the two pipelines face to face, with a strictly equal chunker, to measure the gap. A last lab, optional, opens toward what follows: the hierarchical structural cutting, where the structure commands and the size adjusts, without any fragment losing its address. The through-line is held by Claire and her HR note, in continuity with chapter 12. All the labs measure the size in tokens via the shared module, with tiktoken if it is present and a deterministic fallback otherwise, without an API key.

## Labs

1. **Lab 13-1 — Cutting a raw document: why it fails**
2. **Lab 13-2 — The same document after reconstruction**
3. **Lab 13-3 — Comparing the two pipelines**
4. **Lab 13-4 — Hierarchical structural chunking**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab13-1_split_raw_text.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `tokenizer.py`

## Dependencies

```
scikit-learn>=1.3.0    # recherche TF-IDF (Lab 13-1, 13-2, 13-3)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
