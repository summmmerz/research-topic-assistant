# -*- coding: utf-8 -*-
"""Safe knowledge graph query tool."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.modules.knowledge_graph.service import KnowledgeGraphService
from app.modules.tool.tool_manager import ToolBase


class KnowledgeGraphQueryTool(ToolBase):
    """Translate constrained user questions into graph searches or read-only Cypher."""

    def __init__(
        self,
        knowledge_graph_service: Optional[KnowledgeGraphService] = None,
        **kwargs,
    ):
        super().__init__(
            name="knowledge_graph_query",
            description="用于查询科研知识图谱实体、关系、导师方向和关键词关联",
            **kwargs,
        )
        self.knowledge_graph_service = knowledge_graph_service or KnowledgeGraphService()

    def execute(self, **params) -> Dict[str, Any]:
        question = params.get("question") or params.get("query") or ""
        cypher = params.get("cypher")
        try:
            if cypher:
                self._validate_cypher(cypher)
                rows = self.knowledge_graph_service.run_cypher(
                    cypher,
                    params.get("params") or {},
                )
                return {"success": True, "data": rows, "cypher": cypher}

            query = self._extract_search_query(question)
            results = self.knowledge_graph_service.search_entities(
                query=query,
                limit=int(params.get("limit", 8)),
            )
            details = []
            for item in results[:5]:
                detail = self.knowledge_graph_service.get_entity(item["id"])
                if detail:
                    details.append(detail)

            status = self.knowledge_graph_service.get_status()
            return {
                "success": True,
                "data": {
                    "query": query,
                    "storage": status.get("storage"),
                    "fallback_reason": status.get("fallback_reason"),
                    "results": results,
                    "details": details,
                },
            }
        except Exception as exc:
            return {"success": False, "error": str(exc), "cypher": cypher}

    def _extract_search_query(self, question: str) -> str:
        question = str(question).strip()
        key_phrases = [
            "知识图谱",
            "推荐系统",
            "选题推荐",
            "科研选题",
            "大语言模型",
            "图结构中心性分析",
            "多特征融合评分",
            "导师匹配",
            "语义相似度",
        ]
        matched_phrases = [phrase for phrase in key_phrases if phrase in question]
        if matched_phrases:
            return " ".join(dict.fromkeys(matched_phrases))

        cleaned = re.sub(r"[?？!！。,.，、；;：:\s]+", " ", question)
        stopwords = [
            "查询",
            "关系",
            "关联",
            "研究",
            "方向",
            "哪些",
            "什么",
            "导师",
            "之间",
            "如何",
            "怎么",
            "为什么",
        ]
        for word in stopwords:
            cleaned = cleaned.replace(word, " ")
        cleaned = re.sub(r"\b[和有与及的了]\b", " ", cleaned)
        tokens = [token for token in cleaned.split() if token.strip()]
        return " ".join(tokens) or question

    def _validate_cypher(self, cypher: str) -> None:
        normalized = re.sub(r"\s+", " ", cypher.strip()).upper()
        forbidden = {
            "CREATE",
            "MERGE",
            "DELETE",
            "DETACH",
            "SET",
            "REMOVE",
            "DROP",
            "LOAD CSV",
        }
        if not normalized.startswith(("MATCH ", "OPTIONAL MATCH ", "WITH ")):
            raise ValueError("Only MATCH/RETURN Cypher is allowed")
        if any(token in normalized for token in forbidden):
            raise ValueError("Write clauses are not allowed in knowledge graph queries")
