"""
Hybrid symptom retrieval: lexical token overlap + TF-IDF cosine similarity.

Improves paraphrase matching without external embedding APIs or heavy ML deps.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Iterable

# Phrase-level rewrite: customer language → catalog-friendly tokens (not free-form synonym soup)
_QUERY_REWRITES: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(
            r"\b(not\s+start(?:ing)?|won'?t\s+start|will\s+not\s+start|doesn'?t\s+start|"
            r"not\s+turn(?:ing)?\s+on|won'?t\s+turn\s+on|no\s+power|powered?\s+off|dead|won'?t\s+power)\b",
            re.I,
        ),
        " will not start turn on power up unit",
    ),
    (re.compile(r"\b(not\s+spin(?:ning)?|won'?t\s+spin)\b", re.I), " will not spin drum"),
    (re.compile(r"\b(not\s+drain(?:ing)?|won'?t\s+drain)\b", re.I), " will not drain pump"),
    (re.compile(r"\b(not\s+(?:make|making)\s+ice|no\s+ice)\b", re.I), " not producing ice maker"),
]


def normalize_query_text(text: str) -> str:
    """Expand common customer fault phrases before tokenization / TF-IDF."""
    out = text or ""
    for pattern, suffix in _QUERY_REWRITES:
        if pattern.search(out):
            out = out + suffix
    return out


def _tokenize(text: str) -> list[str]:
    text = normalize_query_text(text)
    raw = [t for t in re.findall(r"[a-z0-9']+", text.lower()) if len(t) > 2]
    return [t.replace("'", "") for t in raw if len(t.replace("'", "")) > 2]


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
    q = normalize_query_text(user_message)
    corp = corpus or [symptom_description]
    semantic = tfidf_similarity(q, symptom_description, corp)
    # Recompute lexical on normalized query so phrase rewrites count

    q_tok, d_tok = set(_tokenize(q)), set(_tokenize(symptom_description))
    if q_tok and d_tok:
        lexical_norm = len(q_tok & d_tok) / max(len(q_tok), 1)
        lexical_score = max(lexical_score, lexical_norm)
    blended = lexical_weight * lexical_score + (1.0 - lexical_weight) * semantic
    if lexical_score >= 0.3 and semantic >= 0.3:
        blended = max(blended, lexical_score, semantic)
    return round(min(blended, 1.0), 2)
