# -*- coding: utf-8 -*-
"""Entity and keyword extraction component."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, Iterable, List


class MetadataExtractor:
    STOPWORDS = {
        "研究", "系统", "方法", "基于", "应用", "分析", "设计", "实现",
        "the", "and", "for", "with", "from", "based", "using", "study",
    }

    def extract(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        rows = [dict(record) for record in records or []]
        corpus_tokens = [self._tokens(row) for row in rows]
        document_frequency = Counter(token for tokens in corpus_tokens for token in set(tokens))
        total_docs = max(len(rows), 1)

        for row, tokens in zip(rows, corpus_tokens):
            keywords = list(row.get("keywords") or [])
            scores = Counter(tokens)
            ranked = sorted(
                scores,
                key=lambda token: scores[token] * math.log((total_docs + 1) / (document_frequency[token] + 1)),
                reverse=True,
            )
            for token in ranked:
                if token not in keywords:
                    keywords.append(token)
                if len(keywords) >= 8:
                    break
            row["keywords"] = keywords
            if not row.get("research_directions"):
                row["research_directions"] = self._infer_research_directions(row)
        return rows

    def _tokens(self, row: Dict[str, Any]) -> List[str]:
        text = " ".join([str(row.get("title", "")), str(row.get("abstract", ""))])
        raw_tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9\-]{2,}", text.lower())
        return [token for token in raw_tokens if token not in self.STOPWORDS]

    def _infer_research_directions(self, row: Dict[str, Any]) -> List[str]:
        text = " ".join([row.get("title", ""), row.get("abstract", ""), " ".join(row.get("keywords", []))])
        rules = [
            ("大语言模型", ["大语言模型", "LLM", "DeepSeek", "Transformer"]),
            ("知识图谱", ["知识图谱", "图谱", "Neo4j", "Cypher"]),
            ("推荐系统", ["推荐", "个性化", "协同过滤"]),
            ("金融科技", ["金融", "风控", "量化", "FinTech"]),
            ("教育智能化", ["教育", "学习行为", "教学"]),
            ("医学智能诊疗", ["医学", "诊疗", "影像"]),
        ]
        matched = []
        for direction, needles in rules:
            if any(needle.lower() in text.lower() for needle in needles):
                matched.append(direction)
        return matched[:3]
