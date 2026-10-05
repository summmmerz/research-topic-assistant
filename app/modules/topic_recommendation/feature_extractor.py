# -*- coding: utf-8 -*-
"""Facade combining semantic, graph and trend recommendation features."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .graph_features import GraphFeatureExtractor
from .semantic_similarity import SemanticSimilarity
from .trend_features import TrendFeatureExtractor


class RecommendationFeatureExtractor:
    def __init__(self, knowledge_graph_service: Optional[Any] = None):
        self.semantic = SemanticSimilarity()
        self.graph = GraphFeatureExtractor(knowledge_graph_service)
        self.trend = TrendFeatureExtractor(knowledge_graph_service)

    def semantic_score(self, topic: Dict[str, Any], user_interest: str) -> float:
        text = " ".join(
            [
                str(topic.get("title", "")),
                str(topic.get("description", "")),
                str(topic.get("keywords", "")),
            ]
        )
        return self.semantic.pair_score(user_interest, text)

    def hotness_score(self, topic: Dict[str, Any]) -> float:
        return self.trend.hotness_score(topic)

    def centrality_score(self, topic: Dict[str, Any]) -> float:
        return self.graph.centrality_score(topic)

    def mentor_text(self, mentor: Optional[Dict[str, Any]]) -> str:
        return self.graph.mentor_keywords(mentor)
