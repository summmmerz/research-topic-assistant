# -*- coding: utf-8 -*-
"""
Stage-based recommendation workflow.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from .database import TopicDatabase
from .multi_feature_algorithm import MultiFeatureRecommender
from .redis_stage_store import RedisStageSessionStore
from app.modules.knowledge_graph.service import KnowledgeGraphService


class StageBasedRecommender:
    """Collect user preferences step by step and generate explainable topics."""

    SESSION_TTL_HOURS = 24

    FALLBACK_DOMAIN_DATA = {
        "计算机科学": {
            "base_directions": ["人工智能赋能教育", "金融科技风险分析", "医学智能诊疗支持"],
            "sub_directions": {
                "人工智能赋能教育": ["大语言模型", "学习行为分析", "推荐系统"],
                "金融科技风险分析": ["大语言模型", "自然语言处理", "时间序列分析"],
                "医学智能诊疗支持": ["医学影像", "自然语言处理", "计算机视觉"],
            },
        },
        "金融学": {
            "base_directions": ["金融科技风险分析", "数据驱动运营决策"],
            "sub_directions": {
                "金融科技风险分析": ["时间序列分析", "推荐系统", "自然语言处理"],
                "数据驱动运营决策": ["供应链优化", "时间序列分析", "推荐系统"],
            },
        },
        "教育学": {
            "base_directions": ["人工智能赋能教育"],
            "sub_directions": {
                "人工智能赋能教育": ["学习行为分析", "推荐系统", "大语言模型"],
            },
        },
    }

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Any = None,
        error_handler: Any = None,
        topic_db: Optional[TopicDatabase] = None,
    ):
        self.config = config or {}
        self.logger = logger
        self.error_handler = error_handler
        self.topic_db = topic_db or TopicDatabase()
        self.knowledge_graph_service = KnowledgeGraphService(
            neo4j_config=self.config.get("neo4j"),
            prefer_neo4j=self.config.get("prefer_neo4j", True),
        )
        self.multi_feature_recommender = MultiFeatureRecommender(
            config=config,
            logger=logger,
            error_handler=error_handler,
            topic_db=self.topic_db,
            knowledge_graph_service=self.knowledge_graph_service,
        )
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.redis_store = None
        self.session_storage = "memory"
        redis_config = self.config.get("redis") or {}
        if self.config.get("session_storage") == "redis" and redis_config:
            self.redis_store = RedisStageSessionStore(redis_config)
            if self.redis_store.available:
                self.session_storage = "redis"
        self.domain_data = self._load_domain_data_from_kg()

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = self._build_empty_session(session_id)
        self._persist_session(session_id)
        return session_id

    def get_current_stage(self, session_id: str) -> int:
        session = self._restore_session(session_id)
        return int(session.get("stage", 1)) if session else 1

    def get_stage_data(self, session_id: str, stage: int) -> Dict[str, Any]:
        session = self._get_or_create_session(session_id)
        user_info = session["user_info"]

        if stage == 1:
            return {
                "stage": 1,
                "title": "选择学科领域",
                "description": "先确定你希望进入的学科领域，系统会据此切换到对应的研究方向与主题。",
                "type": "multiple_choice",
                "options": list(self.domain_data.keys()),
                "required": True,
            }
        if stage == 2:
            domain = user_info.get("domain")
            if not domain:
                return self.get_stage_data(session_id, 1)
            return {
                "stage": 2,
                "title": "选择研究方向",
                "description": f"你已选择“{domain}”，请继续确定更聚焦的研究方向。",
                "type": "multiple_choice",
                "options": self.domain_data.get(domain, {}).get("base_directions", []),
                "required": True,
            }
        if stage == 3:
            domain = user_info.get("domain")
            base_direction = user_info.get("base_direction")
            if not domain or not base_direction:
                return self.get_stage_data(session_id, 2)
            return {
                "stage": 3,
                "title": "选择细分主题",
                "description": f"围绕“{base_direction}”选择你更想深入的具体主题。",
                "type": "multiple_choice",
                "options": self.domain_data.get(domain, {}).get("sub_directions", {}).get(base_direction, []),
                "required": True,
            }
        if stage == 4:
            return {
                "stage": 4,
                "title": "补充你的研究基础",
                "description": "填写你已有的技术栈、文献阅读积累、实验经验，或者明确你不想做的方向。",
                "type": "text_input",
                "required": False,
                "placeholder": "例如：熟悉 Python、Flask、机器学习；希望选题能做出系统原型并完成实验评估。",
            }
        if stage == 5:
            return {
                "stage": 5,
                "title": "补充导师或团队约束",
                "description": "如果有导师方向、实验室资源或论文要求，请在这里说明。",
                "type": "text_input",
                "required": False,
                "placeholder": "例如：导师关注知识图谱和推荐系统，希望题目兼顾可解释性与工程落地。",
            }
        return {
            "stage": 6,
            "title": "推荐完成",
            "description": "系统已生成人性化推荐结果。",
            "type": "completed",
        }

    def submit_stage(self, session_id: str, stage: int, data: Dict[str, Any]) -> Dict[str, Any]:
        session = self._restore_session(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}

        if stage in {1, 2, 3} and not data.get("selection"):
            return {"success": False, "error": "必须先选择一个选项"}

        session["history"].append(
            {
                "stage": stage,
                "data": data,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        user_info = session["user_info"]
        self._apply_stage_data(user_info, stage, data)

        session["stage"] = stage + 1
        session["last_activity"] = datetime.now(timezone.utc).isoformat()

        if stage == 5:
            recommendations = self.generate_recommendations(session_id)
            session["recommendations"] = recommendations
            self._persist_session(session_id)
            return {"success": True, "next_stage": 6, "recommendations": recommendations}

        self._persist_session(session_id)
        return {"success": True, "next_stage": stage + 1}

    def go_back(self, session_id: str) -> Dict[str, Any]:
        session = self._restore_session(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}

        current_stage = int(session.get("stage", 1))
        if current_stage <= 1:
            return {"success": False, "error": "已经是第一步"}

        session["stage"] = current_stage - 1
        if session["history"]:
            session["history"].pop()
        session["user_info"] = self._rebuild_user_info(session["history"])
        session["recommendations"] = []
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        self._persist_session(session_id)
        return {"success": True, "current_stage": session["stage"]}

    def generate_recommendations(self, session_id: str) -> List[Dict[str, Any]]:
        session = self._restore_session(session_id)
        if not session:
            return []

        user_info = session["user_info"]
        domain = user_info.get("domain", "")
        base_direction = user_info.get("base_direction", "")
        sub_direction = user_info.get("sub_direction", "")
        research_basis = user_info.get("research_basis", "")
        mentor_direction = user_info.get("mentor_direction", "")

        user_interest = "，".join(
            [part for part in [domain, base_direction, sub_direction, research_basis] if part]
        )
        mentor = None
        if mentor_direction.strip():
            mentor_digest = hashlib.sha1(mentor_direction.strip().encode("utf-8")).hexdigest()[:12]
            mentor = {
                "id": f"mentor-{mentor_digest}",
                "name": mentor_direction,
                "research": mentor_direction,
                "keywords": mentor_direction,
            }

        available_domains = set(self.topic_db.get_domains())
        domain_filter = domain if domain in available_domains else None

        recommended_topics = self.multi_feature_recommender.recommend_topics(
            user_interest=user_interest,
            mentor=mentor,
            limit=5,
            domain=domain_filter,
        )

        recommendations: List[Dict[str, Any]] = []
        for item in recommended_topics:
            recommendation_id = str(uuid.uuid4())
            explanation = item["explanation"]
            keywords = [kw.strip() for kw in str(item.get("keywords", "")).split(",") if kw.strip()]

            recommendations.append(
                {
                    "id": recommendation_id,
                    "topic_key": item["topic_key"],
                    "title": f"{item['topic_name']}的设计与实现",
                    "topic_name": item["topic_name"],
                    "domain": item.get("domain", ""),
                    "subdomain": item.get("subdomain", ""),
                    "background": item.get("description")
                    or f"该方向结合了“{base_direction} / {sub_direction}”的兴趣输入，适合作为论文型系统研究。",
                    "core_question": f"如何围绕“{item['topic_name']}”提出一个可验证、可实现、可评估的研究问题？",
                    "feasibility": self._build_feasibility_text(
                        item=item,
                        research_basis=research_basis,
                        mentor_direction=mentor_direction,
                    ),
                    "relevance": round(item["semantic_score"] * 100),
                    "hotness": round(item["hotness_score"] * 100),
                    "total_score": round(item["total_score"], 4),
                    "reason_tags": item["reason_tags"],
                    "explanation_summary": explanation["summary"],
                    "next_steps": explanation["next_steps"],
                    "keywords": keywords,
                    "features": {
                        "semantic_score": round(item["semantic_score"], 4),
                        "hotness_score": round(item["hotness_score"], 4),
                        "centrality_score": round(item["centrality_score"], 4),
                        "mentor_match_score": round(item["mentor_match_score"], 4),
                        "novelty_score": round(item["novelty_score"], 4),
                        "feedback_score": round(item["feedback_score"], 4),
                    },
                    "visuals": {
                        "table": {
                            "title": "推荐依据拆解",
                            "headers": ["指标", "得分"],
                            "rows": [
                                ["兴趣匹配", f"{item['semantic_score']:.2f}"],
                                ["研究热度", f"{item['hotness_score']:.2f}"],
                                ["图谱中心性", f"{item['centrality_score']:.2f}"],
                                ["导师契合度", f"{item['mentor_match_score']:.2f}"],
                                ["创新潜力", f"{item['novelty_score']:.2f}"],
                                ["历史反馈", f"{item['feedback_score']:.2f}"],
                            ],
                        }
                    },
                }
            )

        return recommendations

    def submit_feedback(
        self,
        session_id: str,
        recommendation_id: str,
        topic_key: str,
        feedback_type: str,
        note: str = "",
    ) -> Dict[str, Any]:
        self.topic_db.save_feedback(
            session_id=session_id,
            recommendation_id=recommendation_id,
            topic_key=topic_key,
            feedback_type=feedback_type,
            note=note,
        )
        return {
            "success": True,
            "message": "反馈已记录",
            "feedback_summary": self.topic_db.get_feedback_summary(topic_key),
        }

    def import_topics_from_file(self, file_path: str, source: str = "import") -> Dict[str, Any]:
        if not os.path.exists(file_path):
            return {"success": False, "error": "文件不存在"}

        with open(file_path, "r", encoding="utf-8") as file:
            payload = json.load(file)

        topics = payload.get("topics", []) if isinstance(payload, dict) else payload
        normalized = [{**topic, "source": topic.get("source", source)} for topic in topics]
        imported = self.topic_db.bulk_upsert_topics(normalized)
        return {"success": True, "imported": imported}

    def get_session_data(self, session_id: str) -> Dict[str, Any]:
        session = self._restore_session(session_id)
        if not session:
            return {"success": False, "error": "会话不存在"}
        return {
            "success": True,
            "session": session,
            "storage": self.session_storage,
            "redis": self.redis_store.status() if self.redis_store else None,
        }

    def cleanup_expired_sessions(self, max_age_hours: Optional[int] = None) -> int:
        threshold = timedelta(hours=max_age_hours or self.SESSION_TTL_HOURS)
        now = datetime.now(timezone.utc)
        expired_session_ids = []

        for session_id, session in self.sessions.items():
            last_activity = session.get("last_activity") or session.get("created_at")
            if not last_activity:
                continue
            if now - datetime.fromisoformat(last_activity) > threshold:
                expired_session_ids.append(session_id)

        for session_id in expired_session_ids:
            self.sessions.pop(session_id, None)

        return len(expired_session_ids)

    def save_session(self, session_id: str) -> bool:
        session = self._restore_session(session_id)
        if not session:
            return False

        save_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
            "topic_recommendation_sessions",
        )
        os.makedirs(os.path.abspath(save_dir), exist_ok=True)
        save_path = os.path.join(os.path.abspath(save_dir), f"{session_id}.json")

        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(session, file, ensure_ascii=False, indent=2)
        return True

    def load_session(self, session_id: str) -> bool:
        load_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
            "topic_recommendation_sessions",
            f"{session_id}.json",
        )
        load_path = os.path.abspath(load_path)
        if not os.path.exists(load_path):
            return False

        with open(load_path, "r", encoding="utf-8") as file:
            session = json.load(file)
        session.setdefault("last_activity", datetime.now(timezone.utc).isoformat())
        self.sessions[session_id] = session
        self._persist_session(session_id)
        return True

    def _build_feasibility_text(
        self,
        item: Dict[str, Any],
        research_basis: str,
        mentor_direction: str,
    ) -> str:
        parts = []
        if research_basis.strip():
            parts.append("你已经提供了一定研究基础，可以直接进入文献调研与原型验证阶段。")
        else:
            parts.append("该方向适合先从综述、公开数据集和小型原型切入，启动成本较低。")
        if mentor_direction.strip():
            parts.append("若能结合导师资源推进，选题的落地性会更强。")
        if item["novelty_score"] >= 0.8:
            parts.append("方向具备较好的新颖性，但需要尽早缩小范围，避免题目过大。")
        else:
            parts.append("方向相对稳健，适合作为毕业论文型项目。")
        return "".join(parts)

    def _build_empty_session(self, session_id: str) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "session_id": session_id,
            "created_at": now,
            "last_activity": now,
            "stage": 1,
            "user_info": {},
            "history": [],
            "recommendations": [],
        }

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        session = self._restore_session(session_id)
        if session is None:
            session = self._build_empty_session(session_id)
            self.sessions[session_id] = session
        session["last_activity"] = datetime.now(timezone.utc).isoformat()
        self._persist_session(session_id)
        return session

    def _restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self.sessions.get(session_id)
        if session:
            return session
        if self.session_storage == "redis" and self.redis_store:
            try:
                session = self.redis_store.load(session_id)
                if session:
                    self.sessions[session_id] = session
                    return session
            except Exception:
                self.session_storage = "memory"
        return None

    def _persist_session(self, session_id: str) -> None:
        if self.session_storage == "redis" and self.redis_store and session_id in self.sessions:
            try:
                self.redis_store.save(session_id, self.sessions[session_id])
            except Exception:
                self.session_storage = "memory"

    def _apply_stage_data(
        self,
        user_info: Dict[str, Any],
        stage: int,
        data: Dict[str, Any],
    ) -> None:
        if stage == 1:
            user_info["domain"] = data.get("selection")
            user_info.pop("base_direction", None)
            user_info.pop("sub_direction", None)
        elif stage == 2:
            user_info["base_direction"] = data.get("selection")
            user_info.pop("sub_direction", None)
        elif stage == 3:
            user_info["sub_direction"] = data.get("selection")
        elif stage == 4:
            user_info["research_basis"] = data.get("input", "")
        elif stage == 5:
            user_info["mentor_direction"] = data.get("input", "")

    def _rebuild_user_info(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        user_info: Dict[str, Any] = {}
        for record in history:
            self._apply_stage_data(user_info, int(record["stage"]), record["data"])
        return user_info

    def _load_domain_data_from_kg(self) -> Dict[str, Dict[str, Any]]:
        try:
            status = self.knowledge_graph_service.get_status()
            if status.get("total_nodes", 0) > 0:
                graph = self.knowledge_graph_service.get_visualization(max_nodes=120)
                nodes = graph.get("nodes", [])
                domains = [node for node in nodes if node.get("type") in {"领域", "ResearchDirection"}]
                candidates = [
                    node.get("label")
                    for node in nodes
                    if node.get("type") in {"研究方向", "关键词", "Keyword", "方法", "专业"}
                    and node.get("label")
                ]
                candidates = sorted(dict.fromkeys(candidates))
                if domains and candidates:
                    return {
                        domain["label"]: {
                            "base_directions": candidates[:8],
                            "sub_directions": {
                                direction: candidates[:8]
                                for direction in candidates[:8]
                            },
                        }
                        for domain in domains
                        if domain.get("label")
                    }
        except Exception:
            pass

        graph_paths = [
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "knowledge_graph.json")),
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "knowledge_graph.json")),
        ]

        payload = None
        for graph_path in graph_paths:
            if os.path.exists(graph_path):
                with open(graph_path, "r", encoding="utf-8") as file:
                    payload = json.load(file)
                break

        if not payload:
            return self.FALLBACK_DOMAIN_DATA

        nodes_by_id = {node["id"]: node for node in payload.get("nodes", [])}
        adjacency: Dict[str, List[str]] = defaultdict(list)
        for edge in payload.get("edges", []):
            source = edge.get("source")
            target = edge.get("target")
            if source in nodes_by_id and target in nodes_by_id:
                adjacency[source].append(target)
                adjacency[target].append(source)

        domain_data: Dict[str, Dict[str, Any]] = {}
        for node in payload.get("nodes", []):
            if node.get("type") != "领域":
                continue
            domain_id = node["id"]
            domain_label = node["label"]
            directions = []
            sub_directions: Dict[str, List[str]] = {}

            related_direction_ids = [
                neighbor_id
                for neighbor_id in adjacency.get(domain_id, [])
                if nodes_by_id[neighbor_id].get("type") == "研究方向"
            ]
            related_direction_ids.sort(key=lambda item: nodes_by_id[item]["label"])

            for direction_id in related_direction_ids:
                direction_label = nodes_by_id[direction_id]["label"]
                directions.append(direction_label)

                topic_candidates = []
                for second_neighbor_id in adjacency.get(direction_id, []):
                    second_neighbor = nodes_by_id[second_neighbor_id]
                    if second_neighbor.get("type") in {"关键词", "方法", "专业"}:
                        topic_candidates.append(second_neighbor["label"])

                deduped_topics = sorted({item for item in topic_candidates})
                if not deduped_topics:
                    deduped_topics = list(node.get("keywords", []))
                sub_directions[direction_label] = deduped_topics[:8]

            if not directions:
                directions = self.FALLBACK_DOMAIN_DATA.get(domain_label, {}).get("base_directions", [])
                sub_directions = self.FALLBACK_DOMAIN_DATA.get(domain_label, {}).get("sub_directions", {})

            domain_data[domain_label] = {
                "base_directions": directions,
                "sub_directions": sub_directions,
            }

        return domain_data or self.FALLBACK_DOMAIN_DATA
