# -*- coding: utf-8 -*-
"""Build graph relations from normalized metadata."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Iterable, Tuple


class RelationBuilder:
    def build(self, records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
        nodes: Dict[str, Dict[str, Any]] = {}
        edges: Dict[Tuple[str, str, str], Dict[str, str]] = {}

        for record in records or []:
            title = str(record.get("title") or "").strip()
            if not title:
                continue
            paper_id = self._stable_id("paper", record.get("doi") or title)
            keywords = list(record.get("keywords") or [])
            self._add_node(
                nodes,
                {
                    "id": paper_id,
                    "label": title,
                    "title": title,
                    "type": "论文",
                    "year": record.get("year"),
                    "summary": record.get("abstract", ""),
                    "abstract": record.get("abstract", ""),
                    "keywords": keywords,
                    "source_id": record.get("doi") or title,
                    "source": record.get("source", "metadata_export"),
                },
            )

            for author in record.get("authors", []):
                author_id = self._stable_id("author", author)
                self._add_node(nodes, {"id": author_id, "label": author, "name": author, "type": "作者", "keywords": keywords})
                self._add_edge(edges, author_id, paper_id, "WROTE")

            for institution in record.get("institution", []):
                org_id = self._stable_id("institution", institution)
                self._add_node(nodes, {"id": org_id, "label": institution, "name": institution, "type": "机构", "keywords": keywords})
                self._add_edge(edges, paper_id, org_id, "AFFILIATED_WITH")

            for keyword in keywords:
                keyword_id = self._stable_id("keyword", keyword)
                self._add_node(nodes, {"id": keyword_id, "label": keyword, "name": keyword, "type": "关键词", "keywords": [keyword]})
                self._add_edge(edges, paper_id, keyword_id, "HAS_KEYWORD")

            for direction in record.get("research_directions", []):
                direction_id = self._stable_id("direction", direction)
                self._add_node(nodes, {"id": direction_id, "label": direction, "name": direction, "type": "研究方向", "keywords": keywords})
                self._add_edge(edges, paper_id, direction_id, "BELONGS_TO")
                for keyword in keywords[:5]:
                    self._add_edge(edges, self._stable_id("keyword", keyword), direction_id, "RELATED_TO")

            venue = str(record.get("venue") or "").strip()
            if venue:
                venue_id = self._stable_id("venue", venue)
                self._add_node(nodes, {"id": venue_id, "label": venue, "name": venue, "type": "期刊", "keywords": keywords})
                self._add_edge(edges, paper_id, venue_id, "PUBLISHED_IN")

            for fund in record.get("funds", []):
                fund_id = self._stable_id("fund", fund)
                self._add_node(nodes, {"id": fund_id, "label": fund, "name": fund, "type": "基金项目", "keywords": keywords})
                self._add_edge(edges, paper_id, fund_id, "FUNDED_BY")

        return {"nodes": list(nodes.values()), "edges": list(edges.values())}

    def _stable_id(self, prefix: str, value: Any) -> str:
        digest = hashlib.sha1(str(value or "").strip().lower().encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{digest}"

    def _add_node(self, nodes: Dict[str, Dict[str, Any]], node: Dict[str, Any]) -> None:
        existing = nodes.get(node["id"])
        if existing:
            existing_keywords = set(existing.get("keywords", []))
            existing_keywords.update(node.get("keywords", []))
            existing["keywords"] = sorted(existing_keywords)
            for key, value in node.items():
                if value and not existing.get(key):
                    existing[key] = value
            return
        nodes[node["id"]] = node

    def _add_edge(self, edges: Dict[Tuple[str, str, str], Dict[str, str]], source: str, target: str, relation: str) -> None:
        edges[(source, target, relation)] = {"source": source, "target": target, "relation": relation}
