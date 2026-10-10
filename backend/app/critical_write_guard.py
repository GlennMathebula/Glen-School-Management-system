from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from functools import wraps
from hashlib import sha256
import inspect
import json

from fastapi import HTTPException

from app.redis_client import (
    RedisLockBusyError,
    RedisLockUnavailableError,
    redis_processing_lock,
)


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


def _normalise_value(
    value,
) -> str:
    if value is None:
        return "<none>"

    if isinstance(
        value,
        Mapping,
    ):
        return json.dumps(
            {
                str(key): _normalise_value(
                    item
                )
                for key, item in sorted(
                    value.items(),
                    key=lambda pair: str(
                        pair[0]
                    ),
                )
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    if isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        values = sorted(
            _normalise_value(
                item
            )
            for item in value
        )

        return json.dumps(
            values,
            separators=(",", ":"),
        )

    return str(
        value
    ).strip().lower()


def critical_write_lock_key(
    scope: str,
    values: list,
) -> str:
    normalised_scope = str(
        scope or ""
    ).strip().lower()

    material = json.dumps(
        {
            "scope": normalised_scope,
            "values": [
                _normalise_value(
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
        "gm:sms:critical-write:"
        f"{normalised_scope}:"
        f"{digest}"
    )


@contextmanager
def critical_write_lock(
    *,
    scope: str,
    values: list,
    ttl_seconds: int = 120,
    busy_message: str = (
        "This operation is already being processed. "
        "Please wait a moment and try again."
    ),
    fail_open: bool = False,
):
    key = critical_write_lock_key(
        scope,
        values,
    )

    try:
        with redis_processing_lock(
            key,
            ttl_seconds=ttl_seconds,
            busy_message=busy_message,
        ):
            yield

    except RedisLockUnavailableError:
        if fail_open:
            yield
            return

        raise


def redis_guarded_call(
    scope: str,
    *,
    key_fields: tuple[str, ...],
    ttl_seconds: int = 120,
    busy_message: str = (
        "This operation is already being processed. "
        "Please wait a moment and try again."
    ),
    fail_open: bool = False,
):
    def decorator(func):
        signature = inspect.signature(
            func
        )

        @wraps(func)
        def wrapped(*args, **kwargs):
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

            with critical_write_lock(
                scope=scope,
                values=values,
                ttl_seconds=ttl_seconds,
                busy_message=busy_message,
                fail_open=fail_open,
            ):
                return func(
                    *args,
                    **kwargs,
                )

        return wrapped

    return decorator


def redis_guarded_endpoint(
    scope: str,
    *,
    key_fields: tuple[str, ...],
    ttl_seconds: int = 120,
    busy_message: str = (
        "This operation is already being processed. "
        "Please wait a moment and try again."
    ),
    unavailable_message: str = (
        "Processing protection is temporarily unavailable. "
        "Please try again shortly."
    ),
    fail_open: bool = False,
):
    def decorator(func):
        signature = inspect.signature(
            func
        )

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

                values = [
                    _extract_value(
                        bound.arguments,
                        field,
                    )
                    for field in key_fields
                ]

                try:
                    with critical_write_lock(
                        scope=scope,
                        values=values,
                        ttl_seconds=ttl_seconds,
                        busy_message=busy_message,
                        fail_open=fail_open,
                    ):
                        return await func(
                            *args,
                            **kwargs,
                        )

                except RedisLockBusyError as error:
                    raise HTTPException(
                        status_code=409,
                        detail=str(error),
                    ) from error

                except RedisLockUnavailableError as error:
                    raise HTTPException(
                        status_code=503,
                        detail=unavailable_message,
                    ) from error

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

            values = [
                _extract_value(
                    bound.arguments,
                    field,
                )
                for field in key_fields
            ]

            try:
                with critical_write_lock(
                    scope=scope,
                    values=values,
                    ttl_seconds=ttl_seconds,
                    busy_message=busy_message,
                    fail_open=fail_open,
                ):
                    return func(
                        *args,
                        **kwargs,
                    )

            except RedisLockBusyError as error:
                raise HTTPException(
                    status_code=409,
                    detail=str(error),
                ) from error

            except RedisLockUnavailableError as error:
                raise HTTPException(
                    status_code=503,
                    detail=unavailable_message,
                ) from error

        return sync_wrapped

    return decorator
