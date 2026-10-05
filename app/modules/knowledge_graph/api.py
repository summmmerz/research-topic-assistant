# -*- coding: utf-8 -*-
"""
Knowledge graph API.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request

from .service import KnowledgeGraphService


kg_bp = Blueprint("knowledge_graph", __name__, url_prefix="/api/kg")
kg_service = KnowledgeGraphService()


def _parse_entity_types(raw_value: str | None):
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


@kg_bp.route("/status", methods=["GET"])
def get_status():
    return jsonify({"success": True, "status": kg_service.get_status()})


@kg_bp.route("/visualization", methods=["GET"])
def get_visualization():
    entity_types = _parse_entity_types(request.args.get("entity_types"))
    query = request.args.get("query", "")
    max_nodes = request.args.get("max_nodes", default=40, type=int)
    focus_id = request.args.get("focus_id")

    payload = kg_service.get_visualization(
        entity_types=entity_types,
        max_nodes=max_nodes,
        query=query,
        focus_id=focus_id,
    )
    return jsonify({"success": True, **payload})


@kg_bp.route("/search", methods=["GET", "POST"])
def search_entities():
    if request.method == "POST":
        data = request.get_json() or {}
        query = data.get("query", "")
        entity_types = data.get("entity_types") or []
        limit = int(data.get("limit", 12))
    else:
        query = request.args.get("query", "")
        entity_types = _parse_entity_types(request.args.get("entity_types"))
        limit = request.args.get("limit", default=12, type=int)

    return jsonify(
        {
            "success": True,
            "results": kg_service.search_entities(
                query=query,
                entity_types=entity_types,
                limit=limit,
            ),
        }
    )


@kg_bp.route("/entity/<entity_id>", methods=["GET"])
def get_entity(entity_id: str):
    payload = kg_service.get_entity(entity_id)
    if not payload:
        return jsonify({"success": False, "error": "实体不存在"}), 404
    return jsonify({"success": True, "entity": payload})
