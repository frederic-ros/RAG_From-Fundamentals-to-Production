# ch10-vision — Scanned Documents & Multimodal Parsing

Labs for Chapter 10 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 10, which crosses the last frontier of ingestion: the documents that were never text. The five labs form a progression. You first delimit how far the OCR goes — it recognizes the characters, not the structure. You then discover that a vision model does not transcribe but interprets, by making one of Julien's wiring diagrams speak. You confront the graph paradox, where the meaning is in the form and not in the words. You make these visual sources converge toward the same document JSON as the previous chapters, then you assemble a mini Vision-RAG able to answer from images. The test documents are synthetic and reproducible; a real OCR and a local vision model are used if they are present, otherwise deterministic modes take over, without an API key.

## Labs

1. **Lab 10-1 — How far can OCR go?**
2. **Lab 10-2 — When an image becomes a scene**
3. **Lab 10-3 — The graph paradox**
4. **Lab 10-4 — From the visual document to the document JSON**
5. **Lab 10-5 — Building a mini Vision-RAG**
6. **Lab 10-6 — The other family: a shared embedding space (a toy CLIP) (bonus)**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_sample_docs.py
python lab10-1_ocr_how_far.py
```

## Dependencies

```
Pillow>=10.0.0          # generating and reading images
matplotlib>=3.7.0       # generating the test chart
scikit-learn>=1.3.0     # vector search (Lab 10-5)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
