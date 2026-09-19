# -*- coding: utf-8 -*-
"""
qtlib.py — the shared building blocks of Chapter 21 (query transformation).

The chapter starts from an observation: a good question is often a bad search,
because the user speaks the language of the PROBLEM ("it is making an odd
noise") while the document speaks the language of the SOLUTION ("the vibration
signature of a bearing defect"). The question is therefore transformed before it
reaches the index.

The five transformations of the chapter:

  * hyde()          : writes a plausible hypothetical answer and searches with it;
  * expansion()     : generates reformulations (synonyms, neighbouring terms);
  * decomposition() : cuts a compound question into sub-questions;
  * step_back()     : steps up a level, towards a more general question;
  * rewriting()     : resolves the pronouns ("its", "their") using the history;

plus router(), which chooses between them.

An honest teaching note
-----------------------
A real system would delegate these transformations to an LLM. Here they are
implemented deterministically and offline: reproducible, and enough to
demonstrate the PRINCIPLE of each one. The teaching point — "a false answer
already speaks the language of the real documents" — comes out clearly, as in
the offline fallbacks of the earlier chapters. If sentence-transformers is
present, the retrieval uses real embeddings.

A WARNING ON THE WORD LISTS. Several mechanisms in this file key on literal
strings: the problem-to-solution bridge, the stop words, the component and
subject patterns, and above all the anaphora set used by contains_pronoun(). All
of them must be written in the language of the corpus and kept in step with
generate_corpus.py. The anaphora set is the most dangerous: if it matches
nothing, the rewriting branch never fires and the chapter reports "no rewriting
needed" for every question, silently.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


# ===========================================================================
# Detection optionnelle of a model of embedding
# ===========================================================================
_ST_MODEL = None
_MODE = None


def mode() -> str:
    """Mode of retrieval actif : 'sentence-to transforms' or 'tfidf'."""
    global _ST_MODEL, _MODE
    if _MODE is not None:
        return _MODE
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer("all-MiniLM-L6-v2")
        m.encode(["test"])
        _ST_MODEL, _MODE = m, "sentence-transformers"
    except Exception:
        _MODE = "tfidf"
    return _MODE


# ===========================================================================
# Moteur of search (retrieval)
# ===========================================================================
class Search:
    """Indexe a corpus and classe the documents by relevance to a query.

 in mode 'tfidf' (repli), the index is a TF-IDF lexical : it is justement this
    that makes the chapter's "vocabulary gap" visible — a question that
 not emploie not the words of the document not the refinds not. in mode
 'sentence-to transforms', we use of trues embeddings denses.
 """

    def __init__(self, corpus: Sequence[str]) -> None:
        self.corpus = list(corpus)
        self.mode = mode()
        if self.mode == "sentence-transformers":
            self._vecs = _ST_MODEL.encode(self.corpus, normalize_embeddings=True)
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            # token_pattern : on garde also the tokens of A seul character
            # ("A", "B"), otherwise "pump A" and "pump B" would become identical
            # after tokenisation, which would falsify the decomposition.
            self._vec = TfidfVectorizer(sublinear_tf=True, ngram_range=(1, 2),
                                        token_pattern=r"(?u)\b\w+\b")
            self._mat = self._vec.fit_transform(self.corpus)

    def _scores(self, requete: str) -> np.ndarray:
        if self.mode == "sentence-transformers":
            q = _ST_MODEL.encode([requete], normalize_embeddings=True)[0]
            return self._vecs @ q
        from sklearn.metrics.pairwise import cosine_similarity
        q = self._vec.transform([requete])
        return cosine_similarity(q, self._mat)[0]

    def classer(self, requete: str, k: Optional[int] = None) -> List[Tuple[int, float]]:
        """Rank the corpus for a query: [(index, score)], decreasing."""
        scores = self._scores(requete)
        ordre = np.argsort(-scores)
        res = [(int(i), float(scores[i])) for i in ordre]
        return res[:k] if k else res

    def classer_multi(self, requetes: Sequence[str],
                      k: Optional[int] = None) -> List[Tuple[int, float]]:
        """Rank by merging several queries, for expansion and decomposition.

 On additionne the scores of each query (fusion by somme), then on
 ordonne. it is the fusion the more simple and the more lisible.
 """
        total = np.zeros(len(self.corpus))
        for r in requetes:
            total += self._scores(r)
        ordre = np.argsort(-total)
        res = [(int(i), float(total[i])) for i in ordre]
        return res[:k] if k else res


# ===========================================================================
# Vocabulary technique simulated (for HyDE, expansion, recul)
# ===========================================================================
# Pont between the langage of the PROBLEM (words of the user) and the langage of the
# SOLUTION (words documents). it is this pont that a true LLM fournirait ; here on
# the explicite, in a way deterministic and transparente.
_PROBLEM_SOLUTION_BRIDGE: Dict[str, List[str]] = {
    "noise": ["vibration signature", "acoustic signature", "bearing defect"],
    "odd": ["anomaly", "defect"],
    "start-up": ["commissioning", "start-up phase"],
    "hot": ["temperature rise", "overheating", "cooling failure", "bearing wear"],
    "leak": ["sealing", "gasket failure"],
    "broken": ["failure", "fracture"],
    "not working": ["malfunction", "breakdown"],
    "slow": ["slowdown", "loss of performance"],
    "vibrat": ["vibration", "imbalance", "vibration signature"],
}


def _tokens(text: str) -> List[str]:
    return re.findall(r"\w+", text.lower())


# ===========================================================================
#  TRANSFORMATION 1 — HyDE
# ===========================================================================
def hyde(question: str) -> str:
    """Generate a "hypothetical document": a plausible, technical answer.

 Do NOT search for the truth: generate text that RESEMBLES a document
 of answer, in injectant the vocabulary technique (the langage of the solution).
 this document, rather than the question, becomes the search key.

 (Simulation deterministic of a appel LLM : a true HyDE demanderait at the model
 of inventer the answer. Here on assemble a gabarit + the pont of vocabulary.)
 """
    solution_terms: List[str] = []
    for word, solutions in _PROBLEM_SOLUTION_BRIDGE.items():
        if word in question.lower():
            solution_terms.extend(solutions)
    # Keep the entities too (codes M-18, P-42, A, B) present in the question.
    codes = re.findall(r"\b[A-Za-z]+-?\d+\b", question)
    subject = " ".join(codes) if codes else "the equipment concerned"

    if solution_terms:
        body = ", ".join(dict.fromkeys(solution_terms))
        doc = (f"The diagnosis concerning {subject} brings out {body}. "
               f"The technical analysis and the associated procedure make it "
               f"possible to identify the origin of the defect and remedy it.")
    else:
        # No known bridge: stay generic. This is the case where HyDE helps least.
        doc = (f"The technical answer concerning {subject} describes the "
               f"possible causes, the checks to carry out and the recommended "
               f"resolution procedure.")
    return doc


# ===========================================================================
#  TRANSFORMATION 2 — Expansion
# ===========================================================================
def expansion(question: str, max_reform: int = 4) -> List[str]:
    """Generate several reformulations of the question (synonyms, near terms).

    The net is widened: the original question PLUS variants using the
 vocabulary of the solution. On limite volontairement the number (3 to 5) for not
 not diluer the search in the bruit.
 """
    reforms = [question]
    for word, solutions in _PROBLEM_SOLUTION_BRIDGE.items():
        if word in question.lower():
            for s in solutions:
                variant = re.sub(word, s, question, flags=re.IGNORECASE)
                if variant not in reforms:
                    reforms.append(variant)
    # Add a "keywords" reformulation, stripped of the interrogative words. This
    # set must be English, to match the questions the reader will actually type.
    stop = {"why", "how", "what", "which", "who", "when", "where", "the", "a",
            "an", "is", "are", "does", "do", "it", "of", "to", "in", "on",
            "for", "at", "that", "this", "and", "or", "make", "makes", "making"}
    keys = [t for t in _tokens(question) if t not in stop]
    if keys:
        reforms.append(" ".join(keys))
    # Deduplicate while keeping the order, then bound the count.
    uniques = list(dict.fromkeys(reforms))
    return uniques[:max_reform]


# ===========================================================================
# TRANSFORMATION 3 — Decomposition
# ===========================================================================
def decomposition(question: str) -> List[str]:
    """Cut a compound question into sub-questions.

    Comparisons ("compare X and Y", "X and Y") and lists are detected,
    then one sub-question is built per entity. Without that, a single search
    mixes the subjects and answers none of them well.
 """
    q = question.strip()
    # Spot the entities: equipment codes or letters (A, B, P-42, M-18...).
    codes = re.findall(r"\b(?:pump|motor|valve|circuit)\s+([A-Za-z]+-?\d*)\b",
                       q, flags=re.IGNORECASE)
    # Detect the name of the component (pump, motor...).
    component_match = re.search(r"\b(pump|motor|valve|circuit)\b", q, re.IGNORECASE)
    component = component_match.group(1).lower() if component_match else "item"
    # The subject of the question (maintenance, procedure, safety...).
    subject_match = re.search(r"\b(maintenance|procedure|safety|servicing|"
                              r"repair|diagnosis)\b", q, re.IGNORECASE)
    subject = subject_match.group(1).lower() if subject_match else "characteristics"

    if len(codes) >= 2:
        return [f"{subject} {component} {c}" for c in codes]
    # No comparison detected: return the question as it stands.
    return [question]


# ===========================================================================
# TRANSFORMATION 4 — Prise of recul
# ===========================================================================
def step_back(question: str) -> str:
    """Generate a more general question: the context, the principles.

 Quand the question is too pointue for find son context, on remonte of a
    level: the particulars are removed — proper nouns, dates, individual cases —
    so as to query the general rule.
 """
    q = question
    # The DATE is stripped FIRST, then the proper nouns. The order matters in
    # English and did not in French: French month names are lower-case ("mars"),
    # so the proper-noun rule left them alone, but "March" is capitalised. Strip
    # the names first and the date pattern "in <month> <year>" no longer matches.
    q = re.sub(r"\bin\s+\w+\s*\d{4}\b", "", q, flags=re.IGNORECASE)  # "in March 2026"
    q = re.sub(r"\b[A-Z][a-z]+\b", "", q)                # names (Dupont, Julien...)
    q = re.sub(r"\s+", " ", q).strip(" ?.")
    # Reformulate as a question of principle.
    keys = [t for t in _tokens(q) if t not in {"is", "are", "does", "do", "he",
            "she", "it", "to", "the", "a", "an", "that", "this", "entitled",
            "have", "has"}]
    core = " ".join(keys[-4:]) if keys else "this case"
    return f"What are the general rules concerning {core}?"


# ===========================================================================
# TRANSFORMATION 5 — Conversational rewriting
# ===========================================================================
# THE ANAPHORA LIST IS THE MECHANISM, NOT A FILTER.
#
# contains_pronoun() is the first branch of the router: if it returns False the
# question is never rewritten, whatever the conversation history holds. Left in
# French ("sa", "son", "ses", "ca", "cela") against English questions it matches
# nothing, returns False every time, and the whole chapter reports "no rewriting
# needed" — with no error and no warning. Chapter 30 depends on the same
# mechanism.
#
# The set below is deliberately NARROW, mirroring the French one: possessives
# only. "it" and "that" are far too common in English and would route ordinary
# questions to the rewriting branch by accident.
_PRONOUNS = {"its", "his", "her", "their", "theirs", "hers",
             "it", "this one", "that one"}

_ANAPHORIC_POSSESSIVES = {"its", "his", "her", "their", "theirs", "hers"}


def contains_pronoun(question: str) -> bool:
    """True if the question depends on an ambiguous pronoun, and so on a context."""
    toks = _tokens(question)
    # Possessives at the head of a noun phrase are what we are really after.
    return any(p in toks for p in _ANAPHORIC_POSSESSIVES)


def extract_subject(history: Sequence[str]) -> Optional[str]:
    """Extract the last subject (entity) mentioned in the history.

    A phrase of the form "<component> <code>" is sought ("pump P-42", "motor
    M-18") in the previous turns, the most recent first.
 """
    pattern = re.compile(r"\b(pump|motor|valve|circuit)\s+([A-Za-z]+-?\d+)\b",
                         re.IGNORECASE)
    for turn in reversed(list(history)):
        m = pattern.search(turn)
        if m:
            return f"{m.group(1).lower()} {m.group(2).upper()}"
    return None


def rewriting(question: str, history: Sequence[str]) -> str:
    """Rewrite a conversational question into a self-contained one.

    The pronoun ("its", "their") is replaced by the subject found in the
    history, so that the question can be understood ALONE by the search engine,
    which knows nothing of the thread of the dialogue.
 """
    subject = extract_subject(history)
    if not subject:
        return question
    q = question
    # Replace "its/his/their <noun phrase>" with "the <noun phrase> of <subject>",
    # placing the complement straight after the qualified noun so the sentence
    # reads naturally. The noun phrase may be one or two words ("safety
    # procedure"), which is why the second group allows an optional word.
    q = re.sub(r"\b(its|his|her|their)\s+(\w+(?:\s+\w+)?)",
               lambda m: f"the {m.group(2)} of {subject}", q, flags=re.IGNORECASE)
    # Replace a bare "it" or "that one" with the subject.
    q = re.sub(r"\b(that one|this one)\b", subject, q, flags=re.IGNORECASE)
    return q


# ===========================================================================
# ROUTEUR — to choose the transformation selon the type of question
# ===========================================================================
def router(question: str, history: Optional[Sequence[str]] = None) -> str:
    """Decide which transformation strategy to apply.

    In order of priority, the most specific first:
      1. an unresolved pronoun -> 'rewriting'
      2. a comparison or compound question -> 'decomposition'
 3. cas individuel too pointu -> 'step_back'
      4. the vocabulary of the problem -> 'hyde'
 5. sinon (question vague) -> 'expansion'
 """
    q = question.lower()
    if history and contains_pronoun(question):
        return "rewriting"
    if re.search(r"\bcompare[sd]?\b|\bversus\b|\bvs\b", q) or \
       len(re.findall(r"\b(?:pump|motor|valve|circuit)\s+[A-Za-z]+-?\d*", q)) >= 2:
        return "decomposition"
    # An individual case: a proper noun plus an entitlement or bonus word.
    if re.search(r"\b(entitled|bonus|employee|leave|allowance)\b", q) and \
       re.search(r"\b[A-Z][a-z]+\b", question):
        return "step_back"
    # The vocabulary of the problem: the familiar words of the bridge.
    if any(word in q for word in _PROBLEM_SOLUTION_BRIDGE):
        return "hyde"
    return "expansion"


# ===========================================================================
# Metrics
# ===========================================================================
def rank_of(ranking: Sequence[int], doc: int) -> Optional[int]:
    """Rank (1-based) of a document in a ranking, or None if it is absent."""
    for r, d in enumerate(ranking, start=1):
        if d == doc:
            return r
    return None


def mrr(ranking: Sequence[int], relevant: Sequence[int]) -> float:
    """Mean Reciprocal Rank : 1 / rank of the first document relevant."""
    relevant = set(relevant)
    for rank, doc in enumerate(ranking, start=1):
        if doc in relevant:
            return 1.0 / rank
    return 0.0


def rappel_at_k(ranking: Sequence[int], relevant: Sequence[int],
                k: int = 5) -> float:
    """Recall@k : part documents relevant presents in the top k."""
    relevant = set(relevant)
    if not relevant:
        return 1.0
    trouves = sum(1 for d in ranking[:k] if d in relevant)
    return trouves / len(relevant)
