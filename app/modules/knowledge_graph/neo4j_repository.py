# -*- coding: utf-8 -*-
"""Neo4j repository for the research knowledge graph."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional

from app.utils.neo4j_client import Neo4jClient


class Neo4jKnowledgeGraphRepository:
    """Read-only repository used by services and tools."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, client: Optional[Neo4jClient] = None):
        self.client = client or Neo4jClient(config or {})

    @property
    def available(self) -> bool:
        return self.client.available

    def get_status(self) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError(self.client.last_error or "neo4j_unavailable")
        rows = self.client.run_read(
            """
            MATCH (n)
            WITH labels(n)[0] AS label, count(n) AS count
            RETURN label, count
            ORDER BY label
            """
        )
        rel_rows = self.client.run_read("MATCH ()-[r]->() RETURN count(r) AS total_edges")
        top_rows = self.client.run_read(
            """
            MATCH (n)
            WITH n, COUNT { (n)--() } AS degree
            RETURN coalesce(n.id, elementId(n)) AS id,
                   coalesce(n.title, n.name, n.label, n.id) AS label,
                   labels(n)[0] AS type,
                   degree
            ORDER BY degree DESC, label ASC
            LIMIT 5
            """
        )
        total_nodes = sum(int(row["count"]) for row in rows)
        total_edges = int(rel_rows[0]["total_edges"]) if rel_rows else 0
        density = 0.0
        if total_nodes > 1:
            density = round((2 * total_edges) / (total_nodes * (total_nodes - 1)), 4)
        return {
            "storage": "neo4j",
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "entity_types": {row["label"] or "Unknown": int(row["count"]) for row in rows},
            "density": density,
            "top_nodes": top_rows,
        }

    def search_entities(
        self, query: str = "", entity_types: Optional[Iterable[str]] = None, limit: int = 12
    ) -> List[Dict[str, Any]]:
        if not self.available:
            raise RuntimeError(self.client.last_error or "neo4j_unavailable")
        labels = [item for item in entity_types or [] if item]
        cypher = """
            MATCH (n)
            WHERE ($query = "" OR toLower(coalesce(n.title, n.name, n.label, n.summary, "")) CONTAINS toLower($query)
                   OR any(k IN coalesce(n.keywords, []) WHERE toLower(toString(k)) CONTAINS toLower($query)))
              AND (size($labels) = 0 OR any(label IN labels(n) WHERE label IN $labels))
            WITH n, COUNT { (n)--() } AS degree
            RETURN coalesce(n.id, elementId(n)) AS id,
                   coalesce(n.title, n.name, n.label, n.id) AS label,
                   labels(n)[0] AS type,
                   coalesce(n.summary, n.abstract, "") AS summary,
                   degree
            ORDER BY degree DESC, label ASC
            LIMIT $limit
        """
        return self.client.run_read(cypher, {"query": query or "", "labels": labels, "limit": int(limit)})

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if not self.available:
            raise RuntimeError(self.client.last_error or "neo4j_unavailable")
        rows = self.client.run_read(
            """
            MATCH (n)
            WHERE n.id = $entity_id OR elementId(n) = $entity_id
            OPTIONAL MATCH (n)-[r]-(m)
            WITH n, collect(DISTINCT {
                id: coalesce(m.id, elementId(m)),
                label: coalesce(m.title, m.name, m.label, m.id),
                type: labels(m)[0],
                degree: COUNT { (m)--() }
            }) AS related_nodes,
            collect(DISTINCT {
                source: coalesce(startNode(r).id, elementId(startNode(r))),
                target: coalesce(endNode(r).id, elementId(endNode(r))),
                relation: type(r)
            }) AS related_edges
            RETURN properties(n) AS props,
                   coalesce(n.id, elementId(n)) AS id,
                   coalesce(n.title, n.name, n.label, n.id) AS label,
                   labels(n)[0] AS type,
                   related_nodes,
                   related_edges
            LIMIT 1
            """,
            {"entity_id": entity_id},
        )
        if not rows:
            return None
        row = rows[0]
        return {
            **dict(row.get("props") or {}),
            "id": row["id"],
            "label": row["label"],
            "type": row["type"],
            "related_nodes": [item for item in row["related_nodes"] if item.get("id")],
            "related_edges": [item for item in row["related_edges"] if item.get("source")],
        }

    def get_visualization(
        self,
        entity_types: Optional[Iterable[str]] = None,
        max_nodes: int = 40,
        query: str = "",
        focus_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError(self.client.last_error or "neo4j_unavailable")
        labels = [item for item in entity_types or [] if item]
        max_nodes = max(5, min(int(max_nodes or 40), 120))
        if focus_id:
            cypher = """
                MATCH (n)
                WHERE n.id = $focus_id OR elementId(n) = $focus_id
                MATCH path = (n)-[*0..1]-(m)
                WITH collect(DISTINCT m)[0..$limit] AS nodes
                UNWIND nodes AS node
                OPTIONAL MATCH (node)-[r]-(other)
                WHERE other IN nodes
                RETURN collect(DISTINCT node) AS ns, collect(DISTINCT r) AS rs
            """
            params = {"focus_id": focus_id, "limit": max_nodes}
        else:
            cypher = """
                MATCH (n)
                WHERE ($query = "" OR toLower(coalesce(n.title, n.name, n.label, n.summary, "")) CONTAINS toLower($query)
                       OR any(k IN coalesce(n.keywords, []) WHERE toLower(toString(k)) CONTAINS toLower($query)))
                  AND (size($labels) = 0 OR any(label IN labels(n) WHERE label IN $labels))
                WITH n, COUNT { (n)--() } AS degree
                ORDER BY degree DESC
                LIMIT $limit
                WITH collect(n) AS nodes
                UNWIND nodes AS node
                OPTIONAL MATCH (node)-[r]-(other)
                WHERE other IN nodes
                RETURN collect(DISTINCT node) AS ns, collect(DISTINCT r) AS rs
            """
            params = {"query": query or "", "labels": labels, "limit": max_nodes}
        rows = self.client.run_read(cypher, params)
        if not rows:
            return {"nodes": [], "edges": [], "legend": [], "stats": {"node_count": 0, "edge_count": 0}}
        # The official driver returns Node/Relationship objects here.
        nodes = [self._serialize_node(node) for node in rows[0].get("ns", [])]
        edges = [self._serialize_edge(edge) for edge in rows[0].get("rs", []) if edge is not None]
        legend: Dict[str, int] = {}
        for node in nodes:
            legend[node["type"]] = legend.get(node["type"], 0) + 1
        return {
            "nodes": nodes,
            "edges": edges,
            "legend": [{"type": key, "count": value} for key, value in sorted(legend.items())],
            "stats": {"node_count": len(nodes), "edge_count": len(edges)},
        }

    def run_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self.available:
            raise RuntimeError(self.client.last_error or "neo4j_unavailable")
        self._validate_readonly_cypher(query)
        return self.client.run_read(query, params or {})

    def _validate_readonly_cypher(self, query: str) -> None:
        normalized = re.sub(r"\s+", " ", query.strip()).upper()
        forbidden = {"CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP", "CALL DBMS"}
        if not normalized.startswith(("MATCH ", "OPTIONAL MATCH ", "WITH ")):
            raise ValueError("Only read-only MATCH/RETURN Cypher queries are allowed")
        if any(token in normalized for token in forbidden):
            raise ValueError("Write Cypher clauses are not allowed")

    def _serialize_node(self, node: Any) -> Dict[str, Any]:
        props = dict(node)
        node_id = props.get("id") or getattr(node, "element_id", None)
        label = props.get("title") or props.get("name") or props.get("label") or node_id
        labels = list(getattr(node, "labels", []) or [])
        return {
            "id": node_id,
            "label": label,
            "type": labels[0] if labels else props.get("type", "Unknown"),
            "summary": props.get("summary") or props.get("abstract", ""),
            "keywords": props.get("keywords", []),
            "year": props.get("year"),
            "degree": props.get("degree", 0),
        }

    def _serialize_edge(self, edge: Any) -> Dict[str, Any]:
        start_node = getattr(edge, "start_node", None)
        end_node = getattr(edge, "end_node", None)
        return {
            "source": (dict(start_node).get("id") if start_node else None) or getattr(start_node, "element_id", None),
            "target": (dict(end_node).get("id") if end_node else None) or getattr(end_node, "element_id", None),
            "relation": getattr(edge, "type", None) or edge.__class__.__name__,
        }
