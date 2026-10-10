from __future__ import annotations

from collections.abc import Mapping
from functools import wraps
from hashlib import sha256
import inspect
import json

from fastapi.encoders import jsonable_encoder
from redis.exceptions import RedisError

from app.redis_client import get_redis_client


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

    return safe or "read"


def _normalise(
    value,
):
    if value is None:
        return None

    if hasattr(
        value,
        "model_dump",
    ):
        value = value.model_dump()

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _normalise(
                item
            )
            for key, item in sorted(
                value.items(),
                key=lambda pair: str(
                    pair[0]
                ),
            )
        }

    if isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        return [
            _normalise(
                item
            )
            for item in value
        ]

    return str(
        value
    ).strip().lower()


def _extract_value(
    bound_arguments: dict,
    field_path: str,
):
    parts = field_path.split(".")

    value = bound_arguments.get(
        parts[0]
    )

    for part in parts[1:]:
        if value is None:
            return None

        if isinstance(
            value,
            Mapping,
        ):
            value = value.get(
                part
            )
        else:
            value = getattr(
                value,
                part,
                None,
            )

    return value


def cache_version_key(
    scope: str,
) -> str:
    return (
        "gm:sms:cache-version:"
        f"{_safe_scope(scope)}"
    )


def get_cache_version(
    scope: str,
    *,
    client=None,
) -> int:
    if client is None:
        client = get_redis_client()

    if client is None:
        return 0

    try:
        value = client.get(
            cache_version_key(
                scope
            )
        )

        if value is None:
            return 0

        return int(
            value
        )

    except (
        RedisError,
        TypeError,
        ValueError,
    ):
        return 0


def bump_cache_version(
    scope: str,
) -> bool:
    client = get_redis_client()

    if client is None:
        return False

    try:
        client.incr(
            cache_version_key(
                scope
            )
        )

        return True

    except RedisError:
        return False


def redis_cache_key(
    *,
    scope: str,
    version: int,
    values: list,
) -> str:
    safe_scope = _safe_scope(
        scope
    )

    material = json.dumps(
        {
            "scope": safe_scope,
            "version": int(
                version
            ),
            "values": [
                _normalise(
                    value
                )
                for value in values
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )

    digest = sha256(
        material.encode(
            "utf-8"
        )
    ).hexdigest()[:40]

    return (
        "gm:sms:cache:"
        f"{safe_scope}:"
        f"v{int(version)}:"
        f"{digest}"
    )


def redis_cached_endpoint(
    scope: str,
    *,
    key_fields: tuple[str, ...] = (),
    ttl_seconds: int = 180,
):
    def decorator(func):
        signature = inspect.signature(
            func
        )

        def values_from(
            bound_arguments: dict,
        ) -> list:
            return [
                _extract_value(
                    bound_arguments,
                    field,
                )
                for field in key_fields
            ]

        if inspect.iscoroutinefunction(
            func
        ):
            @wraps(func)
            async def async_wrapped(
                *args,
                **kwargs,
            ):
                bound = signature.bind_partial(
                    *args,
                    **kwargs,
                )

                client = get_redis_client()

                if client is None:
                    return await func(
                        *args,
                        **kwargs,
                    )

                version = get_cache_version(
                    scope,
                    client=client,
                )

                key = redis_cache_key(
                    scope=scope,
                    version=version,
                    values=values_from(
                        bound.arguments
                    ),
                )

                try:
                    cached = client.get(
                        key
                    )

                    if cached is not None:
                        if isinstance(
                            cached,
                            bytes,
                        ):
                            cached = cached.decode(
                                "utf-8"
                            )

                        return json.loads(
                            cached
                        )

                except (
                    RedisError,
                    json.JSONDecodeError,
                    UnicodeDecodeError,
                ):
                    pass

                result = await func(
                    *args,
                    **kwargs,
                )

                try:
                    encoded = jsonable_encoder(
                        result
                    )

                    client.set(
                        key,
                        json.dumps(
                            encoded,
                            sort_keys=True,
                            separators=(",", ":"),
                            default=str,
                        ),
                        ex=max(
                            10,
                            int(
                                ttl_seconds
                            ),
                        ),
                    )

                except (
                    RedisError,
                    TypeError,
                    ValueError,
                ):
                    pass

                return result

            return async_wrapped

        @wraps(func)
        def sync_wrapped(
            *args,
            **kwargs,
        ):
            bound = signature.bind_partial(
                *args,
                **kwargs,
            )

            client = get_redis_client()

            if client is None:
                return func(
                    *args,
                    **kwargs,
                )

            version = get_cache_version(
                scope,
                client=client,
            )

            key = redis_cache_key(
                scope=scope,
                version=version,
                values=values_from(
                    bound.arguments
                ),
            )

            try:
                cached = client.get(
                    key
                )

                if cached is not None:
                    if isinstance(
                        cached,
                        bytes,
                    ):
                        cached = cached.decode(
                            "utf-8"
                        )

                    return json.loads(
                        cached
                    )

            except (
                RedisError,
                json.JSONDecodeError,
                UnicodeDecodeError,
            ):
                pass

            result = func(
                *args,
                **kwargs,
            )

            try:
                encoded = jsonable_encoder(
                    result
                )

                client.set(
                    key,
                    json.dumps(
                        encoded,
                        sort_keys=True,
                        separators=(",", ":"),
                        default=str,
                    ),
                    ex=max(
                        10,
                        int(
                            ttl_seconds
                        ),
                    ),
                )

            except (
                RedisError,
                TypeError,
                ValueError,
            ):
                pass

            return result

        return sync_wrapped

    return decorator


def redis_invalidate_after(
    scopes: tuple[str, ...],
):
    def decorator(func):
        if inspect.iscoroutinefunction(
            func
        ):
            @wraps(func)
            async def async_wrapped(
                *args,
                **kwargs,
            ):
                result = await func(
                    *args,
                    **kwargs,
                )

                for scope in scopes:
                    bump_cache_version(
                        scope
                    )

                return result

            return async_wrapped

        @wraps(func)
        def sync_wrapped(
            *args,
            **kwargs,
        ):
            result = func(
                *args,
                **kwargs,
            )

            for scope in scopes:
                bump_cache_version(
                    scope
                )

            return result

        return sync_wrapped

    return decorator
