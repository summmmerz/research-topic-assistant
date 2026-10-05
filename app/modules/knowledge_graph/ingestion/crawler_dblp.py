# -*- coding: utf-8 -*-
"""DBLP metadata ingestion adapter.

Supports prepared DBLP JSON/CSV exports. XML-scale DBLP dumps can be converted
outside this adapter into the same fields to keep the thesis demo deterministic.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List


class DBLPCrawler:
    def collect(self, source_path: str) -> List[Dict[str, Any]]:
        records = self._load_records(source_path)
        normalized = []
        for record in records:
            item = dict(record)
            item["source"] = item.get("source") or "dblp_export"
            item["venue"] = item.get("venue") or item.get("booktitle") or item.get("journal")
            item["doi"] = item.get("doi") or item.get("key") or item.get("url")
            if item.get("title"):
                normalized.append(item)
        return normalized

    def _load_records(self, source_path: str) -> List[Dict[str, Any]]:
        if os.path.isdir(source_path):
            records: List[Dict[str, Any]] = []
            for name in sorted(os.listdir(source_path)):
                if name.lower().startswith("dblp"):
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
