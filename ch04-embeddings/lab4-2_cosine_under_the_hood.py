# -*- coding: utf-8 -*-
"""
Lab 4-2 — Computing the alignment: cosine similarity under the hood

Learning objective
------------------
Implement cosine similarity by hand, and understand why it measures a direction
rather than a length.

The message to take away:

    Two vectors can have very different norms and still be perfectly aligned,
    if they point in the same direction.
"""

import numpy as np


def dot_product(u: np.ndarray, v: np.ndarray) -> float:
    """The raw dot product."""
    return float(np.dot(u, v))


def norm(u: np.ndarray) -> float:
    """The Euclidean norm."""
    return float(np.linalg.norm(u))


def cosine_similarity(u: np.ndarray, v: np.ndarray) -> float:
    """Cosine similarity, computed by hand."""
    nu = norm(u)
    nv = norm(v)

    if nu == 0 or nv == 0:
        return 0.0

    return dot_product(u, v) / (nu * nv)


def compare(name: str, u: np.ndarray, v: np.ndarray) -> None:
    """Print the dot product, the norms and the cosine for two vectors."""
    print("\n" + "=" * 78)
    print(name)
    print("=" * 78)

    print(f"u = {u}")
    print(f"v = {v}")
    print(f"norm(u) = {norm(u):.4f}")
    print(f"norm(v) = {norm(v):.4f}")
    print(f"dot product = {dot_product(u, v):.4f}")
    print(f"cosine similarity = {cosine_similarity(u, v):.4f}")


def main() -> None:
    print("=" * 78)
    print("Lab 4-2 — Cosine similarity under the hood")
    print("=" * 78)

    # The same direction, a different length.
    u = np.array([1.0, 2.0, -1.0])
    v = 10.0 * u

    # A close direction.
    w = np.array([1.2, 1.8, -0.9])

    # An almost opposite direction.
    z = np.array([-1.0, -2.0, 1.0])

    # A very long vector, but badly aligned.
    long_noise = np.array([30.0, 0.0, 0.0])

    compare("Case 1 — same direction, different length", u, v)
    compare("Case 2 — a close direction", u, w)
    compare("Case 3 — the opposite direction", u, z)
    compare("Case 4 — a large norm, weak alignment", u, long_noise)

    print("\n" + "=" * 78)
    print("INTERPRETATION")
    print("=" * 78)
    print("- The dot product grows with the size of the vectors.")
    print("- The cosine neutralises that effect of size.")
    print("- In a semantic engine, what you look for is the alignment of ideas.")
    print("- That is why cosine similarity is so widely used with embeddings.")


if __name__ == "__main__":
    main()
