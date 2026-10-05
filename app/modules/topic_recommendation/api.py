# -*- coding: utf-8 -*-
"""
Topic recommendation API.
"""

from __future__ import annotations

import os
import json

from flask import Blueprint, jsonify, request

from .database import TopicDatabase
from .stage_based import StageBasedRecommender


topic_bp = Blueprint("topic", __name__, url_prefix="/api/topic")
topic_db = TopicDatabase()


def _load_recommender_config() -> dict:
    config_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "config", "config.json")
    )
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as file:
        config = json.load(file) or {}
    redis_config = config.get("redis") or {}
    return {
        **config.get("topic_recommendation", {}),
        "redis": redis_config,
        "neo4j": config.get("neo4j", {}),
        "session_storage": config.get("topic_recommendation", {}).get("session_storage", "redis"),
    }


stage_recommender = StageBasedRecommender(config=_load_recommender_config(), topic_db=topic_db)


@topic_bp.route("/add", methods=["POST"])
def add_topic():
    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"success": False, "error": "title is required"}), 400
    if not data.get("domain"):
        return jsonify({"success": False, "error": "domain is required"}), 400
    if not data.get("keywords"):
        return jsonify({"success": False, "error": "keywords is required"}), 400

    topic_id = topic_db.add_topic(data)
    return jsonify({"success": True, "topic_id": topic_id}), 201


@topic_bp.route("/update/<int:topic_id>", methods=["PUT"])
def update_topic(topic_id: int):
    data = request.get_json() or {}
    success = topic_db.update_topic(topic_id, data)
    if not success:
        return jsonify({"success": False, "error": "topic not found"}), 404
    return jsonify({"success": True})


@topic_bp.route("/delete/<int:topic_id>", methods=["DELETE"])
def delete_topic(topic_id: int):
    success = topic_db.delete_topic(topic_id)
    if not success:
        return jsonify({"success": False, "error": "topic not found"}), 404
    return jsonify({"success": True})


@topic_bp.route("/get/<int:topic_id>", methods=["GET"])
def get_topic(topic_id: int):
    topic = topic_db.get_topic(topic_id)
    if not topic:
        return jsonify({"success": False, "error": "topic not found"}), 404
    return jsonify({"success": True, "topic": topic})


@topic_bp.route("/search", methods=["GET"])
def search_topics():
    topics = topic_db.search_topics(
        domain=request.args.get("domain"),
        keywords=request.args.get("keywords"),
        limit=request.args.get("limit", default=10, type=int),
        offset=request.args.get("offset", default=0, type=int),
        order_by=request.args.get("order_by", default="hotness"),
        order_dir=request.args.get("order_dir", default="DESC"),
    )
    return jsonify({"success": True, "topics": topics, "statistics": topic_db.get_statistics()})


@topic_bp.route("/domains", methods=["GET"])
def get_domains():
    return jsonify({"success": True, "domains": topic_db.get_domains()})


@topic_bp.route("/subdomains/<domain>", methods=["GET"])
def get_subdomains(domain: str):
    return jsonify({"success": True, "subdomains": topic_db.get_subdomains(domain)})


@topic_bp.route("/statistics", methods=["GET"])
def get_statistics():
    return jsonify({"success": True, "statistics": topic_db.get_statistics()})


@topic_bp.route("/feedback/summary", methods=["GET"])
def get_feedback_summary():
    topic_key = request.args.get("topic_key")
    return jsonify(
        {"success": True, "summary": topic_db.get_feedback_summary(topic_key=topic_key)}
    )


@topic_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    data = request.get_json() or {}
    required = ["session_id", "recommendation_id", "topic_key", "feedback_type"]
    missing = [key for key in required if not data.get(key)]
    if missing:
        return jsonify({"success": False, "error": f"missing fields: {', '.join(missing)}"}), 400

    try:
        result = stage_recommender.submit_feedback(
            session_id=data["session_id"],
            recommendation_id=data["recommendation_id"],
            topic_key=data["topic_key"],
            feedback_type=data["feedback_type"],
            note=data.get("note", ""),
        )
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    return jsonify(result)


@topic_bp.route("/import", methods=["POST"])
def import_topics():
    data = request.get_json() or {}
    file_path = data.get("file_path")
    if not file_path:
        return jsonify({"success": False, "error": "file_path is required"}), 400

    allowed_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data")
    )
    absolute_path = os.path.abspath(file_path)
    if not absolute_path.startswith(allowed_root):
        return jsonify({"success": False, "error": "file_path must stay inside project/data"}), 400

    result = stage_recommender.import_topics_from_file(
        file_path=absolute_path,
        source=data.get("source", "manual_import"),
    )
    return jsonify(result), (200 if result.get("success") else 400)


@topic_bp.route("/optimize", methods=["POST"])
def optimize_database():
    topic_db.optimize_database()
    return jsonify({"success": True})


@topic_bp.route("/stage/create", methods=["POST"])
def create_stage_session():
    session_id = stage_recommender.create_session()
    return jsonify(
        {
            "success": True,
            "session_id": session_id,
            "stage_data": stage_recommender.get_stage_data(session_id, 1),
        }
    ), 201


@topic_bp.route("/stage/current/<session_id>", methods=["GET"])
def get_current_stage(session_id: str):
    return jsonify(
        {"success": True, "stage": stage_recommender.get_current_stage(session_id)}
    )


@topic_bp.route("/stage/data/<session_id>/<int:stage>", methods=["GET"])
def get_stage_data(session_id: str, stage: int):
    return jsonify(
        {"success": True, "stage_data": stage_recommender.get_stage_data(session_id, stage)}
    )


@topic_bp.route("/stage/submit/<session_id>/<int:stage>", methods=["POST"])
def submit_stage_data(session_id: str, stage: int):
    result = stage_recommender.submit_stage(session_id, stage, request.get_json() or {})
    return jsonify(result), (200 if result.get("success") else 400)


@topic_bp.route("/stage/back/<session_id>", methods=["POST"])
def go_back_stage(session_id: str):
    result = stage_recommender.go_back(session_id)
    return jsonify(result), (200 if result.get("success") else 400)


@topic_bp.route("/stage/session/<session_id>", methods=["GET"])
def get_session_data(session_id: str):
    result = stage_recommender.get_session_data(session_id)
    return jsonify(result), (200 if result.get("success") else 404)


@topic_bp.route("/stage/save/<session_id>", methods=["POST"])
def save_session(session_id: str):
    success = stage_recommender.save_session(session_id)
    return jsonify({"success": success}), (200 if success else 400)


@topic_bp.route("/stage/load/<session_id>", methods=["POST"])
def load_session(session_id: str):
    success = stage_recommender.load_session(session_id)
    return jsonify({"success": success}), (200 if success else 404)
