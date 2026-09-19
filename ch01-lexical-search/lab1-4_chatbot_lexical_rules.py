# -*- coding: utf-8 -*-
"""
Lab 1-4 — A rule-based lexical chatbot: the previous generation
---------------------------------------------------------------
Objective: build a mini FAQ chatbot with no LLM, no embeddings and no API call.

The chatbot rests only on:
  1. a list of intents;
  2. keywords associated with each intent;
  3. a predetermined answer;
  4. a simple lexical score.

This lab illustrates the previous generation of chatbots: they can be useful on
a very controlled domain, but they fail quickly as soon as the user rephrases,
uses a synonym absent from the rules, or has an intent the designer never
foresaw.

Dependencies: none
Installation: none
Run with: python lab1-4_chatbot_lexical_rules.py
"""

import re
from typing import Dict, List, Tuple


# =============================================================================
# 1. KNOWLEDGE BASE OF THE CHATBOT
# =============================================================================
#
# Each entry stands for one possible intent of the user. An intent is defined
# by a technical label, a list of keywords, and an answer prepared in advance.
#
# The chatbot does not understand meaning. It only looks for words. If no
# relevant keyword is found, it does not know how to answer.
# =============================================================================

FAQ: Dict[str, Dict[str, List[str] | str]] = {
    "battery_lifetime": {
        "keywords": ["battery", "lifetime", "charge", "charged", "100", "percent"],
        "answer": (
            "To preserve battery lifetime, avoid keeping the battery charged at "
            "100 percent for long periods."
        ),
    },
    "machine_learning": {
        "keywords": ["machine", "learning", "learn", "data", "computer", "computers"],
        "answer": (
            "Machine learning allows computers to learn patterns from data without "
            "being explicitly programmed for every rule."
        ),
    },
    "solar_panels": {
        "keywords": ["solar", "panel", "panels", "sunlight", "electricity", "photovoltaic"],
        "answer": (
            "Solar panels convert sunlight into electricity using photovoltaic cells."
        ),
    },
    "python_ai": {
        "keywords": ["python", "programming", "language", "data", "science", "ai"],
        "answer": (
            "Python is widely used in data science and artificial intelligence because "
            "its ecosystem contains many scientific and machine learning libraries."
        ),
    },
    "industrial_maintenance": {
        "keywords": ["maintenance", "machinery", "machine", "lifespan", "operational"],
        "answer": (
            "Regular maintenance of machinery increases its operational lifespan."
        ),
    },
}


# =============================================================================
# 2. TOKENISATION SIMPLE
# =============================================================================
#
# As in a lexical engine, transform the question into normalised words:
#
#   - lowercasing;
#   - removing punctuation;
#   - splitting into words.
#
# The step is deliberately simple. In a real lexical system you would add
# lemmatisation, stop words, spelling correction, and so on.
# =============================================================================


def tokenize(text: str) -> List[str]:
    """Turn a sentence into a list of normalised words."""
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())


# =============================================================================
# 3. THE LEXICAL SCORE OF AN INTENT
# =============================================================================
#
# The score is very simple: count how many words of the question are also
# present among the keywords of the intent.
#
# For example:
#
#   Question: "How can I improve battery lifetime?"
#   Tokens:   ["how", "can", "i", "improve", "battery", "lifetime"]
#
#   Intent battery_lifetime
#   Keywords: ["battery", "lifetime", "charge", "charged", "100", "percent"]
#
#   Words in common: battery, lifetime
#   Score: 2
# =============================================================================


def score_intent(question_tokens: List[str], keywords: List[str]) -> int:
    """Count how many keywords are found in the question."""
    keyword_set = set(keywords)
    return sum(1 for token in question_tokens if token in keyword_set)


# =============================================================================
# 4. DETECTING THE INTENT
# =============================================================================
#
# The chatbot tries every intent and keeps the one with the best lexical score.
#
# If the best score is zero, no intent is recognised. If two intents tie, the
# chatbot keeps the first one encountered. That behaviour is deliberately
# simplistic: it exhibits a classic limit of rule-based systems.
# =============================================================================


def detect_intent(question: str) -> Tuple[str | None, int, List[Tuple[str, int]]]:
    """Return the most probable intent, its score, and all the scores.

    Returns
    -------
    best_intent : str | None
        The name of the intent detected, or None if no keyword was found.
    best_score : int
        The lexical score of the best intent.
    all_scores : list[tuple[str, int]]
        The scores of every intent, for the teaching display.
    """
    question_tokens = tokenize(question)

    all_scores = []
    for intent_name, intent_data in FAQ.items():
        keywords = intent_data["keywords"]
        score = score_intent(question_tokens, keywords)  # type: ignore[arg-type]
        all_scores.append((intent_name, score))

    best_intent, best_score = max(all_scores, key=lambda item: item[1])

    if best_score == 0:
        return None, best_score, all_scores

    return best_intent, best_score, all_scores


# =============================================================================
# 5. GENERATING THE ANSWER
# =============================================================================
#
# Here the word "generation" must be understood in the weak sense: the chatbot
# creates no new answer. It selects a pre-written one.
#
# That is a major difference from an LLM:
#
#   - a lexical chatbot: selects an answer that was foreseen;
#   - an LLM: produces an answer dynamically, from a context.
# =============================================================================


def answer_question(question: str) -> Tuple[str, str | None, int, List[Tuple[str, int]]]:
    """Produce an answer using the lexical rules alone."""
    intent, score, all_scores = detect_intent(question)

    if intent is None:
        fallback = (
            "I do not know how to answer this question. "
            "No predefined lexical rule was matched."
        )
        return fallback, None, score, all_scores

    response = str(FAQ[intent]["answer"])
    return response, intent, score, all_scores


# =============================================================================
# 6. THE TEACHING DISPLAY
# =============================================================================


def display_question(question: str) -> None:
    """Show the behaviour of the chatbot for a given question."""
    response, intent, score, all_scores = answer_question(question)

    print("\n" + "=" * 80)
    print("QUESTION:", question)
    print("=" * 80)

    print("\nTokens detected:")
    print(tokenize(question))

    print("\nScores by intent:")
    for intent_name, intent_score in all_scores:
        print(f"- {intent_name:24s} score={intent_score}")

    print("\nIntent kept:")
    if intent is None:
        print("No intent recognised")
    else:
        print(f"{intent} (score={score})")

    print("\nThe chatbot's answer:")
    print(response)


# =============================================================================
# 7. THE AUTOMATIC DEMONSTRATION
# =============================================================================
#
# The first two questions work, because they contain the keywords the chatbot
# expects.
#
# The later ones expose the limits:
#
#   - "accumulator" is close to "battery" for a human, but not for this lexical
#     rule;
#   - "photovoltaic modules" is close to "solar panels", but the phrasing can
#     throw the system off;
#   - an intent absent from the FAQ cannot be invented.
# =============================================================================


def run_demo() -> None:
    """Run a series of questions, to observe the strengths and the limits."""
    demo_questions = [
        "How can I improve battery lifetime?",
        "What is Python used for in AI?",
        "How can I preserve the accumulator lifespan?",
        "Do photovoltaic modules produce power from light?",
        "Can you explain retrieval augmented generation?",
    ]

    print("=" * 80)
    print("Lab 1-4 — A rule-based lexical chatbot")
    print("=" * 80)
    print(
        "This program shows how a chatbot with no LLM can select an answer "
        "from keywords alone."
    )

    for question in demo_questions:
        display_question(question)


# =============================================================================
# 8. THE OPTIONAL INTERACTIVE MODE
# =============================================================================
#
# After the demonstration, the user can try their own questions.
# To quit: press Enter on an empty line.
# =============================================================================


def run_interactive_mode() -> None:
    """Let the reader try the chatbot by hand."""
    print("\n" + "=" * 80)
    print("Interactive mode")
    print("Type a question, or press Enter on an empty line to quit.")
    print("=" * 80)

    while True:
        try:
            question = input("\nYour question: ").strip()
        except EOFError:
            # No keyboard available (notebook, pipe, CI): leave cleanly.
            print("\nEnd of the lab (no input available).")
            break
        if question == "":
            print("End of the lab.")
            break
        display_question(question)


# =============================================================================
# 9. THE MAIN PROGRAM
# =============================================================================


def main() -> None:
    run_demo()

    # For a lab in class, the interactive mode is switched on. In a notebook or
    # an automated test, comment the following line out to avoid waiting for
    # keyboard input.
    run_interactive_mode()


if __name__ == "__main__":
    main()
