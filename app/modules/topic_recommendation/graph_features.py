# -*- coding: utf-8 -*-
"""Knowledge graph derived recommendation features."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional


class GraphFeatureExtractor:
    """Query graph centrality and mentor keywords with JSON fallback support."""

    def __init__(self, knowledge_graph_service: Optional[Any] = None):
        self.knowledge_graph_service = knowledge_graph_service

    def centrality_score(self, topic: Dict[str, Any]) -> float:
        if not self.knowledge_graph_service:
            return self._clamp(float(topic.get("centrality", topic.get("centrality_score", 0.0))))
        query = " ".join([str(topic.get("title", "")), self._keyword_text(topic.get("keywords"))])
        try:
            hits = self.knowledge_graph_service.search_entities(query=query, limit=8)
        except Exception:
            hits = []
        if not hits:
            return self._clamp(float(topic.get("centrality", topic.get("centrality_score", 0.0))))
        try:
            graph_size = float(self.knowledge_graph_service.get_status().get("total_nodes", 10))
        except Exception:
            graph_size = 10.0
        best_degree = max(float(item.get("degree", 0)) for item in hits)
        best = min(best_degree / max(graph_size ** 0.5, 1.0), 1.0)
        return self._clamp(best)

    def mentor_keywords(self, mentor: Optional[Dict[str, Any]]) -> str:
        if not mentor:
            return ""
        name = str(mentor.get("name", "")).strip()
        if self.knowledge_graph_service and name:
            try:
                hits = self.knowledge_graph_service.search_entities(query=name, limit=3)
                keywords = []
                for hit in hits:
                    detail = self.knowledge_graph_service.get_entity(hit["id"])
                    if detail:
                        keywords.extend(detail.get("keywords", []))
                        keywords.extend(node.get("label", "") for node in detail.get("related_nodes", []))
                if keywords:
                    return " ".join(str(item) for item in keywords if item)
            except Exception:
                pass
        return " ".join(
            str(mentor.get(key, ""))
            for key in ("name", "research", "keywords")
            if mentor.get(key)
        )

    def _keyword_text(self, keywords: Any) -> str:
        if isinstance(keywords, Iterable) and not isinstance(keywords, str):
            return " ".join(str(item) for item in keywords)
        return str(keywords or "")

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
