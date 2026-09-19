# ch06-ingestion — The Challenge of Real Documents: Document Transformation

Labs for Chapter 6 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 6 of the book. It begins a technical turn: how does the machine really read a document? The labs follow the parsing levels, from raw text to multimodal by vision, up to the Smart Parser. You start with Claire and her multi-format documents, you fall with Julien into the trap of the flattened tables, you disentangle with Sophie a public procurement contract on two columns, you submit to Julien an equipment nameplate to a vision model, then you assemble the whole into a Sparser that enriches the ingestion with metadata. The test documents are synthetic and reproducible; the multimodal labs work offline by default, with an optional and free connection to a local model.

## Labs

1. **Lab 6-1 — From the multi-format document to the document JSON**
2. **Lab 6-2 — The flattened-table trap**
3. **Lab 6-3 — Reading order and noise cleaning**
4. **Lab 6-4 — Multimodal parsing by vision (VLM)**
5. **Lab 6-5 — A metadata-augmented "Sparser"**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_sample_docs.py
python lab6-1_multiformat_to_json.py
```

## Dependencies

```
python-docx>=1.1.0
beautifulsoup4>=4.12.0
pypdf>=4.0.0
pdfplumber>=0.11.0
reportlab>=4.0.0
Pillow>=10.0.0
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
