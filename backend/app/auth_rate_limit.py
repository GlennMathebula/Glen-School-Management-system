from __future__ import annotations

from hashlib import sha256

from fastapi import HTTPException
from redis.exceptions import RedisError

from app.redis_client import get_redis_client


def _identity_digest(identity: str) -> str:
    normalized = str(identity or "").strip().lower()

    if not normalized:
        normalized = "anonymous"

    return sha256(
        normalized.encode("utf-8")
    ).hexdigest()[:32]


def _rate_key(
    scope: str,
    identity: str,
) -> str:
    safe_scope = "".join(
        character
        for character in str(scope or "").strip().lower()
        if (
            character.isalnum()
            or character in ("-", "_", ":")
        )
    )

    if not safe_scope:
        safe_scope = "auth"

    return (
        "gm:sms:auth:"
        f"{safe_scope}:"
        f"{_identity_digest(identity)}"
    )


def enforce_auth_rate_limit(
    *,
    scope: str,
    identity: str,
    limit: int,
    window_seconds: int,
) -> dict:
    # Redis burst protection only. PostgreSQL lockouts remain authoritative.
    # Fail-open is deliberate so a Redis outage does not block legitimate login.
    limit = max(1, int(limit))
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

    key = _rate_key(
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
            detail=(
                "Too many authentication attempts. "
                "Please wait before trying again."
            ),
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
