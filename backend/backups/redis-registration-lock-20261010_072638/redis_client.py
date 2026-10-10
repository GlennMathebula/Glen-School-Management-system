from __future__ import annotations

from functools import lru_cache
from typing import Any

import redis
from redis import Redis

from app.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> Redis | None:
    """
    Return a lazily-created Redis client.

    No network connection is made while FastAPI imports. This keeps the
    application available even if Redis is temporarily unavailable.
    """
    if not settings.redis_url:
        return None

    return redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
    )


def get_redis_health() -> dict[str, Any]:
    """
    Check Redis without exposing credentials or the connection URL.
    """
    client = get_redis_client()

    if client is None:
        return {
            "healthy": False,
            "configured": False,
            "service": "Redis",
            "message": "REDIS_URL is not configured.",
            "version": None,
        }

    try:
        ping_ok = bool(client.ping())

        version = None
        try:
            server_info = client.info(section="server")
            version = server_info.get("redis_version")
        except Exception:
            # Version information is optional; a successful PING is enough.
            pass

        return {
            "healthy": ping_ok,
            "configured": True,
            "service": "Redis",
            "message": (
                "Redis connection is healthy."
                if ping_ok
                else "Redis did not acknowledge the health check."
            ),
            "version": version,
        }

    except Exception as error:
        return {
            "healthy": False,
            "configured": True,
            "service": "Redis",
            "message": "Redis connection is unavailable.",
            "version": None,
            "error_type": type(error).__name__,
        }