# -*- coding: utf-8 -*-
"""
Lab 10-6 (BONUS) -- The other family: a shared embedding space (a toy CLIP)

Learning objective
-------------------
Every other lab in this chapter takes the same road: a vision model DESCRIBES
an image in words, and that description is then embedded and searched like
any other text. This lab builds the other road: a SHARED vector space where
an image and a text query are placed side by side directly, with no
description step in between, and compared by plain cosine similarity. This
is the mechanism behind CLIP-style cross-modal search (Radford et al., 2021):
"find the image closest to this text" without ever generating a caption.

Honesty check, up front
------------------------
Training a real CLIP-style encoder needs hundreds of millions of (image,
text) pairs and heavy contrastive learning -- well outside what a
deterministic, offline, no-API-key lab can build. So the "image encoder"
below is a stand-in: each photo is represented not by its pixels, but by a
small set of ground-truth visual tags (as if a human, or a real vision
encoder, had already labelled its content). What THIS lab shows, honestly,
is the downstream mechanism -- one shared space, cosine similarity, search in
both directions -- not the perceptual step that a real encoder would add
before it.

No API key. No network. Fully deterministic.
"""

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# 1. The toy corpus: Julien's equipment photos, as ground-truth visual tags
# ---------------------------------------------------------------------------
# In a real CLIP-style pipeline these tags would never be written by hand:
# a contrastively-trained image encoder would place the *pixels* directly in
# the shared space. Here they stand in for "what the image contains", so the
# lab can focus on what happens once both modalities share one space.
PHOTOS: Dict[str, Dict] = {
    "photo_01": {"label": "Line-4 pump, rust stain on the housing",
                 "tags": {"pump", "rust", "line4", "housing", "worn"}},
    "photo_02": {"label": "Line-4 control panel, red warning light on",
                 "tags": {"panel", "red", "warning_light", "line4", "electrical"}},
    "photo_03": {"label": "Turbine blade, hairline crack near the tip",
                 "tags": {"turbine", "blade", "crack", "metal", "worn"}},
    "photo_04": {"label": "New pump, clean housing, no corrosion",
                 "tags": {"pump", "housing", "new", "clean"}},
    "photo_05": {"label": "Motor M-18, oil leak on the base plate",
                 "tags": {"motor", "oil", "leak", "base_plate", "m18"}},
    "photo_06": {"label": "Control panel, green indicator, all normal",
                 "tags": {"panel", "green", "normal", "electrical"}},
    "photo_07": {"label": "Turbine housing, fresh coat of paint, no damage",
                 "tags": {"turbine", "housing", "new", "clean", "paint"}},
    "photo_08": {"label": "Line-4 pump, red warning sticker on the valve",
                 "tags": {"pump", "red", "warning_sticker", "line4", "valve"}},
}

# The rules a real encoder replaces: mapping words a user might type onto the
# same tag vocabulary the photos are described with. Deliberately simple and
# rule-based, exactly like the query-rewriting stand-ins of Chapter 21 --
# the point here is the shared space, not a language model.
QUERY_TO_TAGS = {
    "pump": {"pump"}, "pumps": {"pump"},
    "rust": {"rust"}, "rusty": {"rust"}, "corrosion": {"rust"},
    "red": {"red"}, "warning": {"warning_light", "warning_sticker"},
    "panel": {"panel"}, "electrical": {"electrical"},
    "turbine": {"turbine"}, "blade": {"blade"}, "crack": {"crack"}, "cracked": {"crack"},
    "new": {"new"}, "clean": {"clean"},
    "motor": {"motor"}, "oil": {"oil"}, "leak": {"leak"}, "leaking": {"leak"},
    "green": {"green"}, "normal": {"normal"},
    "line": {"line4"}, "4": {"line4"},
    "valve": {"valve"}, "sticker": {"warning_sticker"}, "light": {"warning_light"},
    "worn": {"worn"}, "damage": {"crack", "worn"}, "damaged": {"crack", "worn"},
}


# ---------------------------------------------------------------------------
# 2. The shared space: every tag is one axis, images and text are points
# ---------------------------------------------------------------------------
def vocabulary() -> List[str]:
    """All tags used anywhere in the corpus: the axes of the shared space."""
    vocab = set()
    for photo in PHOTOS.values():
        vocab |= photo["tags"]
    return sorted(vocab)


def encode_tags(tags: set, vocab: List[str]) -> List[float]:
    """Project a set of tags into the shared space: one axis per vocabulary
    tag, 1.0 if present. Both a photo and a text query go through this exact
    same function -- there is no separate "image space" and "text space"."""
    return [1.0 if t in tags else 0.0 for t in vocab]


def encode_query(question: str) -> set:
    """Stand-in for a text encoder: turn free text into the same tag
    vocabulary the photos use, via simple keyword matching."""
    tags = set()
    for word in question.lower().replace(",", " ").replace(".", " ").split():
        tags |= QUERY_TO_TAGS.get(word, set())
    return tags


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# 3. Cross-modal search, in both directions
# ---------------------------------------------------------------------------
def search_photos(question: str, vocab: List[str], k: int = 3) -> List[Tuple[str, float]]:
    """Text -> image: the classic CLIP demo, "find the photo for this query"."""
    q_vec = encode_tags(encode_query(question), vocab)
    scored = []
    for photo_id, photo in PHOTOS.items():
        p_vec = encode_tags(photo["tags"], vocab)
        scored.append((photo_id, cosine(q_vec, p_vec)))
    return sorted(scored, key=lambda x: -x[1])[:k]


def search_captions(photo_id: str, candidate_captions: List[str], vocab: List[str]) -> List[Tuple[str, float]]:
    """Image -> text: the reverse direction, "find the caption for this photo".
    A pure text-search pipeline (Lab 10-5's approach) cannot do this at all
    without first re-describing the image -- here it falls out for free,
    because both modalities already live in the same space."""
    p_vec = encode_tags(PHOTOS[photo_id]["tags"], vocab)
    scored = []
    for caption in candidate_captions:
        c_vec = encode_tags(encode_query(caption), vocab)
        scored.append((caption, cosine(p_vec, c_vec)))
    return sorted(scored, key=lambda x: -x[1])


def main() -> None:
    print("=" * 78)
    print("Lab 10-6 (BONUS) -- The other family: a shared embedding space (a toy CLIP)")
    print("=" * 78)

    vocab = vocabulary()
    print(f"\n{len(PHOTOS)} photos, {len(vocab)} shared tags forming the axes of the space.")

    print("\n" + "=" * 78)
    print("1) TEXT -> IMAGE: search photos directly from a text query")
    print("=" * 78)
    queries = [
        "red warning light on a line 4 panel",
        "rusty pump housing",
        "cracked turbine blade",
    ]
    for q in queries:
        results = search_photos(q, vocab, k=2)
        print(f'\n  Query: "{q}"')
        for photo_id, score in results:
            print(f"    {photo_id}  (score {score:.2f})  -- {PHOTOS[photo_id]['label']}")

    print("\n" + "=" * 78)
    print("2) IMAGE -> TEXT: the reverse direction, for free in a shared space")
    print("=" * 78)
    candidate_captions = [
        "Everything is normal, no action needed.",
        "Corrosion detected, schedule a replacement.",
        "Electrical fault, red light active, inspect immediately.",
        "Structural crack found, stop the equipment.",
    ]
    for photo_id in ("photo_01", "photo_02", "photo_03"):
        ranked = search_captions(photo_id, candidate_captions, vocab)
        print(f"\n  Photo {photo_id} -- {PHOTOS[photo_id]['label']}")
        print(f'    best matching caption: "{ranked[0][0]}" (score {ranked[0][1]:.2f})')

    print("\n" + "=" * 78)
    print("3) WHAT THIS COSTS, COMPARED TO Lab 10-5's describe-then-embed PIPELINE")
    print("=" * 78)
    print("- Lab 10-5 needs a vision-model call to describe every image BEFORE it")
    print("  can be searched at all -- the description is the whole basis of the")
    print("  index. Here, once the shared space exists, a text query compares")
    print("  directly to the image's representation: no description step at")
    print("  query time.")
    print("- The price is elsewhere: Lab 10-5's descriptions integrate for free")
    print("  with everything the rest of the book builds (lexical search,")
    print("  hybrid search, the document JSON). A shared embedding space needs")
    print("  its own dedicated multimodal index, and does not blend as naturally")
    print("  with keyword-based search.")
    print("- Lab 10-5's output is a sentence you can read and audit. A shared-space")
    print("  match is a similarity score: harder to explain to Sophie why one")
    print("  photo ranked above another.")

    print("\nKEY TAKEAWAYS")
    print("- A shared embedding space places images and text as points in the")
    print("  SAME geometry, so cosine similarity compares them directly, in")
    print("  either direction, without ever generating a caption.")
    print("- This lab's 'encoder' is hand-built tags standing in for pixels --")
    print("  a real encoder learns this space from hundreds of millions of")
    print("  (image, text) pairs by contrastive training, not keyword rules.")
    print("- Neither road is strictly better: describe-then-embed (Lab 10-5) stays")
    print("  explainable and reuses the book's whole text pipeline; a shared")
    print("  space (this lab) skips the description step but asks for its own")
    print("  infrastructure and is harder to audit.")
    print("- Reference: Radford et al. (2021), Learning Transferable Visual")
    print("  Models From Natural Language Supervision (CLIP), ICML.")


if __name__ == "__main__":
    main()
