"""
Lab 1-1 — Information retrieval with TF-IDF
-------------------------------------------
Objective: turn documents into TF-IDF vectors, compare a user question with
each document, and retrieve the closest ones.

Dependencies: scikit-learn, numpy
Installation: pip install scikit-learn numpy
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# 1) The document corpus
# ---------------------------------------------------------------------------
# The corpus stands here for a small knowledge base. In a real system it could
# be web pages, technical manuals, PDF documents, articles, and so on.
corpus = [
    "The lifetime of a battery decreases if it is regularly charged to 100 percent.",
    "Machine learning allows computers to learn from data without explicit programming.",
    "Solar panels convert sunlight into electricity through photovoltaic cells.",
    "Python is a popular programming language for data science and artificial intelligence.",
    "Regular maintenance of machinery increases its operational lifespan.",
]


# ---------------------------------------------------------------------------
# 2) TF-IDF vectorisation
# ---------------------------------------------------------------------------
# TF-IDF turns each document into a numeric vector.
#   - TF:  a word counts for more if it appears often in a document.
#   - IDF: a word counts for less if it appears in many documents.
# The idea is therefore to bring out the important, discriminating words.
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)

print("Shape of the TF-IDF matrix:", X.shape)
print("Number of documents:", X.shape[0])
print("Number of words / features:", X.shape[1])


# ---------------------------------------------------------------------------
# 3) The user's question
# ---------------------------------------------------------------------------
# The same vectorizer is used to transform the question. This matters: we call
# transform(), not fit_transform(), because the vocabulary has already been
# learned on the corpus.
try:
    query = input("Enter your question: ")
except EOFError:
    # No keyboard available (notebook, pipe, CI): fall back on a sample question
    # so the lab still runs end to end.
    query = "how many days of remote work"
    print(f"Enter your question: {query}   [no input available, sample used]")
query_vec = vectorizer.transform([query])


# ---------------------------------------------------------------------------
# 4) Cosine similarity
# ---------------------------------------------------------------------------
# Cosine similarity measures the angle between two vectors. The closer the
# score is to 1, the closer the texts are considered to be.
similarities = cosine_similarity(query_vec, X).flatten()

print("\nSimilarity scores:")
for i, score in enumerate(similarities):
    print(f"Document {i} — similarity: {score:.4f}")


# ---------------------------------------------------------------------------
# 5) The best document
# ---------------------------------------------------------------------------
# np.argmax returns the index of the highest score.
top_index = np.argmax(similarities)

print("\nMost relevant document:")
print(corpus[top_index])


# ---------------------------------------------------------------------------
# 6) The top-K documents
# ---------------------------------------------------------------------------
# Top-K means retrieving not one document but the K best. It is an idea used
# everywhere in RAG systems.
top_k = 3
# argsort sorts the indices by increasing score; [::-1] reverses to decreasing.
top_indices = np.argsort(similarities)[-top_k:][::-1]

print("\nTop", top_k, "documents:")
for idx in top_indices:
    print(f"- score={similarities[idx]:.4f} | {corpus[idx]}")


# ---------------------------------------------------------------------------
# 7) A raw answer, with no LLM
# ---------------------------------------------------------------------------
# There is no language model here: the answer is simply made of the documents
# retrieved. That is enough to understand the Retrieval half of RAG.
print("\nAnswer generated (without an LLM):")
for idx in top_indices:
    print(corpus[idx])
