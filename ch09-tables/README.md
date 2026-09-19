# ch09-tables — Tables, Workbooks & Structured Data

Labs for Chapter 9 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 9, the most technical of the ingestion part. It starts from a simple truth: a cell contains a value, a table contains a relation, and flattening the table destroys the relation. The six labs form a progression: you first prove the disaster of the flattening with a real vector base, you then bring Excel and CSV back to the document JSON, you explore the four representations of a table, you discover the SQL Table-RAG for the calculation questions, you measure the approaches in a quantified arena, then you assemble a mini Table-RAG that routes each question toward the good path. Three businesses serve as a through-line: Julien and his parameter tables, Sophie and her budgets, Claire and her HR tables. All the labs work without an API key, with optional engines and a local LLM.

## Labs

1. **Lab 9-1 — The disaster demonstration**
2. **Lab 9-2 — From pure data formats to the document JSON**
3. **Lab 9-3 — Four ways to represent a table**
4. **Lab 9-4 — Table-RAG: when RAG is no longer the good answer**
5. **Lab 9-5 — The structures arena: the comparative test bench**
6. **Lab 9-6 — Mini Table-RAG: the synthesis**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_sample_data.py
python lab9-1_flattening_disaster.py
```

## Dependencies

```
pandas>=2.0.0
openpyxl>=3.1.0          # reading and writing Excel
scikit-learn>=1.3.0      # TF-IDF (a lightweight vector search)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
