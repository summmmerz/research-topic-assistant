# -*- coding: utf-8 -*-
"""
Knowledge graph service backed by a local JSON file.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Set

from .neo4j_repository import Neo4jKnowledgeGraphRepository


class KnowledgeGraphService:
    """Load, query and summarize the local research knowledge graph."""

    DEFAULT_GRAPH = {
        "nodes": [
            {
                "id": "domain_cs",
                "label": "计算机科学",
                "type": "领域",
                "summary": "系统当前重点覆盖的学科领域之一。",
                "keywords": ["人工智能", "知识图谱", "推荐系统"],
            },
            {
                "id": "domain_finance",
                "label": "金融学",
                "type": "领域",
                "summary": "系统当前重点覆盖的第二个学科领域。",
                "keywords": ["金融科技", "风险管理", "量化分析"],
            },
            {
                "id": "paper_llm_topic",
                "label": "大语言模型驱动的科研选题辅助系统设计",
                "type": "论文",
                "year": 2026,
                "summary": "围绕科研选题辅助、知识图谱与交互式推荐展开的系统论文。",
                "keywords": ["大语言模型", "科研选题", "知识图谱", "智能体"],
            },
            {
                "id": "paper_kg_recommendation",
                "label": "知识图谱增强的科研选题推荐方法",
                "type": "论文",
                "year": 2025,
                "summary": "研究知识图谱在选题推荐中的可解释性价值。",
                "keywords": ["知识图谱", "推荐系统", "可解释性"],
            },
            {
                "id": "paper_fintech_llm",
                "label": "金融风控场景下的大模型辅助分析",
                "type": "论文",
                "year": 2025,
                "summary": "探讨大模型在金融风控分析中的应用边界。",
                "keywords": ["金融科技", "大模型", "风险控制"],
            },
            {
                "id": "author_student",
                "label": "学生A",
                "type": "作者",
                "summary": "本科毕业设计学生代称。",
                "keywords": ["人工智能", "科研辅助"],
            },
            {
                "id": "author_teacher",
                "label": "教师B",
                "type": "作者",
                "summary": "指导教师代称。",
                "keywords": ["大模型", "知识图谱", "推荐系统"],
            },
            {
                "id": "org_uibe",
                "label": "对外经济贸易大学",
                "type": "机构",
                "summary": "项目所属学校与研究背景场景。",
                "keywords": ["人工智能", "金融学", "科研训练"],
            },
            {
                "id": "kw_llm",
                "label": "大语言模型",
                "type": "关键词",
                "summary": "系统的智能交互与文本生成核心能力来源。",
                "keywords": ["LLM", "自然语言处理"],
            },
            {
                "id": "kw_kg",
                "label": "知识图谱",
                "type": "关键词",
                "summary": "承载论文、作者、机构、关键词关系的结构化网络。",
                "keywords": ["图结构", "知识组织"],
            },
            {
                "id": "kw_recommendation",
                "label": "选题推荐",
                "type": "关键词",
                "summary": "面向研究生科研起步阶段的个性化推荐任务。",
                "keywords": ["推荐", "可解释性"],
            },
            {
                "id": "kw_agent",
                "label": "科研智能体",
                "type": "关键词",
                "summary": "整合大模型、工具调用和上下文记忆的智能代理。",
                "keywords": ["智能体", "工具调用"],
            },
            {
                "id": "method_graph",
                "label": "图结构中心性分析",
                "type": "方法",
                "summary": "用于衡量关键词和研究方向的重要性。",
                "keywords": ["中心性", "PageRank", "图算法"],
            },
            {
                "id": "method_similarity",
                "label": "多特征融合评分",
                "type": "方法",
                "summary": "综合兴趣匹配、热度、中心性、创新性与导师契合度。",
                "keywords": ["排序", "多特征", "推荐算法"],
            },
            {
                "id": "topic_ai_edu",
                "label": "人工智能赋能教育",
                "type": "研究方向",
                "summary": "系统所属更大研究背景。",
                "keywords": ["教育智能化", "个性化培养"],
            },
            {
                "id": "topic_fintech",
                "label": "金融科技风险分析",
                "type": "研究方向",
                "summary": "金融学方向的延展研究场景。",
                "keywords": ["金融科技", "风险管理", "可解释AI"],
            },
        ],
        "edges": [
            {"source": "author_student", "target": "paper_llm_topic", "relation": "撰写"},
            {"source": "author_teacher", "target": "paper_llm_topic", "relation": "指导"},
            {"source": "org_uibe", "target": "author_student", "relation": "培养"},
            {"source": "org_uibe", "target": "author_teacher", "relation": "任职"},
            {"source": "paper_llm_topic", "target": "kw_llm", "relation": "研究主题"},
            {"source": "paper_llm_topic", "target": "kw_kg", "relation": "研究主题"},
            {"source": "paper_llm_topic", "target": "kw_recommendation", "relation": "研究主题"},
            {"source": "paper_llm_topic", "target": "kw_agent", "relation": "研究主题"},
            {"source": "paper_llm_topic", "target": "topic_ai_edu", "relation": "服务场景"},
            {"source": "paper_llm_topic", "target": "method_similarity", "relation": "采用方法"},
            {"source": "paper_llm_topic", "target": "method_graph", "relation": "采用方法"},
            {"source": "paper_kg_recommendation", "target": "kw_kg", "relation": "研究主题"},
            {"source": "paper_kg_recommendation", "target": "kw_recommendation", "relation": "研究主题"},
            {"source": "paper_kg_recommendation", "target": "method_graph", "relation": "采用方法"},
            {"source": "paper_fintech_llm", "target": "kw_llm", "relation": "研究主题"},
            {"source": "paper_fintech_llm", "target": "topic_fintech", "relation": "服务场景"},
            {"source": "paper_fintech_llm", "target": "domain_finance", "relation": "属于"},
            {"source": "paper_llm_topic", "target": "domain_cs", "relation": "属于"},
            {"source": "paper_kg_recommendation", "target": "domain_cs", "relation": "属于"},
            {"source": "kw_kg", "target": "kw_recommendation", "relation": "增强"},
            {"source": "kw_llm", "target": "kw_agent", "relation": "驱动"},
            {"source": "kw_kg", "target": "method_graph", "relation": "依赖"},
            {"source": "kw_recommendation", "target": "method_similarity", "relation": "依赖"},
            {"source": "topic_ai_edu", "target": "domain_cs", "relation": "关联领域"},
            {"source": "topic_fintech", "target": "domain_finance", "relation": "关联领域"},
        ],
    }

    def __init__(
        self,
        graph_path: Optional[str] = None,
        neo4j_config: Optional[Dict[str, Any]] = None,
        prefer_neo4j: bool = True,
    ):
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.graph_path = graph_path or os.path.join(project_root, "data", "knowledge_graph.json")
        self.neo4j_repository = None
        self.storage = "json_fallback"
        self.storage_error: Optional[str] = None
        if prefer_neo4j and graph_path is None:
            config = neo4j_config if neo4j_config is not None else self._load_neo4j_config(project_root)
            self.neo4j_repository = Neo4jKnowledgeGraphRepository(config)
            if self.neo4j_repository.available:
                self.storage = "neo4j"
            else:
                self.storage_error = self.neo4j_repository.client.last_error
        self._graph = self._load_graph()
        self._index_graph()

    def _load_neo4j_config(self, project_root: str) -> Dict[str, Any]:
        config_path = os.path.join(os.path.dirname(project_root), "config", "config.json")
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                return (json.load(file) or {}).get("neo4j", {})
        except Exception:
            return {}

    def _load_graph(self) -> Dict[str, List[Dict[str, Any]]]:
        if not os.path.exists(self.graph_path):
            os.makedirs(os.path.dirname(self.graph_path), exist_ok=True)
            with open(self.graph_path, "w", encoding="utf-8") as file:
                json.dump(self.DEFAULT_GRAPH, file, ensure_ascii=False, indent=2)

        with open(self.graph_path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        return {
            "nodes": payload.get("nodes", []),
            "edges": payload.get("edges", []),
        }

    def _index_graph(self) -> None:
        self.nodes_by_id: Dict[str, Dict[str, Any]] = {
            node["id"]: deepcopy(node) for node in self._graph["nodes"]
        }
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)
        self.edges_by_node: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

        for edge in self._graph["edges"]:
            source = edge["source"]
            target = edge["target"]
            self.adjacency[source].add(target)
            self.adjacency[target].add(source)
            self.edges_by_node[source].append(edge)
            self.edges_by_node[target].append(edge)

        for node_id, node in self.nodes_by_id.items():
            node["degree"] = len(self.adjacency.get(node_id, set()))

    def get_status(self) -> Dict[str, Any]:
        if self.storage == "neo4j" and self.neo4j_repository:
            try:
                return self.neo4j_repository.get_status()
            except Exception as exc:
                self.storage = "json_fallback"
                self.storage_error = str(exc)

        type_counter = Counter(node.get("type", "未分类") for node in self.nodes_by_id.values())
        total_edges = len(self._graph["edges"])
        total_nodes = len(self.nodes_by_id)
        density = 0.0
        if total_nodes > 1:
            density = round((2 * total_edges) / (total_nodes * (total_nodes - 1)), 4)

        return {
            "storage": "json_fallback",
            "fallback_reason": self.storage_error,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "entity_types": dict(type_counter),
            "density": density,
            "top_nodes": self.get_top_nodes(limit=5),
        }

    def get_top_nodes(self, limit: int = 5) -> List[Dict[str, Any]]:
        ranked = sorted(
            self.nodes_by_id.values(),
            key=lambda item: (item.get("degree", 0), item.get("label", "")),
            reverse=True,
        )
        return [
            {
                "id": item["id"],
                "label": item["label"],
                "type": item.get("type", "未分类"),
                "degree": item.get("degree", 0),
            }
            for item in ranked[:limit]
        ]

    def search_entities(
        self,
        query: str = "",
        entity_types: Optional[Iterable[str]] = None,
        limit: int = 12,
    ) -> List[Dict[str, Any]]:
        if self.storage == "neo4j" and self.neo4j_repository:
            try:
                return self.neo4j_repository.search_entities(query, entity_types, limit)
            except Exception as exc:
                self.storage = "json_fallback"
                self.storage_error = str(exc)

        entity_type_set = {item for item in entity_types or [] if item}
        lowered = query.strip().lower()
        query_terms = [term for term in lowered.split() if term]
        results: List[Dict[str, Any]] = []

        for node in self.nodes_by_id.values():
            if entity_type_set and node.get("type") not in entity_type_set:
                continue

            haystack = " ".join(
                [
                    str(node.get("label", "")),
                    str(node.get("summary", "")),
                    " ".join(node.get("keywords", [])),
                ]
            ).lower()

            score = 0
            if lowered:
                if lowered in haystack:
                    score += 10
                if query_terms:
                    matched_terms = [term for term in query_terms if term in haystack]
                    if not matched_terms:
                        continue
                    score += len(matched_terms)
                elif score == 0:
                    continue

            results.append(
                {
                    "id": node["id"],
                    "label": node["label"],
                    "type": node.get("type", "未分类"),
                    "summary": node.get("summary", ""),
                    "degree": node.get("degree", 0),
                    "_score": score,
                }
            )

        results.sort(key=lambda item: (item["_score"], item["degree"], item["label"]), reverse=True)
        for item in results:
            item.pop("_score", None)
        return results[:limit]

    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        if self.storage == "neo4j" and self.neo4j_repository:
            try:
                return self.neo4j_repository.get_entity(entity_id)
            except Exception as exc:
                self.storage = "json_fallback"
                self.storage_error = str(exc)

        node = self.nodes_by_id.get(entity_id)
        if not node:
            return None

        related_edges = self.edges_by_node.get(entity_id, [])
        related_nodes = []
        for neighbor_id in self.adjacency.get(entity_id, set()):
            neighbor = self.nodes_by_id.get(neighbor_id)
            if neighbor:
                related_nodes.append(
                    {
                        "id": neighbor["id"],
                        "label": neighbor["label"],
                        "type": neighbor.get("type", "未分类"),
                        "degree": neighbor.get("degree", 0),
                    }
                )

        related_nodes.sort(key=lambda item: (item["degree"], item["label"]), reverse=True)

        return {
            **deepcopy(node),
            "related_nodes": related_nodes[:10],
            "related_edges": deepcopy(related_edges[:20]),
        }

    def get_visualization(
        self,
        entity_types: Optional[Iterable[str]] = None,
        max_nodes: int = 40,
        query: str = "",
        focus_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.storage == "neo4j" and self.neo4j_repository:
            try:
                payload = self.neo4j_repository.get_visualization(
                    entity_types=entity_types,
                    max_nodes=max_nodes,
                    query=query,
                    focus_id=focus_id,
                )
                payload["storage"] = "neo4j"
                return payload
            except Exception as exc:
                self.storage = "json_fallback"
                self.storage_error = str(exc)

        entity_type_set = {item for item in entity_types or [] if item}
        max_nodes = max(5, min(int(max_nodes or 40), 120))

        if focus_id and focus_id in self.nodes_by_id:
            node_ids = {focus_id, *self.adjacency.get(focus_id, set())}
        else:
            search_hits = self.search_entities(query=query, entity_types=entity_types, limit=max_nodes)
            node_ids = {item["id"] for item in search_hits}
            if not node_ids:
                candidates = [
                    node
                    for node in self.nodes_by_id.values()
                    if not entity_type_set or node.get("type") in entity_type_set
                ]
                candidates.sort(key=lambda item: (item.get("degree", 0), item.get("label", "")), reverse=True)
                node_ids = {item["id"] for item in candidates[:max_nodes]}

        expanded_ids = set(node_ids)
        for node_id in list(node_ids):
            if len(expanded_ids) >= max_nodes:
                break
            for neighbor in sorted(
                self.adjacency.get(node_id, set()),
                key=lambda item: self.nodes_by_id[item].get("degree", 0),
                reverse=True,
            ):
                expanded_ids.add(neighbor)
                if len(expanded_ids) >= max_nodes:
                    break

        nodes = [self._serialize_node(self.nodes_by_id[node_id]) for node_id in expanded_ids]
        edges = [
            deepcopy(edge)
            for edge in self._graph["edges"]
            if edge["source"] in expanded_ids and edge["target"] in expanded_ids
        ]
        legend = self._build_legend(nodes)

        return {
            "storage": "json_fallback",
            "nodes": nodes,
            "edges": edges,
            "legend": legend,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
            },
        }

    def run_cypher(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if self.neo4j_repository and self.neo4j_repository.available:
            return self.neo4j_repository.run_cypher(query, params or {})
        raise RuntimeError(self.storage_error or "neo4j_unavailable")

    def _serialize_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": node["id"],
            "label": node["label"],
            "type": node.get("type", "未分类"),
            "summary": node.get("summary", ""),
            "keywords": node.get("keywords", []),
            "year": node.get("year"),
            "degree": node.get("degree", 0),
        }

    def _build_legend(self, nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        counter = Counter(node["type"] for node in nodes)
        return [
            {"type": entity_type, "count": count}
            for entity_type, count in sorted(counter.items(), key=lambda item: item[0])
        ]
