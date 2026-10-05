# -*- coding: utf-8 -*-
"""Import local JSON knowledge graph data into Neo4j."""

from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

from app.modules.knowledge_graph.ingestion.importer import KnowledgeGraphImporter


def load_config() -> dict:
    config_path = os.path.join("config", "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join("config", "config.json.example")
    with open(config_path, "r", encoding="utf-8") as file:
        return (json.load(file) or {}).get("neo4j", {})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=os.path.join("data", "knowledge_graph.json"))
    args = parser.parse_args()

    with open(args.source, "r", encoding="utf-8") as file:
        graph = json.load(file)

    result = KnowledgeGraphImporter(load_config()).import_graph(graph)
    if not result.get("success"):
        raise SystemExit(f"Neo4j unavailable: {result.get('error')}")
    print(f"Imported {result['nodes']} nodes and {result['edges']} edges.")


if __name__ == "__main__":
    main()
