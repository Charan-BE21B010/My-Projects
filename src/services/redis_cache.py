from __future__ import annotations

import hashlib
import json
from typing import Any


class RedisCache:
    """Redis cache with in-memory fallback when Redis is unavailable."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0", ttl_seconds: int = 300, enabled: bool = True):
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self._memory: dict[str, str] = {}
        self.client = None
        if enabled:
            try:
                import redis

                self.client = redis.Redis.from_url(redis_url, decode_responses=True)
                self.client.ping()
            except Exception:
                self.client = None

    @staticmethod
    def make_key(payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str)
        return "fraud:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            if self.client is not None:
                value = self.client.get(key)
            else:
                value = self._memory.get(key)
            if value:
                return json.loads(value)
        except Exception:
            return None
        return None

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self.enabled:
            return
        raw = json.dumps(value)
        try:
            if self.client is not None:
                self.client.setex(key, self.ttl_seconds, raw)
            else:
                self._memory[key] = raw
        except Exception:
            self._memory[key] = raw
