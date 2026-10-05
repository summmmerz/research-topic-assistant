# -*- coding: utf-8 -*-
"""Trend and hotness features derived from publication years."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional


class TrendFeatureExtractor:
    """Estimate recent growth from graph search hits when available."""

    def __init__(self, knowledge_graph_service: Optional[Any] = None):
        self.knowledge_graph_service = knowledge_graph_service

    def hotness_score(self, topic: Dict[str, Any]) -> float:
        static_score = float(topic.get("hotness", topic.get("hotness_score", 0.0)))
        if not self.knowledge_graph_service:
            return self._clamp(static_score)
        query = " ".join([str(topic.get("title", "")), str(topic.get("keywords", ""))])
        try:
            hits = self.knowledge_graph_service.search_entities(query=query, limit=30)
            years = []
            for hit in hits:
                detail = self.knowledge_graph_service.get_entity(hit["id"])
                year = (detail or {}).get("year")
                if isinstance(year, int):
                    years.append(year)
            if not years:
                return self._clamp(static_score)
            current_year = datetime.utcnow().year
            recent = sum(1 for year in years if current_year - 2 <= year <= current_year)
            previous = sum(1 for year in years if current_year - 5 <= year <= current_year - 3)
            growth = (recent - previous) / max(previous, 1)
            evidence = min(len(years) / 10.0, 1.0)
            dynamic = self._clamp(0.5 + growth * 0.25)
            return self._clamp(0.35 * static_score + 0.65 * dynamic * evidence)
        except Exception:
            return self._clamp(static_score)

    def _clamp(self, value: float) -> float:
        return max(0.0, min(1.0, value))
