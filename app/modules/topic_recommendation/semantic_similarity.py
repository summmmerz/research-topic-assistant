# -*- coding: utf-8 -*-
"""Semantic similarity helpers for topic recommendation."""

from __future__ import annotations

import re
from typing import Iterable, List


class SemanticSimilarity:
    """TF-IDF based similarity with a deterministic token fallback."""

    def score(self, query: str, documents: Iterable[str]) -> List[float]:
        docs = [str(item or "") for item in documents]
        if not docs:
            return []
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
            matrix = vectorizer.fit_transform([query, *docs])
            return [float(item) for item in cosine_similarity(matrix[0:1], matrix[1:]).ravel()]
        except Exception:
            query_tokens = self._tokenize(query)
            scores = []
            for doc in docs:
                doc_tokens = self._tokenize(doc)
                if not query_tokens or not doc_tokens:
                    scores.append(0.0)
                else:
                    scores.append(len(query_tokens & doc_tokens) / len(query_tokens | doc_tokens))
            return scores

    def pair_score(self, query: str, document: str) -> float:
        values = self.score(query, [document])
        return values[0] if values else 0.0

    def _tokenize(self, text: str) -> set[str]:
        return {token for token in re.split(r"[\s,;:/\\()\-_，。；：、]+", str(text).lower()) if token}
