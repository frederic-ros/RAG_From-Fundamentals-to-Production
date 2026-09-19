# ch31-security-governance — Security & data governance: watertightness, trust and autonomy tiers

Labs for Chapter 31 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 31, which armors a production RAG on three inseparable fronts: the watertightness, the trust, and the autonomy. The thesis holds in one sentence: no safeguard replaces the architecture, the real defense is structural. The four labs unroll it. You start with the perimeter: an input classifier catches the instruction hijackings, a scanner quarantines the documents carrying hidden instructions before indexing, and an output safeguard redacts the leaks (Lab 31-1). You then secure the index itself: the attribute filtering (ABAC) applies to the retrieval, before generation, and the metadata governance (status, expiration, trust) sets aside the outdated, no fragment out of clearance ever reaches the model (Lab 31-2). You then frame the passage from saying to doing: four autonomy levels route each request, the jump toward the action imposes a human validation, and everything is logged in an unforgeable hash chain (Lab 31-3). You finally prove the end-to-end auditability: complete logging, session replay, dashboard, and post-incident analysis that reconstitutes the causal chain from the logs alone (Lab 31-4). The through-line follows Julien (maintenance) and Karim (technician), with a defense incursion by Jean-Claude (officer) for the clearance. Without an API key: deterministic TF-IDF retrieval (or sentence-transformers), detection by rules (or a local LLM via Ollama, for example Mistral), the thesis staying visible, offline and reproducible.

## Labs

1. **Lab 31-1 — Anti-injection firewall: direct and indirect**
2. **Lab 31-2 — Securing the index: ABAC and governance metadata**
3. **Lab 31-3 — Autonomy levels and traceability**
4. **Lab 31-4 — Complete audit: logging and post-incident analysis**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab31-1_injection_firewall.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `secukit.py`

## Dependencies

```
numpy>=1.24.0          # vectors and metrics
scikit-learn>=1.3.0    # TF-IDF (mode hors-ligne)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
