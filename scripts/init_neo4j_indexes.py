# -*- coding: utf-8 -*-
"""Create Neo4j indexes required by the thesis knowledge graph schema."""

from __future__ import annotations

import json
import os

from app.modules.knowledge_graph.schema import INDEX_DEFINITIONS, NODE_LABELS
from app.utils.neo4j_client import Neo4jClient


def load_config() -> dict:
    config_path = os.path.join("config", "config.json")
    if not os.path.exists(config_path):
        config_path = os.path.join("config", "config.json.example")
    with open(config_path, "r", encoding="utf-8") as file:
        return (json.load(file) or {}).get("neo4j", {})


def main() -> None:
    client = Neo4jClient(load_config())
    if not client.available:
        raise SystemExit(f"Neo4j unavailable: {client.last_error}")
    for label in NODE_LABELS:
        client.run_write(
            f"CREATE CONSTRAINT {label.lower()}_id_unique IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
        )
    for label, prop in INDEX_DEFINITIONS:
        client.run_write(
            f"CREATE INDEX {label.lower()}_{prop}_idx IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
        )
    gds_status = "not_checked"
    try:
        client.run_write("CALL gds.version() YIELD version RETURN version")
        gds_status = "available"
    except Exception:
        gds_status = "unavailable"
    client.close()
    print(
        f"Created or verified {len(NODE_LABELS)} constraints and "
        f"{len(INDEX_DEFINITIONS)} Neo4j indexes. GDS: {gds_status}."
    )


if __name__ == "__main__":
    main()
