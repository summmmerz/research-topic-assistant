# -*- coding: utf-8 -*-
"""Metadata normalization component."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


class MetadataNormalizer:
    LIST_FIELDS = {"authors", "institution", "keywords", "funds", "research_directions"}

    def normalize(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for record in records or []:
            item = {self._clean_key(key): value for key, value in dict(record).items()}
            item["title"] = self._clean_text(item.get("title") or item.get("论文题名") or "")
            if not item["title"]:
                continue
            item["abstract"] = self._clean_text(item.get("abstract") or item.get("摘要") or "")
            item["venue"] = self._clean_text(item.get("venue") or item.get("期刊") or item.get("会议") or "")
            item["doi"] = self._clean_text(item.get("doi") or item.get("source_id") or item["title"])
            item["year"] = self._parse_year(item.get("year") or item.get("年份") or item.get("date"))
            for field in self.LIST_FIELDS:
                item[field] = self._split_items(item.get(field) or item.get(self._zh_field(field)))
            normalized.append(item)
        return normalized

    def _clean_key(self, key: Any) -> str:
        return str(key).strip()

    def _clean_text(self, value: Any) -> str:
        return re.sub(r"\s+", " ", str(value or "").strip())

    def _split_items(self, value: Any) -> List[str]:
        if isinstance(value, list):
            raw_items = value
        else:
            raw_items = re.split(r"[;,，；、|]", str(value or ""))
        seen = set()
        result = []
        for item in raw_items:
            text = self._clean_text(item)
            if text and text not in seen:
                seen.add(text)
                result.append(text)
        return result

    def _parse_year(self, value: Any):
        match = re.search(r"(19|20)\d{2}", str(value or ""))
        return int(match.group(0)) if match else None

    def _zh_field(self, field: str) -> str:
        return {
            "authors": "作者",
            "institution": "机构",
            "keywords": "关键词",
            "funds": "基金项目",
            "research_directions": "研究方向",
        }.get(field, field)
