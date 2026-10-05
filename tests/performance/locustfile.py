# -*- coding: utf-8 -*-
"""Locust load-test scenarios for the research topic assistant.

The workload mirrors the main flows used in the thesis demo:
home page access, system monitoring, knowledge-graph browsing, staged topic
recommendation, session management, and a small share of chat requests.
"""

from __future__ import annotations

import random
import uuid

from locust import HttpUser, between, task


KG_QUERIES = [
    "知识图谱",
    "推荐系统",
    "机器学习",
    "自然语言处理",
    "科研选题",
]

CHAT_PROMPTS = [
    "请简要说明知识图谱在科研选题推荐中的作用。",
    "如何评价一个毕业论文选题的可行性？",
    "推荐系统可以从哪些维度解释推荐结果？",
]


class ResearchAssistantUser(HttpUser):
    """Simulate a thesis-demo user using the Web system."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.session_id = f"locust-{uuid.uuid4().hex[:12]}"
        self.topic_stage_session_id = None
        self.topic_recommendation = None

        with self.client.post(
            "/api/session/new",
            name="/api/session/new",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"unexpected status {response.status_code}")
                return
            payload = response.json()
            if not payload.get("success") or not payload.get("session_id"):
                response.failure("missing session_id")
                return
            self.session_id = payload["session_id"]

    @task(3)
    def browse_pages(self) -> None:
        """Measure static page rendering for the three main UI entries."""
        path = random.choice(["/", "/topic-recommendation", "/knowledge-graph"])
        with self.client.get(path, name=path, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"unexpected status {response.status_code}")

    @task(5)
    def system_status_and_stats(self) -> None:
        """Measure lightweight monitoring endpoints."""
        path = random.choice(["/api/status", "/api/stats"])
        with self.client.get(path, name=path, catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"unexpected status {response.status_code}")
                return
            payload = response.json()
            if not payload.get("success"):
                response.failure("success flag is false")

    @task(6)
    def knowledge_graph_query(self) -> None:
        """Measure knowledge-graph status, search, and visualization APIs."""
        query = random.choice(KG_QUERIES)
        action = random.choice(["status", "search", "visualization"])

        if action == "status":
            with self.client.get(
                "/api/kg/status",
                name="/api/kg/status",
                catch_response=True,
            ) as response:
                self._expect_success(response)
            return

        if action == "search":
            with self.client.get(
                "/api/kg/search",
                params={"query": query, "limit": 10},
                name="/api/kg/search",
                catch_response=True,
            ) as response:
                if self._expect_success(response):
                    payload = response.json()
                    if "results" not in payload:
                        response.failure("missing results")
            return

        with self.client.get(
            "/api/kg/visualization",
            params={"query": query, "max_nodes": 40},
            name="/api/kg/visualization",
            catch_response=True,
        ) as response:
            if self._expect_success(response):
                payload = response.json()
                if "nodes" not in payload or "edges" not in payload:
                    response.failure("missing graph payload")

    @task(5)
    def topic_recommendation_catalog(self) -> None:
        """Measure topic catalog and statistics endpoints."""
        action = random.choice(["domains", "statistics", "search", "feedback_summary"])

        if action == "domains":
            with self.client.get(
                "/api/topic/domains",
                name="/api/topic/domains",
                catch_response=True,
            ) as response:
                self._expect_success(response)
            return

        if action == "statistics":
            with self.client.get(
                "/api/topic/statistics",
                name="/api/topic/statistics",
                catch_response=True,
            ) as response:
                self._expect_success(response)
            return

        if action == "feedback_summary":
            with self.client.get(
                "/api/topic/feedback/summary",
                name="/api/topic/feedback/summary",
                catch_response=True,
            ) as response:
                self._expect_success(response)
            return

        with self.client.get(
            "/api/topic/search",
            params={"keywords": random.choice(KG_QUERIES), "limit": 10},
            name="/api/topic/search",
            catch_response=True,
        ) as response:
            if self._expect_success(response):
                payload = response.json()
                if "topics" not in payload:
                    response.failure("missing topics")

    @task(2)
    def staged_recommendation_flow(self) -> None:
        """Run a full staged recommendation workflow."""
        with self.client.post(
            "/api/topic/stage/create",
            name="/api/topic/stage/create",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"unexpected status {response.status_code}")
                return
            payload = response.json()
            if not payload.get("success") or not payload.get("session_id"):
                response.failure("missing stage session_id")
                return

            stage_session_id = payload["session_id"]
            stage_data = payload.get("stage_data") or {}
            domain_options = stage_data.get("options") or ["计算机科学"]
            domain = random.choice(domain_options)

        self.topic_stage_session_id = stage_session_id
        flow_payloads = [
            {"selection": domain},
            {"selection": "推荐系统"},
            {"selection": "知识图谱"},
            {"input": "熟悉 Python、Flask、知识图谱和推荐算法，希望完成可运行系统原型。"},
            {"input": "导师关注可解释推荐、科研数据建模和系统性能评估。"},
        ]

        for stage, data in enumerate(flow_payloads, start=1):
            with self.client.post(
                f"/api/topic/stage/submit/{stage_session_id}/{stage}",
                json=data,
                name="/api/topic/stage/submit",
                catch_response=True,
            ) as response:
                if not self._expect_success(response):
                    return
                if stage == 5:
                    payload = response.json()
                    recommendations = payload.get("recommendations") or []
                    if recommendations:
                        self.topic_recommendation = recommendations[0]

        with self.client.get(
            f"/api/topic/stage/session/{stage_session_id}",
            name="/api/topic/stage/session",
            catch_response=True,
        ) as response:
            self._expect_success(response)

    @task(1)
    def submit_recommendation_feedback(self) -> None:
        """Measure feedback persistence after a recommendation is generated."""
        if not self.topic_stage_session_id or not self.topic_recommendation:
            self.staged_recommendation_flow()
            return

        payload = {
            "session_id": self.topic_stage_session_id,
            "recommendation_id": self.topic_recommendation["id"],
            "topic_key": self.topic_recommendation["topic_key"],
            "feedback_type": random.choice(["like", "bookmark", "ignore"]),
            "note": "locust performance test",
        }
        with self.client.post(
            "/api/topic/feedback",
            json=payload,
            name="/api/topic/feedback",
            catch_response=True,
        ) as response:
            self._expect_success(response)

    @task(2)
    def session_history_and_settings(self) -> None:
        """Measure user-session utilities used by the Web client."""
        action = random.choice(["history", "settings_get", "settings_post"])

        if action == "history":
            with self.client.get(
                "/api/history",
                params={"session_id": self.session_id, "limit": 20},
                name="/api/history",
                catch_response=True,
            ) as response:
                self._expect_success(response)
            return

        if action == "settings_get":
            with self.client.get(
                "/api/settings",
                params={"session_id": self.session_id},
                name="/api/settings",
                catch_response=True,
            ) as response:
                self._expect_success(response)
            return

        with self.client.post(
            "/api/settings",
            json={
                "session_id": self.session_id,
                "settings": {
                    "stream_output": True,
                    "chunk_size": random.choice([8, 10, 12]),
                    "delay": 0.03,
                    "theme": random.choice(["light", "dark"]),
                },
            },
            name="/api/settings",
            catch_response=True,
        ) as response:
            self._expect_success(response)

    @task(1)
    def chat(self) -> None:
        """Measure the non-streaming chat endpoint with short prompts."""
        with self.client.post(
            "/api/chat",
            json={
                "message": random.choice(CHAT_PROMPTS),
                "session_id": self.session_id,
                "function": "general_chat",
            },
            name="/api/chat",
            catch_response=True,
        ) as response:
            if not self._expect_success(response):
                return
            payload = response.json()
            if "response" not in payload:
                response.failure("missing response text")

    def _expect_success(self, response) -> bool:
        if response.status_code != 200:
            response.failure(f"unexpected status {response.status_code}")
            return False
        payload = response.json()
        if payload.get("success") is False:
            response.failure(str(payload.get("error") or "success flag is false"))
            return False
        return True
