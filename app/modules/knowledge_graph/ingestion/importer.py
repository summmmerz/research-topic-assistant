# -*- coding: utf-8 -*-
"""Neo4j import component."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.modules.knowledge_graph.schema import TYPE_TO_LABEL
from app.utils.neo4j_client import Neo4jClient


class KnowledgeGraphImporter:
    def __init__(self, neo4j_config: Optional[Dict[str, Any]] = None, client: Optional[Neo4jClient] = None):
        self.client = client or Neo4jClient(neo4j_config or {})

    def import_graph(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        if not self.client.available:
            return {"success": False, "error": self.client.last_error or "neo4j_unavailable", "nodes": 0, "edges": 0}
        node_count = 0
        edge_count = 0
        for node in graph.get("nodes", []):
            label = TYPE_TO_LABEL.get(str(node.get("type", "")), "ResearchDirection")
            props = dict(node)
            props.setdefault("name", props.get("label"))
            self.client.run_write(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                {"id": props["id"], "props": props},
            )
            node_count += 1
        for edge in graph.get("edges", []):
            rel_type = self._safe_rel_type(edge.get("relation"))
            self.client.run_write(
                f"""
                MATCH (s {{id: $source}})
                MATCH (t {{id: $target}})
                MERGE (s)-[r:{rel_type}]->(t)
                SET r.name = $relation
                """,
                edge,
            )
            edge_count += 1
        return {"success": True, "nodes": node_count, "edges": edge_count}

    def _safe_rel_type(self, value: Any) -> str:
        text = re.sub(r"\W+", "_", str(value or "RELATED_TO")).strip("_").upper()
        return text or "RELATED_TO"
