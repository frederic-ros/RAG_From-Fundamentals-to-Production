# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test vector sets of Chapter 19.

The labs of this chapter do not work on text but on VECTORS: that is the level
where approximate search lives. To stay reproducible and offline, no real
embeddings are computed — deterministic vectors are generated that imitate their
geometry: clusters, the way documents close in meaning group together in a real
corpus.

This script writes several sets of increasing size into the `data/` folder, in
NumPy .npy format. Every lab reloads them, so two runs give exactly the same
figures.

    corpus_1k.npy  —  1,000 vectors (warm-up)
    corpus_5k.npy  —  5,000 vectors
    corpus_20k.npy — 20,000 vectors
    corpus_50k.npy — 50,000 vectors (where the "wall" becomes noticeable)
    corpus_ref.npy —  4,000 vectors (the reference set for Labs 3 to 6)

Run before the labs: python generate_corpus.py
No API key, no network.
"""

from pathlib import Path

import numpy as np

import annlib as A

DATA = Path(__file__).resolve().parent / "data"
DATA.mkdir(exist_ok=True)


# The sizes for the "wall" labs: the latency of exact search.
SIZES = {
    "corpus_1k.npy": 1_000,
    "corpus_5k.npy": 5_000,
    "corpus_20k.npy": 20_000,
    "corpus_50k.npy": 50_000,
}


def main() -> None:
    print("Generating the Chapter 19 vector sets:")

    # Sets of increasing size: the same clusters, more or fewer points.
    for name, n in SIZES.items():
        vectors = A.generate_corpus(n, dim=64, n_clusters=10, seed=3)
        np.save(DATA / name, vectors)
        mb = vectors.nbytes / (1024 * 1024)
        print(f"  + {name:16s} {n:6d} vectors x 64 dim  ({mb:.1f} MB)")

    # The reference set for Labs 3 to 6, at a validated teaching setting.
    ref = A.generate_corpus(4_000, dim=64, n_clusters=10, seed=3)
    np.save(DATA / "corpus_ref.npy", ref)
    print(f"  + {'corpus_ref.npy':16s} {ref.shape[0]:6d} vectors x 64 dim  (reference)")

    print(f"\nDone. Sets available in: {DATA}")
    print("A tip: the labs reload these files; rerun this script if you delete them.")


if __name__ == "__main__":
    main()
