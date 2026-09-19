# -*- coding: utf-8 -*-
"""
Lab 11-4 — The local/web router: choosing your source (the first agentic step)

Learning objective
------------------
A RAG system may have several sources at hand: an internal corpus (stable,
governed) and web sources (fresh, volatile). Rather than submit to its sources,
the system CHOOSES between them according to the question. This is the first
step towards agentic behaviour.

    A question about an internal procedure -> the internal corpus.
    A question demanding freshness ("2026", "latest version") -> the web.

The router is deliberately simple, deterministic and explainable: it analyses the
question, decides, and JUSTIFIES its choice. No decision is opaque.

A NOTE ON THE CUE LISTS. The two lists below ARE the mechanism. They are matched
against the text of the question, so they must be written in the language the
reader will actually type. Translating the questions and leaving the cues in
French would make the router match nothing and route everything to the default.

No API key. Reuses, conceptually, Labs 11-2 and 11-3 for the web route.
Run generate_fixtures.py first.
"""

from pathlib import Path
from typing import Dict, Tuple

FIX = Path(__file__).resolve().parent / "fixtures"

# Cues that lean towards the WEB: a need for freshness.
WEB_CUES = [
    "2025", "2026", "latest version", "most recent", "up to date", "up-to-date",
    "currently", "today", "recent", "new", "reform", "current rate",
    "in force", "news",
]
# Cues that lean towards the INTERNAL corpus: stable, governed.
INTERNAL_CUES = [
    "procedure", "manual", "policy", "internal", "datasheet", "handbook",
    "how do i configure", "how to configure", "instructions", "staff rules",
]


def route_question(question: str) -> Dict:
    """Decide the source and justify it. Returns {source, justification, scores}."""
    q = question.lower()
    web_score = sum(1 for cue in WEB_CUES if cue in q)
    internal_score = sum(1 for cue in INTERNAL_CUES if cue in q)

    web_hits = [cue for cue in WEB_CUES if cue in q]
    internal_hits = [cue for cue in INTERNAL_CUES if cue in q]

    if web_score > internal_score:
        source = "web"
        justification = f"freshness cues detected: {', '.join(web_hits)}"
    elif internal_score > web_score:
        source = "internal"
        justification = f"internal-content cues: {', '.join(internal_hits)}"
    else:
        # A tie, or no cue at all: the internal corpus is preferred, being
        # governed and reliable, and a web fallback remains possible.
        source = "internal"
        justification = ("no dominant freshness cue; by default the governed "
                         "internal corpus is queried")
    return {
        "source": source,
        "justification": justification,
        "scores": {"web": web_score, "internal": internal_score},
    }


# Simulated answers from the two sources, for a demonstration with no network.
def answer_internal(question: str) -> str:
    return "[Internal corpus] The procedure is described in internal manual v2.1."


def answer_web(question: str) -> str:
    return "[Web — official portal, 2026] The rate in force is 4.7% since June 2026."


def process(question: str) -> Tuple[str, Dict]:
    decision = route_question(question)
    answer = answer_web(question) if decision["source"] == "web" else answer_internal(question)
    return answer, decision


def main() -> None:
    print("=" * 78)
    print("Lab 11-4 — The local/web router: choosing your source (the first agentic step)")
    print("=" * 78)

    questions = [
        "What is the procedure for approving a file?",
        "What is the compliance rate in force in 2026?",
        "What is the latest version of the drive datasheet?",
        "How do I configure the internal server?",
        "What is the company HR policy?",
    ]

    print("\n" + "=" * 78)
    print("THE ROUTER IN ACTION")
    print("=" * 78)
    for question in questions:
        answer, decision = process(question)
        print(f"\nQ: {question}")
        print(f"   routed to: {decision['source'].upper()}  "
              f"(web={decision['scores']['web']}, internal={decision['scores']['internal']})")
        print(f"   why      : {decision['justification']}")
        print(f"   answer   : {answer}")

    print("\n" + "=" * 78)
    print("WHY THIS IS A FIRST AGENTIC STEP")
    print("=" * 78)
    print("- The system no longer submits to one source: it chooses, and explains.")
    print("- The decision is transparent: you can see the cues that drove it.")
    print("- This is the seed of an agent: analyse, decide, justify, act.")

    print("\nWHAT TO REMEMBER")
    print("- Routing by cues: freshness -> the web; governed content -> the internal corpus.")
    print("- On a tie, the internal source wins, being reliable — a choice, not an accident.")
    print("- A good router always cites its source: traceability is what builds trust.")


if __name__ == "__main__":
    main()
