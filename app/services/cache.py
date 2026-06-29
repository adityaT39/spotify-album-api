"""A tiny Redis-backed cache for public Spotify catalog data.

Degrades gracefully: if Redis is unreachable, reads miss and writes become
no-ops, so the app keeps working (just without caching).
"""

import json
from typing import Any

import redis

from app.config import settings

_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_json(key: str) -> Any | None:
    """Return the cached value for `key`, or None on a miss / if Redis is down."""
    if _client is None:
        return None
    try:
        raw = _client.get(key)
    except redis.RedisError:
        return None
    return json.loads(raw) if raw is not None else None


def set_json(key: str, value: Any, ttl: int = 3600) -> None:
    """Cache a JSON-serializable `value` under `key` for `ttl` seconds."""
    if _client is None:
        return
    try:
        _client.set(key, json.dumps(value), ex=ttl)
    except redis.RedisError:
        pass
