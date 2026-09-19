# ch19-ann-hnsw — Searching Fast at Scale: Approximate Search

Labs for Chapter 19 of *RAG — From Fundamentals to Production*.

This companion chapter extends chapter 19, which makes the dense retrieval realistic at the scale of a real corpus: no longer searching better, but searching fast when the vectors count in the millions. The six labs follow the rise of the chapter, from the problem toward the tool. You start from the wall of exact search, its latency grows linearly with the corpus, until becoming seconds per query beyond the prototype (Lab 19-1). You then accept a fruitful renunciation: searching approximately to go hundreds of times faster, by measuring the saving of computations against the preserved quality (Lab 19-2). You open the hood of the structure that dominates today, HNSW, by building a small layered graph and tracing the traversal of a query, from the long highway jumps to the local streets (Lab 19-3). You then set the central dial, ef\_search, to see, with your own eyes, the recall/latency compromise and its saturation point (Lab 19-4). You finally choose a production strategy according to the business constraints: Julien optimizes the latency, Sophie the recall, same corpus, opposite settings, both legitimate (Lab 19-5). A bonus lab adds the lever of quantization: dividing the memory by four almost without loss of recall (Lab 19-6). A second bonus lab builds the other major ANN family, IVF: partition instead of navigate, a k-means directory of neighborhoods whose own dial, n\_probe, is compared side by side with HNSW's (Lab 19-7). The through-line follows Julien (maintenance) and Sophie (regulatory). All the code is in pure NumPy, deterministic, instrumented to make the HNSW navigation transparent: it counts the computed distances and exposes the layers of the graph. No API key, no network, you learn the principle of the ANN, not a library that will become obsolete.

## Labs

1. **Lab 19-1 — The wall of the million vectors**
2. **Lab 19-2 — Finding the house without visiting all the streets**
3. **Lab 19-3 — Building a mini-HNSW by hand**
4. **Lab 19-4 — The magic dial: recall vs speed**
5. **Lab 19-5 — Julien goes to production**
6. **Lab 19-6 — Optimizing the memory: quantization (bonus)**
7. **Lab 19-7 — The other family: cluster-based search (IVF) (bonus)**

## Running them

Generate the local data first, then run any lab:

```bash
python generate_corpus.py
python lab19-1_exact_search_wall.py
```

## Shared modules

Imported by the labs of this chapter, not meant to be run on their own:

- `annlib.py`

## Dependencies

```
numpy>=1.24.0          # vectors and linear algebra (core dependency for all labs)
```

Or install everything at once from the repository root:

```bash
pip install -r requirements-all.txt
```

No API key is ever required: every corpus is generated locally and deterministically, and every lab runs offline.
