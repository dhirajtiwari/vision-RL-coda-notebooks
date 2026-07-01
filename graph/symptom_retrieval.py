"""
Hybrid symptom retrieval: lexical token overlap + TF-IDF cosine similarity.

Improves paraphrase matching without external embedding APIs or heavy ML deps.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]


def _tfidf_vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    if not tokens:
        return {}
    tf = Counter(tokens)
    total = len(tokens)
    return {term: (count / total) * idf.get(term, 0.0) for term, count in tf.items()}


def _cosine_sparse(a: dict[str, float], b: dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a.get(k, 0.0) * b.get(k, 0.0) for k in set(a) | set(b))
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_idf(corpus: Iterable[str]) -> dict[str, float]:
    docs = [_tokenize(doc) for doc in corpus]
    n = max(len(docs), 1)
    df: Counter[str] = Counter()
    for tokens in docs:
        df.update(set(tokens))
    return {term: math.log((1 + n) / (1 + count)) + 1.0 for term, count in df.items()}


def tfidf_similarity(query: str, document: str, corpus: list[str]) -> float:
    """Cosine similarity between query and document in a shared TF-IDF space."""
    full_corpus = list(corpus) + [query, document]
    idf = build_idf(full_corpus)
    q_vec = _tfidf_vector(_tokenize(query), idf)
    d_vec = _tfidf_vector(_tokenize(document), idf)
    return round(_cosine_sparse(q_vec, d_vec), 3)


def hybrid_symptom_score(
    user_message: str,
    symptom_description: str,
    *,
    lexical_score: float,
    corpus: list[str] | None = None,
    lexical_weight: float = 0.45,
) -> float:
    """
    Blend lexical and TF-IDF scores.
    Uses max-boost when both signals agree (score > 0.35).
    """
    corp = corpus or [symptom_description]
    semantic = tfidf_similarity(user_message, symptom_description, corp)
    blended = lexical_weight * lexical_score + (1.0 - lexical_weight) * semantic
    if lexical_score >= 0.3 and semantic >= 0.3:
        blended = max(blended, lexical_score, semantic)
    return round(min(blended, 1.0), 2)
