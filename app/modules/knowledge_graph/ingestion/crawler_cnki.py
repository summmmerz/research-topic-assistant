# -*- coding: utf-8 -*-
"""CNKI import adapter for user-provided legal exports.

The project should not scrape CNKI pages directly. This adapter reads legal
CSV/JSON exports and normalizes common Chinese field names into the internal
metadata schema used by the knowledge graph pipeline.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, Iterable, List


class CNKIImportAdapter:
    FIELD_MAP = {
        "题名": "title",
        "论文题名": "title",
        "标题": "title",
        "作者": "authors",
        "作者单位": "institution",
        "机构": "institution",
        "关键词": "keywords",
        "摘要": "abstract",
        "年份": "year",
        "发表时间": "year",
        "期刊": "venue",
        "来源": "venue",
        "基金": "funds",
        "基金项目": "funds",
        "DOI": "doi",
    }

    def collect(self, source_path: str) -> List[Dict[str, Any]]:
        records = self._load_records(source_path)
        normalized = []
        for record in records:
            item = self._map_record(record)
            item["source"] = item.get("source") or "cnki_export"
            if item.get("title"):
                normalized.append(item)
        return normalized

    def _load_records(self, source_path: str) -> List[Dict[str, Any]]:
        if os.path.isdir(source_path):
            records: List[Dict[str, Any]] = []
            for name in sorted(os.listdir(source_path)):
                if name.lower().startswith("cnki") or "知网" in name:
                    records.extend(self._load_records(os.path.join(source_path, name)))
            return records
        if source_path.lower().endswith(".json"):
            with open(source_path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            if isinstance(payload, dict):
                return list(payload.get("papers") or payload.get("records") or [])
            return list(payload or [])
        if source_path.lower().endswith(".csv"):
            with open(source_path, "r", encoding="utf-8-sig", newline="") as file:
                return list(csv.DictReader(file))
        return []

    def _map_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        mapped: Dict[str, Any] = dict(record)
        for source_key, target_key in self.FIELD_MAP.items():
            if source_key in record and target_key not in mapped:
                mapped[target_key] = record[source_key]
        return mapped
