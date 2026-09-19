# -*- coding: utf-8 -*-
"""
Lab 19-6 (BONUS) — Optimising memory: quantisation

Learning objective
------------------
The chapter notes, in a box, that HNSW keeps both the graph AND the vectors in
main memory — expensive from a few million fragments onward. The usual answer is
QUANTISATION: compressing the vectors, for instance from 32-bit floats to 8-bit
integers. This lab implements it and measures the trade-off.

    Quantisation is a key lever for reducing production costs.

Two representations are compared:

  - float32: 4 bytes per value, full precision;
  - int8   : 1 byte per value, memory divided by four.

And what that compression costs in RECALL is checked: very little, often
invisible in the final quality. That is what makes the lever so profitable.

No API key. Reloads corpus_ref.npy.
Run generate_corpus.py first.
"""

from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"


def main() -> None:
    print("=" * 78)
    print("Lab 19-6 (BONUS) — Optimising memory: quantisation")
    print("=" * 78)

    f = DATA / "corpus_ref.npy"
    if not f.exists():
        print("\nSet not found. Run this first: python generate_corpus.py")
        return

    corpus = np.load(f).astype(np.float32)
    n, dim = corpus.shape
    print(f"\nCorpus: {n} vectors x {dim} dimensions.")

    # --- Memory ---------------------------------------------------------------
    codes, mini, scale = A.quantize_int8(corpus)
    mem_f32 = corpus.nbytes
    mem_i8 = codes.nbytes + mini.nbytes + scale.nbytes

    print("\n" + "=" * 78)
    print("1) MEMORY: float32 against int8")
    print("=" * 78)
    print(f"  float32: {mem_f32/1024:8.1f} kB  ({corpus.itemsize} bytes/value)")
    print(f"  int8   : {mem_i8/1024:8.1f} kB  (1 byte/value plus reconstruction tables)")
    print(f"  Gain   : memory divided by about {mem_f32/mem_i8:.1f}.")
    print(f"\n  Extrapolated to 10 million vectors x {dim} dim:")
    print(f"    float32: {10_000_000*dim*4/1e9:.1f} GB   |   int8: {10_000_000*dim/1e9:.1f} GB")

    # --- Recall: full precision against quantised -----------------------------
    approx = A.dequantize_int8(codes, mini, scale)

    rng = np.random.default_rng(606)
    qids = rng.choice(n, 100, replace=False)
    queries = corpus[qids] + rng.normal(0, 0.08, (100, dim))

    recalls = []
    for q in queries:
        ex_f32, _ = A.exact_search(corpus, q, k=10)   # the truth, at full precision
        ex_i8, _ = A.exact_search(approx, q, k=10)    # search on the quantised vectors
        recalls.append(A.recall(ex_i8, ex_f32))
    # The mean reconstruction error, as a cosine gap.
    sims = np.sum(corpus * approx, axis=1)
    mean_error = float(np.mean(1 - sims))

    print("\n" + "=" * 78)
    print("2) THE COST IN QUALITY: almost nothing")
    print("=" * 78)
    print(f"  Mean reconstruction error (1 - cosine): {mean_error:.6f}")
    print(f"  Recall of the neighbours found on int8 against float32: {np.mean(recalls):.1%}")
    print(f"  -> On average {np.mean(recalls)*10:.1f} of the 10 true neighbours are found,")
    print("     with four times less memory.")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("- Moving from float32 to int8 divides memory by about 4, with almost no recall lost.")
    print("- The precision lost on each vector is tiny, and dilutes in the search:")
    print("  the good neighbours stay the good neighbours.")
    print("- At scale, this lever transforms the infrastructure budget (RAM).")

    print("\nWHAT TO REMEMBER")
    print("- Quantisation compresses the vectors: less memory, therefore less cost.")
    print("- The trade-off is no longer recall against latency but recall against MEMORY —")
    print("  and it is often very favourable.")
    print("- It is a production setting in its own right, alongside ef_search and M.")


if __name__ == "__main__":
    main()
