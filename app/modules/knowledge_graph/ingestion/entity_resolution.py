# -*- coding: utf-8 -*-
"""Entity resolution component."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List


class EntityResolver:
    def resolve(self, records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        resolved = []
        for record in records or []:
            item = dict(record)
            for field in ("authors", "institution", "keywords", "funds", "research_directions"):
                item[field] = self._dedupe([self._canonical(value, field) for value in item.get(field, [])])
            resolved.append(item)
        return resolved

    def _canonical(self, value: Any, field: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "").strip())
        aliases = {
            "Tsinghua University": "清华大学",
            "Peking University": "北京大学",
            "UIBE": "对外经济贸易大学",
            "LLM": "大语言模型",
            "Large Language Model": "大语言模型",
            "KG": "知识图谱",
        }
        if field in {"institution", "keywords", "research_directions"}:
            return aliases.get(text, text)
        return text

    def _dedupe(self, values: List[str]) -> List[str]:
        seen = set()
        result = []
        for value in values:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
        return result
