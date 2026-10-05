# -*- coding: utf-8 -*-
"""Build a JSON knowledge graph from prepared academic metadata.

Input files must be legally obtained JSON or CSV exports placed under
``data/kg_sources``. The pipeline normalizes metadata, extracts keywords and
research directions, resolves simple aliases, builds graph triples, and can
optionally import the result into Neo4j.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.modules.knowledge_graph.ingestion.crawler_cnki import CNKIImportAdapter
from app.modules.knowledge_graph.ingestion.crawler_dblp import DBLPCrawler
from app.modules.knowledge_graph.ingestion.entity_resolution import EntityResolver
from app.modules.knowledge_graph.ingestion.extractor import MetadataExtractor
from app.modules.knowledge_graph.ingestion.importer import KnowledgeGraphImporter
from app.modules.knowledge_graph.ingestion.normalizer import MetadataNormalizer
from app.modules.knowledge_graph.ingestion.relation_builder import RelationBuilder


def load_records(source_dir: str) -> List[Dict[str, Any]]:
    cnki_records = CNKIImportAdapter().collect(source_dir)
    dblp_records = DBLPCrawler().collect(source_dir)
    if cnki_records or dblp_records:
        return [*cnki_records, *dblp_records]

    records: List[Dict[str, Any]] = []
    for filename in sorted(os.listdir(source_dir)):
        path = os.path.join(source_dir, filename)
        if filename.lower().endswith(".json"):
            with open(path, "r", encoding="utf-8") as file:
                payload = json.load(file)
            if isinstance(payload, dict):
                records.extend(payload.get("papers") or payload.get("records") or [])
            else:
                records.extend(payload or [])
        elif filename.lower().endswith(".csv"):
            with open(path, "r", encoding="utf-8-sig", newline="") as file:
                records.extend(csv.DictReader(file))
    return records


def build_graph(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    normalizer = MetadataNormalizer()
    extractor = MetadataExtractor()
    resolver = EntityResolver()
    relation_builder = RelationBuilder()
    normalized = normalizer.normalize(records)
    extracted = extractor.extract(normalized)
    resolved = resolver.resolve(extracted)
    return relation_builder.build(resolved)


def load_neo4j_config() -> Dict[str, Any]:
    config_path = os.path.join("config", "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join("config", "config.json.example")
    with open(config_path, "r", encoding="utf-8") as file:
        return (json.load(file) or {}).get("neo4j", {})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=os.path.join("data", "kg_sources"))
    parser.add_argument("--output", default=os.path.join("data", "knowledge_graph.json"))
    parser.add_argument("--import-neo4j", action="store_true", help="Import graph into configured Neo4j after building JSON")
    args = parser.parse_args()
    os.makedirs(args.source_dir, exist_ok=True)
    records = load_records(args.source_dir)
    graph = build_graph(records)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(graph, file, ensure_ascii=False, indent=2)
    print(f"Built graph with {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")
    if args.import_neo4j:
        result = KnowledgeGraphImporter(load_neo4j_config()).import_graph(graph)
        if not result.get("success"):
            raise SystemExit(f"Neo4j import failed: {result.get('error')}")
        print(f"Imported graph into Neo4j: {result['nodes']} nodes, {result['edges']} edges.")


if __name__ == "__main__":
    main()
