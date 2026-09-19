# =============================================================================
# Lab 1-5: THE TEST THAT HURTS — SYNONYMS AND A SCORE OF ZERO
# =============================================================================
#
# Learning objective
# ------------------
# This lab shows a fundamental limit of lexical search:
#
#   two sentences can be very close for a human being, and very far apart for
#   TF-IDF or BM25, if they do not share the same words.
#
# For example:
#
#   Document: "Bordeaux is renowned for its wines."
#   Query:    "Which city is associated with oenology?"
#
# A human understands that "wine" and "oenology" are linked. A lexical engine
# does not necessarily know it.
#
# The lab therefore prepares the chapter on embeddings and semantic search: to
# go beyond exact words, meaning will have to be represented.
#
# Dependencies: numpy, scikit-learn
# Installation: pip install numpy scikit-learn
# =============================================================================

import math
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =============================================================================
# 1. CORPUS D'EXEMPLE
# =============================================================================
#
# Each document holds one simple piece of information. The corpus is
# deliberately small, so that the results are easy to interpret.
#
# The document we are after is document 0: it speaks of Bordeaux and of wine.
# We will then ask questions that drift further and further, lexically, from
# that document.
# =============================================================================

corpus = [
    "Bordeaux is renowned for its wines and its eighteenth-century architecture.",
    "Paris is the capital of France and home to the Eiffel Tower.",
    "Toulouse is nicknamed the pink city and has a strong aerospace industry.",
    "Lyon is known for its gastronomy and its historic centre.",
    "Marseille is a large Mediterranean port.",
]

names = [
    "DOC 0 — Bordeaux / wines",
    "DOC 1 — Paris / capital",
    "DOC 2 — Toulouse / aerospace",
    "DOC 3 — Lyon / gastronomy",
    "DOC 4 — Marseille / port",
]


# =============================================================================
# 2. THE TEST QUERIES
# =============================================================================
#
# Query 1 shares a word with the document: the lexical engine should work.
#
# Query 2 looks just as close to a human, but says "wine" where the document
# says "wines". A single letter is enough for the engine to lose it.
#
# Queries 3 and 4 use terms that are close for a human but absent from the
# document: "vineyard", "oenology". The lexical score then collapses.
#
# Query 5 is deliberately more implicit: it shows that the problem is not only
# synonymy, but also business or cultural phrasing.
# =============================================================================

queries = [
    "Which French city is renowned for its wines?",
    "Which city is known for wine?",
    "Which French city is famous for its vineyard?",
    "Which French metropolis is associated with oenology?",
    "Which city should you visit to discover a great winegrowing culture?",
]


# =============================================================================
# 3. TOKENISATION TOOLS FOR BM25
# =============================================================================
#
# BM25 works on words, so a simple function is defined here: it lowercases the
# text and extracts the words.
#
# A short stop-word list removes the scaffolding of the questions — "which",
# "city", "known", "renowned" — so that they cannot create a spurious match on
# their own. The tokenisation is deliberately simple, to stay readable.
# =============================================================================

STOP_WORDS = {
    "the", "a", "an", "of", "to", "in", "on", "for", "by", "with", "and",
    "or", "is", "are", "its", "it", "this", "that", "these", "which", "what",
    "who", "you", "should", "does", "do", "french", "city", "cities",
    "metropolis", "known", "renowned", "famous", "associated", "great",
}


def tokenize(text):
    """Split a text into simple words and drop a few function words."""
    tokens = re.findall(r"\b\w+\b", text.lower())
    return [token for token in tokens if token not in STOP_WORDS]


# =============================================================================
# 4. A SIMPLE BM25 IMPLEMENTATION
# =============================================================================
#
# BM25 is a lexical method, more robust than TF-IDF in many cases. But it stays
# lexical: if the words of the query are absent from the document, it cannot
# guess the synonyms.
# =============================================================================

def bm25_scores(query, documents, k1=1.5, b=0.75):
    """Compute a simple BM25 score between a query and each document."""
    tokenized_docs = [tokenize(doc) for doc in documents]
    tokenized_query = tokenize(query)

    n_docs = len(tokenized_docs)
    doc_lengths = [len(doc) for doc in tokenized_docs]
    avg_doc_length = sum(doc_lengths) / n_docs

    # Number of documents contenant each word.
    document_frequency = Counter()
    for doc_tokens in tokenized_docs:
        for term in set(doc_tokens):
            document_frequency[term] += 1

    scores = []

    for doc_tokens, doc_length in zip(tokenized_docs, doc_lengths):
        term_frequency = Counter(doc_tokens)
        score = 0.0

        for term in tokenized_query:
            if term not in term_frequency:
                continue

            df = document_frequency[term]
            idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))

            tf = term_frequency[term]
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_length / avg_doc_length)

            score += idf * numerator / denominator

        scores.append(score)

    return np.array(scores)


# =============================================================================
# 5. FONCTIONS D'AFFICHAGE
# =============================================================================

def show_corpus():
    """Print the corpus used in this lab."""
    print("=" * 78)
    print("CORPUS")
    print("=" * 78)
    for name, doc in zip(names, corpus):
        print(f"{name}")
        print(f"  {doc}\n")


def show_top_results(method_name, scores, top_k=3):
    """Print the best documents for a given method."""
    ranking = np.argsort(scores)[::-1]

    print(f"\n{method_name} - top {top_k}")
    print("-" * 78)

    for rank, doc_index in enumerate(ranking[:top_k], start=1):
        print(
            f"#{rank} | {names[doc_index]:28s} | score = {scores[doc_index]:.4f}"
        )

    best_index = int(ranking[0])
    return best_index, float(scores[best_index])


def explain_result(query, tfidf_best, tfidf_score, bm25_best, bm25_score):
    """Produit a courte interprstateion educational."""
    expected_index = 0

    print("\nInterpretation")
    print("-" * 78)

    if tfidf_best == expected_index and bm25_best == expected_index:
        print("Both engines find the right document.")
        print("The query still shares enough vocabulary with the corpus.")
    elif tfidf_score == 0 and bm25_score == 0:
        print("Neither engine really finds the right document.")
        print("The important words of the query are absent from the document.")
        print("This is the wall of synonymy: the engine compares words, not meaning.")
    else:
        print("The result becomes unstable.")
        print("The lexical engine catches a few words, but not the full intent.")
        print("A human understands the question better than the system does.")

    print(f"Query analysed: {query}")


# =============================================================================
# 6. PROGRAMME PRINCIPAL
# =============================================================================

def main():
    print("=" * 78)
    print("Lab 1-5 — The test that hurts: a synonym query, a score of zero")
    print("=" * 78)

    show_corpus()

    # -------------------------------------------------------------------------
    # Vectorization TF-IDF of the corpus.
    # -------------------------------------------------------------------------
    # On apprend the vocabulary on the corpus uniquement.
    # Words absent from the corpus will simply be ignored in the queries.
    # -------------------------------------------------------------------------
    vectorizer = TfidfVectorizer(lowercase=True, tokenizer=tokenize, token_pattern=None)
    tfidf_matrix = vectorizer.fit_transform(corpus)

    print("Vocabulary learned by TF-IDF:")
    print(sorted(vectorizer.get_feature_names_out()))

    print("\n" + "=" * 78)
    print("TESTS")
    print("=" * 78)

    summary = []

    for i, query in enumerate(queries, start=1):
        print("\n" + "=" * 78)
        print(f"QUERY {i}")
        print("=" * 78)
        print(query)

        # ---------------------------------------------------------------------
        # TF-IDF + cosine similarity.
        # ---------------------------------------------------------------------
        query_vector = vectorizer.transform([query])
        tfidf_scores = cosine_similarity(query_vector, tfidf_matrix).flatten()

        # ---------------------------------------------------------------------
        # BM25.
        # ---------------------------------------------------------------------
        bm25 = bm25_scores(query, corpus)

        tfidf_best, tfidf_best_score = show_top_results("TF-IDF", tfidf_scores)
        bm25_best, bm25_best_score = show_top_results("BM25", bm25)

        explain_result(
            query=query,
            tfidf_best=tfidf_best,
            tfidf_score=tfidf_best_score,
            bm25_best=bm25_best,
            bm25_score=bm25_best_score,
        )

        summary.append((query, tfidf_best_score, bm25_best_score))

    # -------------------------------------------------------------------------
    # The final summary.
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print("The right document is always: DOC 0 — Bordeaux / wines")
    print("\nHow the best score obtained evolves:")

    for i, (query, tfidf_score, bm25_score) in enumerate(summary, start=1):
        print(
            f"Query {i} | TF-IDF max = {tfidf_score:.4f} | BM25 max = {bm25_score:.4f}"
        )

    print("\nThe teaching conclusion")
    print("-" * 78)
    print("TF-IDF and BM25 are useful, fast and explainable.")
    print("But they still rest on the presence of words in the texts.")
    print("When the query uses vocabulary absent from the corpus,")
    print("the score can collapse even when the answer is obvious to a human.")
    print("\nTransition: the chapter on embeddings will introduce another idea —")
    print("representing sentences by their meaning, not only by their words.")


if __name__ == "__main__":
    main()
