# -*- coding: utf-8 -*-
"""Redis-backed web session state store."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from app.utils.redis_client import RedisClient


class RedisWebSessionStore:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.redis = RedisClient(self.config)
        self.ttl_seconds = int(self.config.get("context_ttl_seconds", 86400))

    @property
    def available(self) -> bool:
        return self.redis.available

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not self.redis.client:
            return None
        payload = self.redis.client.get(self._key(session_id))
        return json.loads(payload) if payload else None

    def set(self, session_id: str, session: Dict[str, Any]) -> None:
        if not self.redis.client:
            raise RuntimeError(self.redis.last_error or "redis_unavailable")
        self.redis.client.setex(
            self._key(session_id),
            self.ttl_seconds,
            json.dumps(session, ensure_ascii=False),
        )

    def delete(self, session_id: str) -> None:
        if self.redis.client:
            self.redis.client.delete(self._key(session_id))

    def status(self) -> Dict[str, Any]:
        status = self.redis.status()
        status["key_prefix"] = "session:"
        return status
