from __future__ import annotations

from hashlib import sha256

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.redis_client import get_redis_client


def _identity_digest(
    identity: str,
) -> str:
    normalized = str(
        identity or ""
    ).strip().lower()

    if not normalized:
        normalized = "anonymous"

    return sha256(
        normalized.encode(
            "utf-8"
        )
    ).hexdigest()[:32]


def _safe_scope(
    scope: str,
) -> str:
    safe = "".join(
        character
        for character in str(
            scope or ""
        ).strip().lower()
        if (
            character.isalnum()
            or character in (
                "-",
                "_",
                ":",
            )
        )
    )

    return safe or "request"


def abuse_rate_key(
    scope: str,
    identity: str,
) -> str:
    return (
        "gm:sms:abuse:"
        f"{_safe_scope(scope)}:"
        f"{_identity_digest(identity)}"
    )


def enforce_abuse_rate_limit(
    *,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int,
    detail: str = (
        "Too many requests. "
        "Please wait before trying again."
    ),
) -> dict:
    # Abuse protection is deliberately fail-open.
    # Durable authentication/authorization and PostgreSQL
    # account rules remain authoritative when Redis is down.
    limit = max(
        1,
        int(limit),
    )

    window_seconds = max(
        10,
        int(window_seconds),
    )

    client = get_redis_client()

    if client is None:
        return {
            "enforced": False,
            "reason": "redis_not_configured",
        }

    key = abuse_rate_key(
        scope,
        identity,
    )

    script = (
        "local current = redis.call('INCR', KEYS[1]); "
        "if current == 1 then "
        "redis.call('EXPIRE', KEYS[1], ARGV[1]); "
        "end; "
        "local ttl = redis.call('TTL', KEYS[1]); "
        "return {current, ttl};"
    )

    try:
        result = client.eval(
            script,
            1,
            key,
            window_seconds,
        )

        count = int(
            result[0]
        )

        ttl = max(
            1,
            int(
                result[1]
            ),
        )

    except RedisError:
        return {
            "enforced": False,
            "reason": "redis_unavailable",
        }

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail=detail,
            headers={
                "Retry-After": str(
                    ttl
                ),
            },
        )

    return {
        "enforced": True,
        "count": count,
        "limit": limit,
        "retry_after_seconds": ttl,
    }


def enforce_resend_cooldown(
    *,
    scope: str,
    identity: str,
    cooldown_seconds: int = 60,
    hourly_limit: int = 5,
) -> dict:
    cooldown = enforce_abuse_rate_limit(
        scope=f"{scope}:cooldown",
        identity=identity,
        limit=1,
        window_seconds=cooldown_seconds,
        detail=(
            "This item was already sent recently. "
            "Please wait before requesting another copy."
        ),
    )

    hourly = enforce_abuse_rate_limit(
        scope=f"{scope}:hour",
        identity=identity,
        limit=hourly_limit,
        window_seconds=3600,
        detail=(
            "Too many resend requests. "
            "Please wait before trying again."
        ),
    )

    return {
        "cooldown": cooldown,
        "hourly": hourly,
    }
