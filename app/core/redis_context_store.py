# -*- coding: utf-8 -*-
"""Redis-backed short-term conversation memory."""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from app.utils.redis_client import RedisClient


class RedisContextStore:
    """Store recent K-turn context in Redis lists with TTL."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        redis_config = self.config.get("redis") or self.config
        self.redis = RedisClient(redis_config)
        self.ttl_seconds = int(redis_config.get("context_ttl_seconds", 86400))
        self.max_history_length = int(self.config.get("max_history_length", 10))

    @property
    def available(self) -> bool:
        return self.redis.available

    def _key(self, user_id: str) -> str:
        return f"context:{user_id}"

    def append(self, user_id: str, role: str, content: str) -> None:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        item = json.dumps(
            {"role": role, "content": content, "timestamp": time.time()},
            ensure_ascii=False,
        )
        key = self._key(user_id)
        pipe = self.redis.client.pipeline()
        pipe.rpush(key, item)
        pipe.ltrim(key, -self.max_history_length, -1)
        pipe.expire(key, self.ttl_seconds)
        pipe.execute()

    def replace(self, user_id: str, messages: List[Dict[str, Any]]) -> None:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        key = self._key(user_id)
        pipe = self.redis.client.pipeline()
        pipe.delete(key)
        for message in messages[-self.max_history_length :]:
            pipe.rpush(key, json.dumps(message, ensure_ascii=False))
        pipe.expire(key, self.ttl_seconds)
        pipe.execute()

    def get(self, user_id: str, depth: Optional[int] = None) -> List[Dict[str, Any]]:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        depth = int(depth or self.max_history_length)
        rows = self.redis.client.lrange(self._key(user_id), -depth, -1)
        messages: List[Dict[str, Any]] = []
        for row in rows:
            try:
                messages.append(json.loads(row))
            except json.JSONDecodeError:
                continue
        return messages

    def get_all(self, user_id: str) -> List[Dict[str, Any]]:
        return self.get(user_id, self.max_history_length)

    def clear(self, user_id: str) -> None:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        self.redis.client.delete(self._key(user_id))

    def status(self) -> Dict[str, Any]:
        payload = self.redis.status()
        payload["context_ttl_seconds"] = self.ttl_seconds
        return payload
