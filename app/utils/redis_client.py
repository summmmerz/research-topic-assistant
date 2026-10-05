# -*- coding: utf-8 -*-
"""Optional Redis client wrapper used by context and cache stores."""

from __future__ import annotations

from typing import Any, Dict, Optional


class RedisClient:
    """Create a Redis connection without making Redis mandatory."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.client = None
        self.last_error: Optional[str] = None
        self._connect()

    @property
    def available(self) -> bool:
        return self.client is not None

    def _connect(self) -> None:
        url = self.config.get("url")
        if not url:
            self.last_error = "redis_not_configured"
            return
        try:
            import redis

            self.client = redis.Redis.from_url(url, decode_responses=True)
            self.client.ping()
            self.last_error = None
        except Exception as exc:  # pragma: no cover - depends on local service
            self.client = None
            self.last_error = str(exc)

    def status(self) -> Dict[str, Any]:
        return {
            "available": self.available,
            "storage": "redis" if self.available else "json_fallback",
            "last_error": self.last_error,
        }
