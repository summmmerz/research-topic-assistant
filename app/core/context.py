#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Conversation context manager."""

from typing import Any, Dict, List, Optional
import json
import os
import threading
import time

from app.core.redis_context_store import RedisContextStore


class ContextManager:
    """Manage per-user conversation history and compressed long-term context."""

    SUMMARY_PREFIX = "此前对话摘要（用于延续上下文）：\n"

    def __init__(self, config: Dict[str, Any]):
        self.config = {
            "max_history_length": config.get("max_history_length", 10),
            "max_context_depth": config.get("max_context_depth", 5),
            "save_interval": config.get("save_interval", 300),
            "context_file": config.get("context_file", "data/contexts/contexts.json"),
            "auto_save": config.get("auto_save", True),
            "auto_load": config.get("auto_load", True),
            "auto_summarize": config.get("auto_summarize", True),
            "summary_trigger_length": config.get(
                "summary_trigger_length", config.get("max_history_length", 10)
            ),
            "summary_keep_recent": config.get(
                "summary_keep_recent", config.get("max_context_depth", 5)
            ),
            "max_summary_chars": config.get("max_summary_chars", 1200),
        }
        self.config["storage_backend"] = config.get("storage_backend", "json")
        self.config["redis"] = config.get("redis", {})

        self.redis_store = None
        self.storage_backend = "json"
        if self.config["storage_backend"] == "redis":
            self.redis_store = RedisContextStore(
                {
                    "max_history_length": self._redis_history_length(),
                    "redis": self.config["redis"],
                }
            )
            if self.redis_store.available:
                self.storage_backend = "redis"

        self.contexts: Dict[str, List[Dict[str, Any]]] = {}
        self.last_save_time = time.time()
        self.lock = threading.RLock()

        context_dir = os.path.dirname(self.config["context_file"])
        if context_dir:
            os.makedirs(context_dir, exist_ok=True)

        if self.config["auto_load"]:
            self.load_contexts()

    def update_context(self, user_id: str, content: str, role: str = "user"):
        """Append a message and summarize older context when the limit is reached."""
        with self.lock:
            if self.storage_backend == "redis" and self.redis_store:
                try:
                    self.redis_store.append(user_id, role, content)
                    if self.config["auto_summarize"]:
                        self._summarize_redis_context(user_id)
                    return
                except Exception:
                    self.storage_backend = "json"

            if user_id not in self.contexts:
                self.contexts[user_id] = []

            self.contexts[user_id].append(
                {"role": role, "content": content, "timestamp": time.time()}
            )

            if self.config["auto_summarize"]:
                self._summarize_context(user_id)
            self._trim_history(user_id)

            if self.config["auto_save"]:
                self._check_save()

    def get_context(
        self, user_id: str = "default", depth: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """Return model-ready context: latest summary plus recent messages."""
        with self.lock:
            if self.storage_backend == "redis" and self.redis_store:
                try:
                    return self._format_context_for_model(
                        self.redis_store.get_all(user_id), depth
                    )
                except Exception:
                    self.storage_backend = "json"

            if user_id not in self.contexts:
                return []
            return self._format_context_for_model(self.contexts[user_id], depth)

    def clear_context(self, user_id: str = "default"):
        """Clear one user's context."""
        with self.lock:
            if self.storage_backend == "redis" and self.redis_store:
                try:
                    self.redis_store.clear(user_id)
                    return
                except Exception:
                    self.storage_backend = "json"

            if user_id in self.contexts:
                del self.contexts[user_id]

            if self.config["auto_save"]:
                self.save_contexts()

    def _trim_history(self, user_id: str):
        if len(self.contexts[user_id]) <= self.config["max_history_length"]:
            return

        summary = self._latest_summary(self.contexts[user_id])
        normal_messages = [
            msg for msg in self.contexts[user_id] if not self._is_summary_message(msg)
        ]
        if summary:
            keep_count = max(self.config["max_history_length"] - 1, 0)
            self.contexts[user_id] = [summary] + normal_messages[-keep_count:]
        else:
            self.contexts[user_id] = normal_messages[-self.config["max_history_length"] :]

    def _summarize_redis_context(self, user_id: str):
        if not self.redis_store:
            return
        messages = self.redis_store.get_all(user_id)
        summarized = self._summarized_messages(messages)
        if summarized != messages:
            self.redis_store.replace(user_id, summarized)

    def _summarize_context(self, user_id: str):
        self.contexts[user_id] = self._summarized_messages(self.contexts[user_id])

    def _summarized_messages(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        normal_messages = [msg for msg in messages if not self._is_summary_message(msg)]
        if len(normal_messages) <= self.config["summary_trigger_length"]:
            return messages

        keep_recent = min(
            self.config["summary_keep_recent"],
            max(self.config["summary_trigger_length"] - 1, 1),
        )
        messages_to_summarize = normal_messages[:-keep_recent]
        recent_messages = normal_messages[-keep_recent:]
        if not messages_to_summarize:
            return messages

        summary_message = {
            "role": "system",
            "content": self.SUMMARY_PREFIX
            + self._build_summary(
                self._latest_summary_content(messages), messages_to_summarize
            ),
            "timestamp": time.time(),
            "type": "context_summary",
        }
        return [summary_message] + recent_messages

    def _build_summary(
        self, existing_summary: str, messages: List[Dict[str, Any]]
    ) -> str:
        sections: List[str] = []
        if existing_summary:
            sections.append(existing_summary)

        role_names = {"user": "用户", "assistant": "助手", "system": "系统"}
        for msg in messages:
            content = " ".join(str(msg.get("content", "")).split())
            if not content:
                continue
            role = role_names.get(msg.get("role", ""), msg.get("role", "消息"))
            sections.append(f"- {role}: {content}")

        summary = "\n".join(sections)
        max_chars = int(self.config["max_summary_chars"])
        if len(summary) > max_chars:
            summary = summary[-max_chars:].lstrip()
            first_line_break = summary.find("\n")
            if first_line_break > 0:
                summary = summary[first_line_break + 1 :]
            summary = f"（摘要已压缩，保留最近关键信息）\n{summary}"
        return summary

    def _format_context_for_model(
        self, messages: List[Dict[str, Any]], depth: Optional[int] = None
    ) -> List[Dict[str, str]]:
        if depth is None:
            depth = self.config["max_context_depth"]

        summary = self._latest_summary(messages)
        normal_messages = [
            msg for msg in messages if not self._is_summary_message(msg)
        ]
        recent_messages = normal_messages[-min(depth, len(normal_messages)) :]

        formatted_messages: List[Dict[str, str]] = []
        if summary:
            formatted_messages.append(
                {"role": summary["role"], "content": summary["content"]}
            )
        formatted_messages.extend(
            {"role": msg["role"], "content": msg["content"]}
            for msg in recent_messages
            if "role" in msg and "content" in msg
        )
        return formatted_messages

    def _latest_summary(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        summaries = [msg for msg in messages if self._is_summary_message(msg)]
        return summaries[-1] if summaries else None

    def _latest_summary_content(self, messages: List[Dict[str, Any]]) -> str:
        summary = self._latest_summary(messages)
        if not summary:
            return ""
        content = summary.get("content", "")
        if content.startswith(self.SUMMARY_PREFIX):
            return content[len(self.SUMMARY_PREFIX) :]
        return content

    def _is_summary_message(self, message: Dict[str, Any]) -> bool:
        return message.get("type") == "context_summary"

    def _redis_history_length(self) -> int:
        if not self.config["auto_summarize"]:
            return self.config["max_history_length"]
        return max(
            self.config["max_history_length"],
            self.config["summary_trigger_length"] + 1,
        )

    def _check_save(self):
        current_time = time.time()
        if current_time - self.last_save_time >= self.config["save_interval"]:
            self.save_contexts()
            self.last_save_time = current_time

    def save_contexts(self):
        try:
            with self.lock:
                save_data = {
                    "version": "1.0",
                    "timestamp": time.time(),
                    "contexts": self.contexts,
                }
                with open(self.config["context_file"], "w", encoding="utf-8") as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存上下文失败: {str(e)}")

    def load_contexts(self):
        try:
            with self.lock:
                if os.path.exists(self.config["context_file"]):
                    with open(self.config["context_file"], "r", encoding="utf-8") as f:
                        load_data = json.load(f)

                    if load_data.get("version") == "1.0":
                        self.contexts = load_data.get("contexts", {})

                    self._clean_expired_contexts()
        except Exception as e:
            print(f"加载上下文失败: {str(e)}")

    def _clean_expired_contexts(self):
        current_time = time.time()
        expired_users = []

        for user_id, context in self.contexts.items():
            if not context:
                expired_users.append(user_id)
                continue

            last_msg_time = context[-1].get("timestamp", 0)
            if current_time - last_msg_time > 24 * 3600:
                expired_users.append(user_id)

        for user_id in expired_users:
            del self.contexts[user_id]

    def update_config(self, config: Dict[str, Any]):
        with self.lock:
            self.config.update(config)

            context_dir = os.path.dirname(self.config["context_file"])
            if context_dir:
                os.makedirs(context_dir, exist_ok=True)

            for user_id in self.contexts:
                if self.config["auto_summarize"]:
                    self._summarize_context(user_id)
                self._trim_history(user_id)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "storage": self.storage_backend,
                "redis": self.redis_store.status() if self.redis_store else None,
                "num_users": len(self.contexts),
                "total_messages": sum(len(context) for context in self.contexts.values()),
                "max_history_length": self.config["max_history_length"],
                "max_context_depth": self.config["max_context_depth"],
                "auto_summarize": self.config["auto_summarize"],
                "summary_trigger_length": self.config["summary_trigger_length"],
                "summary_keep_recent": self.config["summary_keep_recent"],
                "last_save_time": self.last_save_time,
            }

    def get_user_ids(self) -> List[str]:
        with self.lock:
            return list(self.contexts.keys())

    def get_user_context_size(self, user_id: str) -> int:
        with self.lock:
            if user_id in self.contexts:
                return len(self.contexts[user_id])
            return 0

    def export_context(self, user_id: str) -> Dict[str, Any]:
        with self.lock:
            if user_id in self.contexts:
                return {
                    "user_id": user_id,
                    "context": self.contexts[user_id],
                    "export_time": time.time(),
                }
            return {"user_id": user_id, "context": [], "export_time": time.time()}

    def import_context(self, user_id: str, context_data: List[Dict[str, Any]]):
        with self.lock:
            valid_context = []
            for item in context_data:
                if "role" in item and "content" in item:
                    valid_context.append(
                        {
                            "role": item["role"],
                            "content": item["content"],
                            "timestamp": item.get("timestamp", time.time()),
                            **(
                                {"type": item["type"]}
                                if item.get("type") == "context_summary"
                                else {}
                            ),
                        }
                    )

            self.contexts[user_id] = valid_context

            if self.config["auto_summarize"]:
                self._summarize_context(user_id)
            self._trim_history(user_id)

            if self.config["auto_save"]:
                self.save_contexts()
