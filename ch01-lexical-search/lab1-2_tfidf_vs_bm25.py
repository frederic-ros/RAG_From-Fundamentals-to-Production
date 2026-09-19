# =============================================================================
# LAB 1-2: COMPARING TF-IDF AND BM25
# =============================================================================
#
# Learning objective
# ------------------
# This lab compares two lexical information-retrieval techniques:
#
#   1. TF-IDF
#   2. BM25
#
# Neither is a neural embedding. Neither really understands the meaning of a
# sentence. They mainly compare the words present in the query with the words
# present in the documents.
#
# The important difference is that BM25 corrects some of TF-IDF's defects:
#
#   - it limits the effect of excessive repetition of a word;
#   - it takes document length into account;
#   - it often gives better results in document search.
#
# The corpus here is deliberately built to make those differences visible.
#
# =============================================================================

import math
import re
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =============================================================================
# 1. THE EXAMPLE CORPUS
# =============================================================================
#
# Each string counts as one document. The corpus gathers several documents
# about batteries, solar energy, machine learning and maintenance.
#
# Some documents are short and precise. Others are long, or repeat certain
# words heavily. That is deliberate: it is what shows that TF-IDF and BM25 do
# not react in quite the same way.
# =============================================================================

corpus = [
    # A short document, highly relevant to a question about batteries.
    "Battery lifetime decreases when a battery is always charged to 100 percent.",

    # A very long document: it does talk about batteries, but it carries a lot
    # of extra information. BM25 penalises long documents more.
    "Battery maintenance is important in electric vehicles. A battery should be monitored carefully. "
    "Temperature, charging cycles, storage conditions, voltage, current, diagnostics, user habits, "
    "software updates, and manufacturer recommendations all influence the operational lifetime of the system.",

    # A document that repeats the word "battery" heavily. TF-IDF can be swayed
    # by that repetition, whereas BM25 limits the accumulation effect through a
    # saturation of the term frequency.
    "Battery battery battery battery battery charging charging charging.",

    # A document relevant to a query about machine learning.
    "Machine learning allows computers to learn from data without explicit programming.",

    # A document relevant to a query about solar energy.
    "Solar panels convert sunlight into electricity through photovoltaic cells.",

    # A short document about Python and AI.
    "Python is a popular programming language for data science and AI.",

    # A short document about industrial maintenance.
    "Regular maintenance of machinery increases its operational lifespan.",
]


document_names = [
    "D1 — battery, short and precise",
    "D2 — battery, long and detailed",
    "D3 — artificial word repetition",
    "D4 — machine learning",
    "D5 — solar",
    "D6 — Python / AI",
    "D7 — maintenance",
]


# =============================================================================
# 2. SIMPLE TOKENISATION
# =============================================================================
#
# BM25 needs to work on lists of words, so a small tokenisation function is
# written here:
#
#   - lowercasing;
#   - removing punctuation;
#   - splitting into words.
#
# In a real search engine this step can be far more complex: stemming,
# lemmatisation, stop words, accents, multiple languages, and so on.
# =============================================================================


def tokenize(text):
    """Turn a sentence into a list of simple words."""
    return re.findall(r"\b[a-zA-Z]+\b", text.lower())


# The tokenised corpus, for BM25
tokenized_corpus = [tokenize(doc) for doc in corpus]


# =============================================================================
# 3. SEARCHING WITH TF-IDF
# =============================================================================
#
# With TF-IDF each document becomes a vector whose dimension equals the number
# of distinct words in the corpus. Each dimension corresponds to one word:
#
#   dimension 0 -> "battery"
#   dimension 1 -> "charging"
#   dimension 2 -> "machine"
#   ...
#
# The value in each dimension is the TF-IDF weight of that word.
# =============================================================================


def search_tfidf(query, top_k=5):
    """Return the documents closest to the query, according to TF-IDF."""

    vectorizer = TfidfVectorizer(stop_words="english")

    # Learn the vocabulary on the corpus, and vectorise the documents.
    tfidf_matrix = vectorizer.fit_transform(corpus)

    # Transform the query into the same vector space as the documents.
    query_vector = vectorizer.transform([query])

    # Cosine similarity between the query and each document.
    scores = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # Sort the scores in decreasing order.
    ranking = np.argsort(scores)[::-1][:top_k]

    return [(idx, scores[idx]) for idx in ranking]


# =============================================================================
# 4. SEARCHING WITH BM25
# =============================================================================
#
# BM25 is an improvement on TF-IDF, widely used in document search.
#
# The general idea:
#
#   - a word that is rare in the corpus is important;
#   - a word that is frequent in a document raises the score;
#   - but excessive repetition of a word must not raise the score indefinitely;
#   - very long documents are slightly penalised.
#
# A simplified formula. For each word of the query, summed:
#
#   IDF(word) * ((tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_len / mean_len)))
#
# where:
#
#   tf = frequency of the word in the document
#   k1 = the term-frequency saturation parameter
#   b  = the length-normalisation parameter
#
# The classic values:
#
#   k1 = 1.5
#   b  = 0.75
# =============================================================================


def compute_idf(term, tokenized_documents):
    """Compute the BM25 IDF of a word."""

    number_of_documents = len(tokenized_documents)

    # The number of documents containing the term.
    documents_containing_term = sum(1 for doc in tokenized_documents if term in doc)

    # The IDF formula used in BM25. The +1 avoids negative values on the small
    # teaching corpora used here.
    return math.log(1 + (number_of_documents - documents_containing_term + 0.5) /
                    (documents_containing_term + 0.5))



def bm25_score(query, document_tokens, tokenized_documents, k1=1.5, b=0.75):
    """Compute the BM25 score between a query and a document."""

    query_tokens = tokenize(query)
    document_length = len(document_tokens)
    average_document_length = np.mean([len(doc) for doc in tokenized_documents])
    term_frequencies = Counter(document_tokens)

    score = 0.0

    for term in query_tokens:
        if term not in term_frequencies:
            # If the query word is absent from the document, it contributes
            # nothing to the score.
            continue

        tf = term_frequencies[term]
        idf = compute_idf(term, tokenized_documents)

        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * document_length / average_document_length)

        score += idf * numerator / denominator

    return score



def search_bm25(query, top_k=5):
    """Return the documents most relevant according to BM25."""

    scores = [
        bm25_score(query, doc_tokens, tokenized_corpus)
        for doc_tokens in tokenized_corpus
    ]

    ranking = np.argsort(scores)[::-1][:top_k]

    return [(idx, scores[idx]) for idx in ranking]


# =============================================================================
# 5. SIDE-BY-SIDE DISPLAY
# =============================================================================


def display_results(query, top_k=5):
    """Print the TF-IDF and BM25 results side by side."""

    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    tfidf_results = search_tfidf(query, top_k=top_k)
    bm25_results = search_bm25(query, top_k=top_k)

    print("\n--- TF-IDF results ---")
    for rank, (idx, score) in enumerate(tfidf_results, start=1):
        print(f"{rank}. {document_names[idx]} | score = {score:.4f}")
        print(f"   {corpus[idx]}\n")

    print("\n--- BM25 results ---")
    for rank, (idx, score) in enumerate(bm25_results, start=1):
        print(f"{rank}. {document_names[idx]} | score = {score:.4f}")
        print(f"   {corpus[idx]}\n")


# =============================================================================
# 6. EXPERIMENTS TO RUN
# =============================================================================
#
# The queries below are chosen to bring the differences out.
#
# Query 1: "battery charging lifetime"
#   Compares a short relevant document, a long relevant one, and one that
#   repeats the words artificially.
#
# Query 2: "machine learning data"
#   Both methods should find the machine-learning document clearly.
#
# Query 3: "maintenance lifespan"
#   Shows how strongly lexical search depends on the exact words.
# =============================================================================

if __name__ == "__main__":
    queries = [
        "battery charging lifetime",
        "machine learning data",
        "maintenance lifespan",
    ]

    for query in queries:
        display_results(query, top_k=5)


# =============================================================================
# 7. QUESTIONS FOR THE READER
# =============================================================================
#
# 1. Which document is ranked first for the query "battery charging lifetime"?
#
# 2. Is the document that repeats "battery" many times really the most relevant
#    one, to a human reader?
#
# 3. Why does BM25 limit the effect of repeating a word?
#
# 4. Why does BM25 penalise very long documents slightly?
#
# 5. Do TF-IDF or BM25 understand that "AI" and "artificial intelligence" are
#    semantically close?
#
# 6. Why do these methods remain useful in modern RAG systems?
#
# The expected answer to question 6:
#
# TF-IDF and BM25 are fast, simple and effective at finding documents that
# contain the exact words of the query. In modern RAG systems BM25 is often
# used alongside embeddings, in a hybrid approach:
#
#   - BM25 finds documents by lexical match;
#   - the embeddings find documents by semantic proximity;
#   - a reranker can then sort the best passages.
#
# =============================================================================
