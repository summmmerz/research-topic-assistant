# -*- coding: utf-8 -*-
"""
Multi-feature topic recommender.

The implementation is intentionally lightweight and deterministic so it can run
without online model downloads while still exposing explainable scores.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional
import hashlib

from .database import TopicDatabase
from .feature_extractor import RecommendationFeatureExtractor


class MultiFeatureRecommender:
    """Score topics with semantic, trend, centrality, mentor, diversity and feedback signals."""

    DEFAULT_WEIGHTS = {
        "semantic": 0.35,
        "hotness": 0.18,
        "centrality": 0.17,
        "mentor_match": 0.15,
        "novelty": 0.08,
        "feedback": 0.07,
    }

    DEFAULT_TOPICS = [
        {
            "topic_key": "llm_research_assistant",
            "title": "大语言模型驱动的科研助手",
            "domain": "计算机科学",
            "subdomain": "人工智能",
            "keywords": ["大语言模型", "科研辅助", "提示工程", "多轮对话"],
            "hotness": 0.95,
            "novelty": 0.82,
            "centrality": 0.88,
            "description": "面向科研选题、文献综述和研究规划的智能助手设计。",
        },
        {
            "topic_key": "knowledge_graph_recommendation",
            "title": "知识图谱增强的选题推荐",
            "domain": "计算机科学",
            "subdomain": "知识工程",
            "keywords": ["知识图谱", "推荐系统", "可解释性", "科研选题"],
            "hotness": 0.86,
            "novelty": 0.78,
            "centrality": 0.91,
            "description": "利用结构化学术知识网络提升推荐准确性和可解释性。",
        },
        {
            "topic_key": "trend_prediction_transformer",
            "title": "基于 Transformer 的研究趋势预测",
            "domain": "计算机科学",
            "subdomain": "数据挖掘",
            "keywords": ["Transformer", "时间序列", "趋势预测", "学术热点"],
            "hotness": 0.83,
            "novelty": 0.84,
            "centrality": 0.74,
            "description": "预测新兴研究主题的演化轨迹与热点迁移。",
        },
        {
            "topic_key": "cross_domain_fintech_ai",
            "title": "金融科技中的可解释人工智能",
            "domain": "金融学",
            "subdomain": "金融科技",
            "keywords": ["金融科技", "可解释AI", "风险控制", "模型治理"],
            "hotness": 0.79,
            "novelty": 0.76,
            "centrality": 0.73,
            "description": "结合金融场景约束构建更可信的智能分析模型。",
        },
        {
            "topic_key": "multimodal_literature_analysis",
            "title": "多模态学术文献分析",
            "domain": "计算机科学",
            "subdomain": "自然语言处理",
            "keywords": ["多模态", "文献分析", "图表理解", "学术检索"],
            "hotness": 0.8,
            "novelty": 0.87,
            "centrality": 0.69,
            "description": "融合文本、图表和元数据提升文献理解能力。",
        },
        {
            "topic_key": "privacy_local_model",
            "title": "面向隐私保护的本地科研模型部署",
            "domain": "计算机科学",
            "subdomain": "系统安全",
            "keywords": ["隐私保护", "本地部署", "开源模型", "科研系统"],
            "hotness": 0.72,
            "novelty": 0.81,
            "centrality": 0.67,
            "description": "减少对外部云端 API 的依赖，提升数据安全性与可控性。",
        },
    ]

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        logger: Any = None,
        error_handler: Any = None,
        topic_db: Optional[TopicDatabase] = None,
        knowledge_graph_service: Any = None,
    ):
        self.config = config or {}
        self.logger = logger
        self.error_handler = error_handler
        self.topic_db = topic_db or TopicDatabase()
        self.feature_extractor = RecommendationFeatureExtractor(knowledge_graph_service)
        self.weights = dict(self.DEFAULT_WEIGHTS)
        self.weights.update(self.config.get("weights", {}))
        self._normalize_weights()
        self.feature_cache: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._ensure_seed_topics()

    def _ensure_seed_topics(self) -> None:
        if self.topic_db.get_statistics()["total_topics"] > 0:
            return
        self.topic_db.bulk_upsert_topics(self.DEFAULT_TOPICS)

    def _normalize_weights(self) -> None:
        total = sum(self.weights.values()) or 1.0
        for key in list(self.weights.keys()):
            self.weights[key] = self.weights[key] / total

    def set_weights(self, weights: Dict[str, float]) -> None:
        self.weights.update(weights)
        self._normalize_weights()

    def get_weights(self) -> Dict[str, float]:
        return dict(self.weights)

    def calculate_semantic_similarity(self, topic: Dict[str, Any], user_interest: str) -> float:
        cache_key = f"{topic['topic_key']}::{user_interest}"
        if cache_key in self.feature_cache["semantic"]:
            return self.feature_cache["semantic"][cache_key]

        score = self.feature_extractor.semantic_score(topic, user_interest)

        self.feature_cache["semantic"][cache_key] = score
        return score

    def calculate_hotness(self, topic: Dict[str, Any]) -> float:
        return self._clamp(self.feature_extractor.hotness_score(topic))

    def calculate_centrality(self, topic: Dict[str, Any], method: str = "degree") -> float:
        return self._clamp(self.feature_extractor.centrality_score(topic))

    def calculate_novelty(self, topic: Dict[str, Any], user_interest: str) -> float:
        topic_tokens = self._tokenize(topic.get("keywords", ""))
        interest_tokens = self._tokenize(user_interest)
        overlap = len(topic_tokens & interest_tokens)
        base = float(topic.get("novelty", 0.0))
        if not topic_tokens:
            return self._clamp(base)
        overlap_ratio = overlap / len(topic_tokens)
        return self._clamp(base * (1 - 0.35 * overlap_ratio))

    def calculate_mentor_match(
        self, topic: Dict[str, Any], mentor: Optional[Dict[str, Any]] = None
    ) -> float:
        if not mentor:
            return 0.0
        mentor_text = self.feature_extractor.mentor_text(mentor)
        mentor_tokens = self._tokenize(mentor_text)
        topic_tokens = self._tokenize(topic.get("keywords", "") + " " + topic.get("title", ""))
        if not mentor_tokens or not topic_tokens:
            return 0.0
        return len(mentor_tokens & topic_tokens) / len(mentor_tokens | topic_tokens)

    def calculate_feedback_score(self, topic_key: str) -> float:
        summary = self.topic_db.get_feedback_summary(topic_key)
        like_count = summary.get("like", 0)
        bookmark_count = summary.get("bookmark", 0)
        ignore_count = summary.get("ignore", 0)
        raw = 0.12 * like_count + 0.18 * bookmark_count - 0.1 * ignore_count
        return self._clamp(0.5 + raw, lower=0.0, upper=1.0)

    def calculate_score(
        self,
        topic: Dict[str, Any],
        user_interest: str,
        mentor: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        semantic_score = self.calculate_semantic_similarity(topic, user_interest)
        hotness_score = self.calculate_hotness(topic)
        centrality_score = self.calculate_centrality(topic)
        mentor_match_score = self.calculate_mentor_match(topic, mentor)
        novelty_score = self.calculate_novelty(topic, user_interest)
        feedback_score = self.calculate_feedback_score(topic["topic_key"])

        total_score = (
            self.weights["semantic"] * semantic_score
            + self.weights["hotness"] * hotness_score
            + self.weights["centrality"] * centrality_score
            + self.weights["mentor_match"] * mentor_match_score
            + self.weights["novelty"] * novelty_score
            + self.weights["feedback"] * feedback_score
        )

        explanation = self._build_explanation(
            topic,
            semantic_score,
            hotness_score,
            centrality_score,
            mentor_match_score,
            novelty_score,
            feedback_score,
        )

        return {
            "topic_id": topic.get("id", topic["topic_key"]),
            "topic_key": topic["topic_key"],
            "topic_name": topic["title"],
            "domain": topic.get("domain", ""),
            "subdomain": topic.get("subdomain", ""),
            "semantic_score": semantic_score,
            "hotness_score": hotness_score,
            "centrality_score": centrality_score,
            "mentor_match_score": mentor_match_score,
            "novelty_score": novelty_score,
            "feedback_score": feedback_score,
            "total_score": total_score,
            "description": topic.get("description", ""),
            "keywords": topic.get("keywords", ""),
            "explanation": explanation,
            "reason_tags": explanation["reason_tags"],
        }

    def recommend_topics(
        self,
        user_interest: str,
        mentor: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        topics = self.topic_db.search_topics(domain=domain, limit=100, offset=0, order_by="hotness")
        topics = self._merge_graph_candidates(topics, user_interest=user_interest, domain=domain)
        scored_topics = [
            self.calculate_score(topic, user_interest=user_interest, mentor=mentor)
            for topic in topics
        ]
        scored_topics.sort(key=lambda item: item["total_score"], reverse=True)
        return scored_topics[:limit]

    def _merge_graph_candidates(
        self,
        topics: List[Dict[str, Any]],
        user_interest: str,
        domain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        graph_service = self.feature_extractor.graph.knowledge_graph_service
        if not graph_service:
            return topics
        merged = {topic["topic_key"]: topic for topic in topics if topic.get("topic_key")}
        for query in [user_interest, domain or ""]:
            if not query:
                continue
            try:
                hits = graph_service.search_entities(query=query, limit=30)
            except Exception:
                hits = []
            for hit in hits:
                try:
                    detail = graph_service.get_entity(hit["id"]) or {}
                except Exception:
                    detail = {}
                candidate = self._graph_hit_to_topic(hit, detail, domain)
                merged.setdefault(candidate["topic_key"], candidate)
        return list(merged.values())

    def _graph_hit_to_topic(
        self,
        hit: Dict[str, Any],
        detail: Dict[str, Any],
        domain: Optional[str],
    ) -> Dict[str, Any]:
        label = hit.get("label") or detail.get("label") or hit.get("id")
        keywords = detail.get("keywords") or []
        related_labels = [
            node.get("label", "")
            for node in detail.get("related_nodes", [])[:8]
            if node.get("label")
        ]
        all_keywords = list(dict.fromkeys([*keywords, *related_labels, str(label)]))
        degree = float(hit.get("degree") or detail.get("degree") or len(detail.get("related_edges", [])) or 0)
        digest = hashlib.sha1(str(hit.get("id") or label).encode("utf-8")).hexdigest()[:12]
        return {
            "topic_key": f"kg_{digest}",
            "title": str(label),
            "domain": domain or self._infer_domain(detail, all_keywords),
            "subdomain": hit.get("type") or detail.get("type") or "知识图谱候选",
            "keywords": ",".join(str(item) for item in all_keywords if item),
            "hotness": 0.62,
            "novelty": 0.76,
            "centrality": max(min(degree / 10.0, 1.0), 0.55),
            "description": detail.get("summary") or f"该候选主题来自知识图谱实体“{label}”及其邻接关系。",
            "source": "knowledge_graph",
        }

    def _infer_domain(self, detail: Dict[str, Any], keywords: List[str]) -> str:
        text = " ".join([str(detail.get("label", "")), " ".join(keywords)])
        if any(word in text for word in ["金融", "风控", "量化"]):
            return "金融学"
        if any(word in text for word in ["教育", "学习", "教学"]):
            return "教育学"
        return "计算机科学"

    def batch_recommend(
        self,
        user_interest: str,
        mentors: Optional[List[Dict[str, Any]]] = None,
        limit: int = 10,
        domain: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        if not mentors:
            return {"default": self.recommend_topics(user_interest, None, limit, domain)}

        return {
            mentor.get("id", "unknown"): self.recommend_topics(
                user_interest=user_interest,
                mentor=mentor,
                limit=limit,
                domain=domain,
            )
            for mentor in mentors
        }

    def clear_cache(self) -> None:
        self.feature_cache = defaultdict(dict)

    def get_feature_importance(
        self,
        topics: List[Dict[str, Any]],
        user_interest: str,
        mentor: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        if not topics:
            return {key: 0.0 for key in self.weights.keys()}

        aggregate = defaultdict(float)
        for topic in topics:
            scored = self.calculate_score(topic, user_interest, mentor)
            aggregate["semantic"] += scored["semantic_score"]
            aggregate["hotness"] += scored["hotness_score"]
            aggregate["centrality"] += scored["centrality_score"]
            aggregate["mentor_match"] += scored["mentor_match_score"]
            aggregate["novelty"] += scored["novelty_score"]
            aggregate["feedback"] += scored["feedback_score"]

        return {key: value / len(topics) for key, value in aggregate.items()}

    def _build_explanation(
        self,
        topic: Dict[str, Any],
        semantic_score: float,
        hotness_score: float,
        centrality_score: float,
        mentor_match_score: float,
        novelty_score: float,
        feedback_score: float,
    ) -> Dict[str, Any]:
        reason_tags: List[str] = []
        reasons: List[str] = []

        if semantic_score >= 0.25:
            reason_tags.append("兴趣匹配")
            reasons.append("与当前研究兴趣描述高度相关")
        if hotness_score >= 0.8:
            reason_tags.append("热点趋势")
            reasons.append("近期热度较高，适合切入前沿方向")
        if centrality_score >= 0.8:
            reason_tags.append("图谱枢纽")
            reasons.append("在知识图谱中位于核心位置，延展文献更丰富")
        if mentor_match_score >= 0.15:
            reason_tags.append("导师契合")
            reasons.append("与导师方向或团队资源更匹配")
        if novelty_score >= 0.75:
            reason_tags.append("跨界创新")
            reasons.append("保留了较强的新颖性，适合作为创新点突破")
        if feedback_score > 0.55:
            reason_tags.append("用户认可")
            reasons.append("历史反馈表现更好，说明接受度较高")

        if not reasons:
            reasons.append("综合表现均衡，适合作为稳妥的起步选题")

        next_steps = [
            f"先围绕“{topic['title']}”整理近三年的核心论文与综述。",
            "进一步缩小到可实验、可验证的子问题。",
            "尽快确认可用数据、评价指标和导师资源。",
        ]

        return {
            "reason_tags": reason_tags,
            "summary": "；".join(reasons),
            "next_steps": next_steps,
        }

    def _tokenize(self, text: str) -> set[str]:
        cleaned = str(text or "").lower()
        separators = [",", "，", "。", "；", ";", "：", ":", "/", "\\", "(", ")", "-", "_", "\n", "\t"]
        for separator in separators:
            cleaned = cleaned.replace(separator, " ")
        return {token.strip() for token in cleaned.split(" ") if token.strip()}

    def _clamp(self, value: float, lower: float = 0.0, upper: float = 1.0) -> float:
        return max(lower, min(upper, value))
