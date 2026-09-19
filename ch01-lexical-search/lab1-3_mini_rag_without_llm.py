"""
Lab 1-3 — Introduction to an elementary RAG, with no LLM
--------------------------------------------------------
Objective: understand the Retrieval-Augmented Generation logic by separating:
  1. a knowledge base,
  2. a search for relevant passages,
  3. a raw answer built from the passages retrieved.

Dependencies: numpy, scikit-learn
Installation: pip install numpy scikit-learn
"""
# =============================================================================
# TEACHING NOTE: TF-IDF AND INFORMATION RETRIEVAL
# =============================================================================
#
# This lab uses TF-IDF (Term Frequency - Inverse Document Frequency) to
# represent documents as numeric vectors.
#
# The idea is simple:
#
#   1) TF (term frequency)
#      Measures how often a word appears in a document. The more frequent a
#      word is in a document, the more important it seems for describing it.
#
#   2) IDF (inverse document frequency)
#      Reduces the importance of words present in almost every document — "the",
#      "of", "is", and so on. A word that is rare across the collection gets a
#      higher weight than a very common one.
#
#   3) TF-IDF
#      The final score combines TF and IDF. A word gets a high score when it is
#      frequent in the document under study, but rare across the whole set.
#
# Once the documents have been turned into TF-IDF vectors, the same treatment
# is applied to the user's question. A similarity — usually the cosine — can
# then be computed between the question and each document, in order to find the
# most relevant ones.
#
# IMPORTANT
# TF-IDF is a lexical approach. The system essentially compares words and their
# frequencies. It does not really understand the meaning of a sentence.
#
# For example, "cat" and "feline" are two different words as far as TF-IDF is
# concerned. The system does not know they are semantically close.
#
# Modern embedding models (Sentence Transformers, BGE, E5, MiniLM and others)
# work differently: they learn a vector representation of sentence meaning
# through deep learning. So:
#
#     "The cat is sleeping."
#     "The feline is asleep."
#
# produce close vectors, even though the words differ.
#
# The advantages of TF-IDF:
#   - very simple to understand;
#   - fast to compute;
#   - requires no AI model at all;
#   - an excellent teaching tool for understanding document search.
#
# The limits:
#   - does not understand meaning;
#   - handles synonyms badly;
#   - sensitive to spelling mistakes;
#   - ignores the context of a sentence.
#
# Despite its limits, TF-IDF remains an excellent introduction to document
# search, and it makes visible the foundations used in modern RAG:
#
#     text -> vector -> similarity -> relevant documents
#
# The difference is that modern embeddings represent the meaning of the texts,
# where TF-IDF mainly represents the presence of words.
# =============================================================================
# =============================================================================
# HOW DOES TF-IDF VECTORISATION WORK IN THIS LAB?
# =============================================================================
#
# This lab presents a very simple document-search system, which is one of the
# fundamental building blocks of a RAG system.
#
# IMPORTANT
# No modern neural embedding is used here — no Sentence Transformers, BGE, E5
# or MiniLM. An older but far more teachable technique is used instead: TF-IDF.
#
# -----------------------------------------------------------------------------
# 1) THE CORPUS
# -----------------------------------------------------------------------------
#
# Suppose the corpus is:
#
#   corpus = [
#       "The lifetime of a battery decreases if it is regularly charged to 100 percent.",
#       "Machine learning allows computers to learn from data without explicit programming.",
#       "Solar panels convert sunlight into electricity through photovoltaic cells.",
#       "Python is a popular programming language for data science and AI.",
#       "Regular maintenance of machinery increases its operational lifespan."
#   ]
#
# Each sentence counts as one document.
#
# -----------------------------------------------------------------------------
# 2) BUILDING THE VOCABULARY
# -----------------------------------------------------------------------------
#
# TF-IDF starts by walking through every document to extract the words present
# in the corpus. It then builds a global vocabulary of all the distinct words:
#
#   [battery, lifetime, machine, learning, computers, data, solar,
#    panels, python, science, maintenance, lifespan, ...]
#
# Suppose the corpus holds 35 distinct words in total. Each document is then
# represented by a vector of size 35.
#
# In contrast with modern embeddings:
#
#     TF-IDF:                dimension = the number of words in the vocabulary
#     Sentence Transformers: dimension = fixed by the model (384, 768, 1024...)
#
# -----------------------------------------------------------------------------
# 3) TURNING A DOCUMENT INTO A VECTOR
# -----------------------------------------------------------------------------
#
# Take the first document:
#
#   "The lifetime of a battery decreases if it is regularly charged to 100 percent."
#
# TF-IDF computes a weight for each word of the vocabulary. Simplified:
#
#   battery      -> 0.52
#   lifetime     -> 0.48
#   decreases    -> 0.45
#   charged      -> 0.57
#
# Words absent from the document get the value 0. The document therefore
# becomes a list of numbers:
#
#   [0.52, 0.48, 0.45, 0.57, 0, 0, 0, 0, ...]
#
# Each position of the vector corresponds directly to a word of the vocabulary.
#
# -----------------------------------------------------------------------------
# 4) WHAT DOES TF-IDF MEAN?
# -----------------------------------------------------------------------------
#
# TF, term frequency, measures how often a word occurs in the document. The
# more often it appears, the higher its weight.
#
# IDF, inverse document frequency, reduces the importance of words present in
# almost every document. "The", "of" and "is" appear everywhere; they carry
# little information for telling documents apart, so their weight is cut.
#
# TF-IDF = TF x IDF. A word gets a high score when it is frequent in the
# document and rare across the corpus.
#
# -----------------------------------------------------------------------------
# 5) WHAT DOES THE VECTORISATION PRODUCE?
# -----------------------------------------------------------------------------
#
# After:
#
#   vectorizer = TfidfVectorizer()
#   X = vectorizer.fit_transform(corpus)
#
# we get a matrix with X.shape = (5, 35), which means 5 documents and 35
# distinct words in the vocabulary. Each row is a document, each column a word:
#
#                battery learning solar python maintenance ...
#   document 1     0.52     0      0      0       0
#   document 2      0      0.61    0      0       0
#   document 3      0       0     0.58    0       0
#   document 4      0       0      0     0.63     0
#   document 5      0       0      0      0      0.57
#
# -----------------------------------------------------------------------------
# 6) HOW DOES THE SEARCH WORK?
# -----------------------------------------------------------------------------
#
# If the user asks:
#
#   "How can computers learn from data?"
#
# TF-IDF turns that question into a vector too. The important words are
# "computers", "learn" and "data", so the question vector lands very close to:
#
#   "Machine learning allows computers to learn from data..."
#
# A mathematical similarity, usually the cosine, is then computed between the
# question vector and each document vector. The document with the highest
# similarity is taken to be the most relevant.
#
# -----------------------------------------------------------------------------
# 7) THE LIMITS OF TF-IDF
# -----------------------------------------------------------------------------
#
# TF-IDF mainly compares words. It does not really understand the meaning of a
# sentence. For example, "AI" and "Artificial Intelligence" mean the same thing
# to a human, and yet TF-IDF may treat them as very different, because they are
# not the same words. Likewise "cat" and "feline" are seen as two distinct
# terms.
#
# -----------------------------------------------------------------------------
# 8) THE DIFFERENCE WITH MODERN EMBEDDINGS
# -----------------------------------------------------------------------------
#
# In TF-IDF, one dimension is one word.
# In modern embeddings, one dimension is an abstract feature learned by a
# neural network.
#
# Embeddings try to represent the meaning of a sentence, where TF-IDF
# essentially represents the presence and the importance of words.
#
# -----------------------------------------------------------------------------
# WHAT TO REMEMBER
# -----------------------------------------------------------------------------
#
# TF-IDF is an excellent introduction to document search:
#
#     text -> vectorisation -> similarity -> relevant documents
#
# Modern RAG systems use exactly the same general idea, but replace TF-IDF with
# embeddings able to represent the meaning of sentences rather than the plain
# words of a vocabulary.
#
# =============================================================================
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# 1) The knowledge base
# ---------------------------------------------------------------------------
corpus = [
    "The lifetime of a battery decreases if it is regularly charged to 100 percent.",
    "Machine learning allows computers to learn from data without explicit programming.",
    "Solar panels convert sunlight into electricity through photovoltaic cells.",
    "Python is a popular programming language for data science and AI.",
    "Regular maintenance of machinery increases its operational lifespan.",
]


# ---------------------------------------------------------------------------
# 2) TF-IDF indexing
# ---------------------------------------------------------------------------
# This step prepares the corpus for search: each document becomes a vector that
# can be handled mathematically.
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(corpus)


# ---------------------------------------------------------------------------
# 3) The user's question
# ---------------------------------------------------------------------------
try:
    query = input("Enter your question: ")
except EOFError:
    # No keyboard available (notebook, pipe, CI): fall back on a sample question
    # so the lab still runs end to end.
    query = "how many days of remote work"
    print(f"Enter your question: {query}   [no input available, sample used]")
query_vec = vectorizer.transform([query])


# ---------------------------------------------------------------------------
# 4) Finding the most relevant document
# ---------------------------------------------------------------------------
similarities = cosine_similarity(query_vec, X).flatten()
top_idx = int(similarities.argmax())

print("\nMost relevant document:")
print(corpus[top_idx])
print(f"Score: {similarities[top_idx]:.4f}")


# ---------------------------------------------------------------------------
# 5) Retrieving the 3 best documents
# ---------------------------------------------------------------------------
top_k = 3
top_indices = np.argsort(similarities)[-top_k:][::-1]

print("\nTop", top_k, "documents:")
for idx in top_indices:
    print(f"- score={similarities[idx]:.4f} | {corpus[idx]}")


# ---------------------------------------------------------------------------
# 6) The raw answer
# ---------------------------------------------------------------------------
# The "Generation" of RAG is heavily simplified here: no new sentence is
# generated by an LLM, the documents retrieved are simply assembled.
print("\nRaw answer, with no LLM:")
print(" ".join(corpus[idx] for idx in top_indices))
