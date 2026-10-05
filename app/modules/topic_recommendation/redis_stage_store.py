# -*- coding: utf-8 -*-
"""Redis persistence for staged topic recommendation sessions."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.utils.redis_client import RedisClient


class RedisStageSessionStore:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.redis = RedisClient(self.config)
        self.ttl_seconds = int(self.config.get("context_ttl_seconds", 86400))

    @property
    def available(self) -> bool:
        return self.redis.available

    def _key(self, session_id: str) -> str:
        return f"recommendation_stage:{session_id}"

    def save(self, session_id: str, session: Dict[str, Any]) -> None:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        self.redis.client.setex(
            self._key(session_id),
            self.ttl_seconds,
            json.dumps(session, ensure_ascii=False),
        )

    def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        payload = self.redis.client.get(self._key(session_id))
        if not payload:
            return None
        return json.loads(payload)

    def delete(self, session_id: str) -> None:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        self.redis.client.delete(self._key(session_id))

    def status(self) -> Dict[str, Any]:
        status = self.redis.status()
        status["key_prefix"] = "recommendation_stage:"
        return status
