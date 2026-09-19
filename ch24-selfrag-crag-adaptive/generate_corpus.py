# -*- coding: utf-8 -*-
"""
generate_corpus.py — the test corpus of Chapter 24 (Self-RAG, CRAG, Adaptive).

A deterministic corpus with DELIBERATE GAPS, so that the three mechanisms of the
chapter have something to bite on:

  - Self-RAG must DOUBT where the fragments are weak;
  - CRAG must FALL BACK on the (simulated) web where the corpus says nothing;
  - Adaptive-RAG must ROUTE by complexity: direct, simple, iterative.

The gaps are wired in: pump P-99, the heatwave and agency workers question, and
the corrosive-environment lubricant are all absent from the corpus.

A NOTE ON THE ROUTING. Each query carries an `expected_route`. The router of
cragkit.py decides from word lists (analysis markers, factual markers, business
entity markers) which must be kept in step with these questions. Lab 24-4 prints
the decision against the expectation for all nine: run it after any edit.

One trap to keep in mind: "summarise" must NOT be an analysis marker, or query 4
would be routed to the iterative path. The French "Résume" was outside the list
for the same reason.

Run before the labs: python generate_corpus.py
"""

import json
from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


FRAGMENTS = [
    # --- Maintenance (Julien) — well covered ---------------------------------
    {"id": 0, "subject": "stop-P12",
     "text": "Emergency stop procedure for pump P-12: cut the supply at the main "
             "isolator, close the suction valve, then purge the circuit. "
             "Immobilisation in thirty seconds."},
    {"id": 1, "subject": "stop-P42",
     "text": "Emergency stop procedure for pump P-42: hit the mushroom button, "
             "isolate the discharge circuit and lock off the equipment. Hydraulic "
             "brake: a stop in five seconds."},
    {"id": 2, "subject": "reference-P42",
     "text": "Pump P-42 carries the manufacturer reference HX-420; it belongs to "
             "the high-pressure centrifugal range of the workshop."},
    {"id": 3, "subject": "overheating-M18",
     "text": "Overheating of motor M-18: check the ventilation flow, the condition "
             "of the bearings and the mechanical load; clean the fins of the heat "
             "sink."},
    # --- HR (Claire) — partially covered -------------------------------------
    {"id": 4, "subject": "remote-permanent",
     "text": "Remote work for permanent staff: up to three days a week after six "
             "months of service, subject to the manager's approval."},
    {"id": 5, "subject": "long-service-bonus",
     "text": "Long-service bonus: paid after three years of effective presence, "
             "calculated under the collective agreement."},
    # --- Architecture (Sophie) -----------------------------------------------
    {"id": 6, "subject": "rag-vs-finetuning",
     "text": "RAG and fine-tuning answer distinct needs: RAG injects fresh "
             "knowledge without retraining, fine-tuning adjusts the style and the "
             "behaviour of the model."},
    {"id": 7, "subject": "embeddings",
     "text": "An embedding represents a text by a dense vector; vector proximity "
             "approximates proximity of meaning, but not exact relevance."},
    # --- Thematic decoys -----------------------------------------------------
    {"id": 8, "subject": "decoy-safety",
     "text": "General safety procedure: wearing protective equipment and "
             "respecting the access instructions for the machine areas."},
    {"id": 9, "subject": "decoy-maintenance",
     "text": "Preventive maintenance schedule: quarterly lubrication and an annual "
             "check on the sealing of the circuits."},
    {"id": 10, "subject": "decoy-leave",
     "text": "Booking paid leave depends on length of service and on the reference "
             "period defined by the company."},
    {"id": 11, "subject": "decoy-valves",
     "text": "The isolation valves are checked annually, to guarantee their "
             "sealing and their operability."},
]


QUERIES = [
    # DIRECT — trivial or factual (Adaptive: ideally no retrieval).
    {"question": "What is the reference of pump P-42?",
     "relevant": [2], "expected_route": "simple", "expected_grade": "confident"},
    {"question": "What is today's date?",
     "relevant": [], "expected_route": "direct", "expected_grade": "not_confident"},
    # SIMPLE — one pass is enough.
    {"question": "What is the emergency stop procedure for pump P-12?",
     "relevant": [0], "expected_route": "simple", "expected_grade": "confident"},
    # NOTE: "Summarise" must not be an analysis marker, or this goes iterative.
    {"question": "Summarise the emergency stop procedure of pump P-42.",
     "relevant": [1], "expected_route": "simple", "expected_grade": "confident"},
    # ITERATIVE — complex, multi-facet.
    {"question": "Analyse the possible causes of overheating in motor M-18 and "
                 "their consequences for production.",
     "relevant": [3], "facets": ["ventilation", "bearings", "load"],
     "expected_route": "iterative", "expected_grade": "ambiguous"},
    {"question": "Compare the emergency stop procedures of pumps P-12 and P-42.",
     "relevant": [0, 1], "facets": ["P-12", "P-42"],
     "expected_route": "iterative", "expected_grade": "ambiguous"},
    # NOT CONFIDENT — outside the corpus, so a web fallback (CRAG).
    {"question": "What are the employer's obligations for agency workers "
                 "during a heatwave?",
     "relevant": [], "expected_route": "simple", "expected_grade": "not_confident",
     "expected_web": "web-heatwave-agency-workers"},
    {"question": "What is the emergency stop procedure for pump P-99?",
     "relevant": [], "expected_route": "simple", "expected_grade": "not_confident",
     "expected_web": "web-p99-specs"},
    # RARE or WEAK — Self-RAG must doubt: the fragments are barely relevant.
    {"question": "Which exact lubricant should be used for the bearings of pump "
                 "P-42 in a corrosive environment?",
     "relevant": [], "expected_route": "simple", "expected_grade": "not_confident"},
]


def main() -> None:
    data = {"fragments": FRAGMENTS, "queries": QUERIES}
    path = CORPUS / "fragments.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generating the Chapter 24 test corpus:")
    print(f"  + {path.name}: {len(FRAGMENTS)} fragments, {len(QUERIES)} queries")
    print("  Deliberate gaps: P-99, heatwave and agency workers, the corrosive")
    print("  lubricant — all outside the corpus. They trigger the CRAG web fallback")
    print("  and the doubt of Self-RAG.")
    print("  Varied complexity (direct / simple / iterative) for the Adaptive router.")
    print("The running threads: Julien (maintenance), Claire (HR), Sophie (architecture).")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
