# -*- coding: utf-8 -*-
"""
Topic recommendation storage.

This module keeps the topic catalog and recommendation feedback in SQLite so the
web layer can support explainable recommendations and a lightweight feedback loop.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional


class TopicDatabase:
    """SQLite-backed store for topics and recommendation feedback."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            db_path = os.path.join(project_root, "data", "topic_recommendation.db")

        self.db_path = db_path
        self._init_database()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with self._connect() as conn:
            self._ensure_schema_compatibility(conn)
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_key TEXT UNIQUE,
                    title TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    subdomain TEXT,
                    keywords TEXT NOT NULL,
                    hotness REAL DEFAULT 0,
                    novelty REAL DEFAULT 0,
                    centrality REAL DEFAULT 0,
                    description TEXT,
                    related_resources TEXT DEFAULT '[]',
                    source TEXT DEFAULT 'seed',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recommendation_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    recommendation_id TEXT NOT NULL,
                    topic_key TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    note TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_topics_domain ON topics(domain);
                CREATE INDEX IF NOT EXISTS idx_topics_topic_key ON topics(topic_key);
                CREATE INDEX IF NOT EXISTS idx_feedback_topic_key
                    ON recommendation_feedback(topic_key);
                CREATE INDEX IF NOT EXISTS idx_feedback_session_id
                    ON recommendation_feedback(session_id);
                """
            )

    def _ensure_schema_compatibility(self, conn: sqlite3.Connection) -> None:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        if "topics" in tables:
            columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(topics)").fetchall()
            }
            required_columns = {
                "topic_key",
                "title",
                "domain",
                "keywords",
                "hotness",
                "novelty",
                "centrality",
            }
            if not required_columns.issubset(columns):
                conn.execute("DROP TABLE IF EXISTS topics")

        if "recommendation_feedback" in tables:
            columns = {
                row["name"]
                for row in conn.execute(
                    "PRAGMA table_info(recommendation_feedback)"
                ).fetchall()
            }
            required_columns = {
                "session_id",
                "recommendation_id",
                "topic_key",
                "feedback_type",
                "created_at",
            }
            if not required_columns.issubset(columns):
                conn.execute("DROP TABLE IF EXISTS recommendation_feedback")

    def add_topic(self, topic_data: Dict[str, Any]) -> int:
        now = datetime.utcnow().isoformat()
        payload = self._normalize_topic_payload(topic_data)

        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO topics (
                    topic_key, title, domain, subdomain, keywords, hotness, novelty,
                    centrality, description, related_resources, source, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["topic_key"],
                    payload["title"],
                    payload["domain"],
                    payload["subdomain"],
                    payload["keywords"],
                    payload["hotness"],
                    payload["novelty"],
                    payload["centrality"],
                    payload["description"],
                    json.dumps(payload["related_resources"], ensure_ascii=False),
                    payload["source"],
                    now,
                    now,
                ),
            )
            return int(cursor.lastrowid)

    def upsert_topic(self, topic_data: Dict[str, Any]) -> int:
        existing = self.get_topic_by_key(topic_data.get("topic_key") or topic_data.get("id"))
        if existing:
            self.update_topic(int(existing["id"]), topic_data)
            return int(existing["id"])
        return self.add_topic(topic_data)

    def bulk_upsert_topics(self, topics: Iterable[Dict[str, Any]]) -> int:
        count = 0
        for topic in topics:
            self.upsert_topic(topic)
            count += 1
        return count

    def update_topic(self, topic_id: int, topic_data: Dict[str, Any]) -> bool:
        current = self.get_topic(topic_id)
        if not current:
            return False

        payload = self._normalize_topic_payload({**current, **topic_data})
        payload["updated_at"] = datetime.utcnow().isoformat()

        with self._connect() as conn:
            result = conn.execute(
                """
                UPDATE topics
                SET topic_key = ?, title = ?, domain = ?, subdomain = ?, keywords = ?,
                    hotness = ?, novelty = ?, centrality = ?, description = ?,
                    related_resources = ?, source = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    payload["topic_key"],
                    payload["title"],
                    payload["domain"],
                    payload["subdomain"],
                    payload["keywords"],
                    payload["hotness"],
                    payload["novelty"],
                    payload["centrality"],
                    payload["description"],
                    json.dumps(payload["related_resources"], ensure_ascii=False),
                    payload["source"],
                    payload["updated_at"],
                    topic_id,
                ),
            )
            return result.rowcount > 0

    def delete_topic(self, topic_id: int) -> bool:
        with self._connect() as conn:
            result = conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
            return result.rowcount > 0

    def get_topic(self, topic_id: int) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM topics WHERE id = ?", (topic_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def get_topic_by_key(self, topic_key: Optional[str]) -> Optional[Dict[str, Any]]:
        if not topic_key:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM topics WHERE topic_key = ?",
                (str(topic_key),),
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def search_topics(
        self,
        domain: Optional[str] = None,
        keywords: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        order_by: str = "hotness",
        order_dir: str = "DESC",
    ) -> List[Dict[str, Any]]:
        allowed_order = {"hotness", "novelty", "centrality", "updated_at", "title"}
        order_by = order_by if order_by in allowed_order else "hotness"
        order_dir = "ASC" if str(order_dir).upper() == "ASC" else "DESC"

        sql = "SELECT * FROM topics"
        clauses: List[str] = []
        params: List[Any] = []

        if domain:
            clauses.append("domain = ?")
            params.append(domain)
        if keywords:
            clauses.append("keywords LIKE ?")
            params.append(f"%{keywords}%")

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        sql += f" ORDER BY {order_by} {order_dir} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def get_domains(self) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DISTINCT domain FROM topics ORDER BY domain"
            ).fetchall()
        return [row["domain"] for row in rows]

    def get_subdomains(self, domain: str) -> List[str]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT subdomain
                FROM topics
                WHERE domain = ? AND subdomain IS NOT NULL AND subdomain != ''
                ORDER BY subdomain
                """,
                (domain,),
            ).fetchall()
        return [row["subdomain"] for row in rows]

    def get_statistics(self) -> Dict[str, Any]:
        with self._connect() as conn:
            total_topics = conn.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
            domain_count = conn.execute(
                "SELECT COUNT(DISTINCT domain) FROM topics"
            ).fetchone()[0]
            averages = conn.execute(
                "SELECT AVG(hotness), AVG(novelty), AVG(centrality) FROM topics"
            ).fetchone()
            feedback_total = conn.execute(
                "SELECT COUNT(*) FROM recommendation_feedback"
            ).fetchone()[0]

        return {
            "total_topics": int(total_topics),
            "domain_count": int(domain_count),
            "avg_hotness": round(float(averages[0] or 0), 3),
            "avg_novelty": round(float(averages[1] or 0), 3),
            "avg_centrality": round(float(averages[2] or 0), 3),
            "feedback_total": int(feedback_total),
        }

    def save_feedback(
        self,
        session_id: str,
        recommendation_id: str,
        topic_key: str,
        feedback_type: str,
        note: str = "",
    ) -> int:
        if feedback_type not in {"like", "bookmark", "ignore"}:
            raise ValueError("Unsupported feedback type")

        created_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO recommendation_feedback (
                    session_id, recommendation_id, topic_key, feedback_type, note, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, recommendation_id, topic_key, feedback_type, note, created_at),
            )
            return int(cursor.lastrowid)

    def get_feedback_summary(self, topic_key: Optional[str] = None) -> Dict[str, Any]:
        sql = """
            SELECT topic_key, feedback_type, COUNT(*) AS cnt
            FROM recommendation_feedback
        """
        params: List[Any] = []
        if topic_key:
            sql += " WHERE topic_key = ?"
            params.append(topic_key)
        sql += " GROUP BY topic_key, feedback_type"

        summary: Dict[str, Dict[str, int]] = {}
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        for row in rows:
            topic_summary = summary.setdefault(
                row["topic_key"], {"like": 0, "bookmark": 0, "ignore": 0}
            )
            topic_summary[row["feedback_type"]] = int(row["cnt"])

        if topic_key:
            return summary.get(topic_key, {"like": 0, "bookmark": 0, "ignore": 0})
        return summary

    def optimize_database(self) -> None:
        with self._connect() as conn:
            conn.execute("VACUUM")

    def _normalize_topic_payload(self, topic_data: Dict[str, Any]) -> Dict[str, Any]:
        topic_key = str(
            topic_data.get("topic_key")
            or topic_data.get("id")
            or topic_data.get("title", "").strip().lower().replace(" ", "_")
        )
        related_resources = topic_data.get("related_resources") or []

        return {
            "topic_key": topic_key,
            "title": topic_data.get("title", topic_data.get("name", "")).strip(),
            "domain": topic_data.get("domain", "通用研究").strip(),
            "subdomain": (topic_data.get("subdomain") or "").strip(),
            "keywords": self._normalize_keywords(topic_data.get("keywords")),
            "hotness": float(topic_data.get("hotness", topic_data.get("hotness_score", 0.5))),
            "novelty": float(topic_data.get("novelty", topic_data.get("novelty_score", 0.5))),
            "centrality": float(
                topic_data.get("centrality", topic_data.get("centrality_score", 0.5))
            ),
            "description": (topic_data.get("description") or "").strip(),
            "related_resources": related_resources,
            "source": (topic_data.get("source") or "seed").strip(),
        }

    def _normalize_keywords(self, value: Any) -> str:
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            return ", ".join(items)
        return str(value or "").strip()

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        result = dict(row)
        try:
            result["related_resources"] = json.loads(result["related_resources"] or "[]")
        except json.JSONDecodeError:
            result["related_resources"] = []
        result["keywords_list"] = [
            part.strip() for part in result.get("keywords", "").split(",") if part.strip()
        ]
        return result
