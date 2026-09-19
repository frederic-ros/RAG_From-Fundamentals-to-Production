# -*- coding: utf-8 -*-
"""
Lab 4-3 — Visualising the map of meaning in 2D, with PCA

Learning objective
------------------
Show that sentences can form semantic "neighbourhoods" inside a vector space.

To avoid any dependency on a model download, the lab uses teaching embeddings
built from thematic prototypes:

  - animals;
  - computing;
  - human resources.

The plot produced is saved to:

    map_of_meaning_pca.png

A note on robustness
--------------------
The matplotlib "Agg" backend is forced (file rendering, no graphical interface),
so that the script runs anywhere: a server, CI, a notebook, or a machine with no
screen. The embeddings are deterministic: the map is identical from one run to
the next.
"""

from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")  # a non-interactive backend: no display required
import matplotlib.pyplot as plt  # noqa: E402 (after matplotlib.use)
import numpy as np  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402


PHRASES: List[Tuple[str, str]] = [
    ("Animals", "The domestic cat likes to hunt mice."),
    ("Animals", "The dog barks when the postman approaches."),
    ("Animals", "The tiger is a solitary feline of the Asian forests."),
    ("Animals", "The rabbit hides in its burrow."),

    ("Computing", "The Linux server reboots after the update."),
    ("Computing", "The Python code raises a KeyError exception."),
    ("Computing", "The database uses SQL indexes."),
    ("Computing", "The Kubernetes cluster deploys several containers."),

    ("HR", "The head of human resources organises the annual reviews."),
    ("HR", "The employment contract provides for a probationary period."),
    ("HR", "Paid leave requests are approved on the portal."),
    ("HR", "Internal training supports the growth of skills."),
]


CATEGORY_PROTOTYPES: Dict[str, np.ndarray] = {
    "Animals": np.array([1.0, 0.0, 0.0, 0.2, 0.1]),
    "Computing": np.array([0.0, 1.0, 0.0, 0.1, 0.3]),
    "HR": np.array([0.0, 0.0, 1.0, 0.3, 0.1]),
}

EMBEDDING_DIM = 5
OUTPUT_FILE = Path(__file__).resolve().parent / "map_of_meaning_pca.png"


def deterministic_noise(text: str, dim: int = EMBEDDING_DIM) -> np.ndarray:
    """Create a small deterministic noise, to avoid points landing on top of
    one another.

    The seed depends on the text: the same sentence gives the same noise, so the
    map is reproducible.
    """
    seed = sum(ord(c) for c in text)
    rng = np.random.default_rng(seed)
    return rng.normal(loc=0.0, scale=0.06, size=dim)


def build_embeddings() -> np.ndarray:
    """Build the teaching embeddings, by category."""
    vectors: List[np.ndarray] = []

    for category, phrase in PHRASES:
        if category not in CATEGORY_PROTOTYPES:
            raise KeyError(f"Category with no prototype: {category!r}")
        vector = CATEGORY_PROTOTYPES[category] + deterministic_noise(phrase)
        vectors.append(vector)

    return np.vstack(vectors)


def main() -> None:
    print("=" * 78)
    print("Lab 4-3 — Visualising the map of meaning in 2D")
    print("=" * 78)

    labels = [category for category, _ in PHRASES]
    texts = [phrase for _, phrase in PHRASES]
    embeddings = build_embeddings()

    print(f"Number of sentences: {len(texts)}")
    print(f"Initial dimension of the vectors: {embeddings.shape[1]}")

    pca = PCA(n_components=2)
    points_2d = pca.fit_transform(embeddings)

    print(f"Variance explained by the 2 PCA axes: {pca.explained_variance_ratio_.sum():.2%}")

    style_by_label = {
        "Animals": {"marker": "o", "color": "#1E6BA8"},
        "Computing": {"marker": "s", "color": "#2A7F62"},
        "HR": {"marker": "^", "color": "#D9822B"},
    }

    plt.figure(figsize=(11, 8))

    # A fixed marker AND a fixed colour per category: the legend stays honest,
    # and the plot survives being printed in greyscale.
    seen_labels = set()
    for i, (x, y) in enumerate(points_2d):
        label = labels[i]
        style = style_by_label[label]
        legend = label if label not in seen_labels else None
        seen_labels.add(label)
        plt.scatter(x, y, s=90, marker=style["marker"], color=style["color"], label=legend)
        plt.text(x + 0.02, y + 0.02, f"{label} — {texts[i][:38]}...", fontsize=8)

    plt.title("The map of meaning in 2D — a PCA projection")
    plt.xlabel("Principal component 1")
    plt.ylabel("Principal component 2")
    plt.legend(title="Semantic neighbourhood", loc="best")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.tight_layout()

    plt.savefig(OUTPUT_FILE, dpi=160)
    plt.close()

    print(f"Plot saved to: {OUTPUT_FILE}")

    print("\nWHAT TO REMEMBER")
    print("- Sentences on the same theme cluster together in the space.")
    print("- PCA does not create meaning: it projects a vector space into 2D.")
    print("- Geometric neighbourhood becomes a visual intuition of semantic retrieval.")


if __name__ == "__main__":
    main()
