from __future__ import annotations

from collections.abc import Mapping
from functools import wraps
from hashlib import sha256
import inspect
import json

from redis.exceptions import RedisError

from app.redis_client import (
    RedisLockBusyError,
    RedisLockUnavailableError,
    get_redis_client,
    redis_processing_lock,
)


class CommunicationDuplicateError(ValueError):
    pass


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


def _normalise(
    value,
):
    if value is None:
        return "<none>"

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


def communication_dedup_keys(
    *,
    scope: str,
    values: list,
) -> tuple[str, str]:
    safe_scope = "".join(
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
    ) or "communication"

    material = json.dumps(
        {
            "scope": safe_scope,
            "values": [
                _normalise(
                    value
                )
                for value in values
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    digest = sha256(
        material.encode(
            "utf-8"
        )
    ).hexdigest()[:40]

    return (
        (
            "gm:sms:communication:"
            f"inflight:{safe_scope}:{digest}"
        ),
        (
            "gm:sms:communication:"
            f"recent:{safe_scope}:{digest}"
        ),
    )


def _duplicate_result(
    *,
    mode: str,
    bound_arguments: dict,
):
    if mode == "none":
        return None

    if mode == "statement":
        delivery = (
            bound_arguments.get(
                "delivery"
            )
            or {}
        )

        return {
            "student_number": (
                delivery.get(
                    "student_number"
                )
                if isinstance(
                    delivery,
                    Mapping,
                )
                else None
            ),
            "status": "Skipped",
            "reason": (
                "Duplicate statement delivery "
                "was suppressed."
            ),
            "duplicate_suppressed": True,
        }

    if mode == "notification_batch":
        return {
            "sent": 0,
            "skipped": 0,
            "failed": 0,
            "missing_email": 0,
            "force_resend": bool(
                bound_arguments.get(
                    "force_resend",
                    False,
                )
            ),
            "duplicate_suppressed": True,
            "results": [],
        }

    raise CommunicationDuplicateError(
        "This communication is already being "
        "processed or was submitted moments ago."
    )


def communication_guarded_call(
    scope: str,
    *,
    key_fields: tuple[str, ...],
    recent_seconds: int = 10,
    lock_ttl_seconds: int = 60,
    fail_open: bool = True,
    duplicate_mode: str = "raise",
):
    def decorator(func):
        signature = inspect.signature(
            func
        )

        @wraps(func)
        def wrapped(
            *args,
            **kwargs,
        ):
            bound = signature.bind_partial(
                *args,
                **kwargs,
            )

            values = [
                _extract_value(
                    bound.arguments,
                    field,
                )
                for field in key_fields
            ]

            (
                inflight_key,
                recent_key,
            ) = communication_dedup_keys(
                scope=scope,
                values=values,
            )

            try:
                client = get_redis_client()
            except RedisError:
                client = None

            if client is None:
                if fail_open:
                    return func(
                        *args,
                        **kwargs,
                    )

                raise RedisLockUnavailableError(
                    "Redis communication protection "
                    "is unavailable."
                )

            try:
                if (
                    recent_seconds > 0
                    and client.exists(
                        recent_key
                    )
                ):
                    return _duplicate_result(
                        mode=duplicate_mode,
                        bound_arguments=(
                            bound.arguments
                        ),
                    )
            except RedisError:
                if fail_open:
                    return func(
                        *args,
                        **kwargs,
                    )

                raise RedisLockUnavailableError(
                    "Redis communication protection "
                    "is unavailable."
                )

            try:
                with redis_processing_lock(
                    inflight_key,
                    ttl_seconds=(
                        lock_ttl_seconds
                    ),
                    busy_message=(
                        "This communication is already "
                        "being processed."
                    ),
                ):
                    try:
                        if (
                            recent_seconds > 0
                            and client.exists(
                                recent_key
                            )
                        ):
                            return _duplicate_result(
                                mode=duplicate_mode,
                                bound_arguments=(
                                    bound.arguments
                                ),
                            )
                    except RedisError:
                        if not fail_open:
                            raise RedisLockUnavailableError(
                                "Redis communication "
                                "protection is unavailable."
                            )

                    result = func(
                        *args,
                        **kwargs,
                    )

                    if recent_seconds > 0:
                        try:
                            client.set(
                                recent_key,
                                "1",
                                ex=recent_seconds,
                            )
                        except RedisError:
                            if not fail_open:
                                raise RedisLockUnavailableError(
                                    "Redis communication "
                                    "protection is unavailable."
                                )

                    return result

            except RedisLockBusyError:
                return _duplicate_result(
                    mode=duplicate_mode,
                    bound_arguments=(
                        bound.arguments
                    ),
                )

            except RedisLockUnavailableError:
                if fail_open:
                    return func(
                        *args,
                        **kwargs,
                    )

                raise

        return wrapped

    return decorator
