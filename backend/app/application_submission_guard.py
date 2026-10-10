from __future__ import annotations

from contextlib import ExitStack, contextmanager
from hashlib import sha256

from app.redis_client import (
    RedisLockUnavailableError,
    redis_processing_lock,
)


def _digest(
    kind: str,
    value: str,
) -> str:
    normalized = str(
        value or ""
    ).strip().lower()

    material = (
        f"{kind}:"
        f"{normalized}"
    )

    return sha256(
        material.encode("utf-8")
    ).hexdigest()[:32]


def application_submission_lock_keys(
    application_data: dict,
) -> list[str]:
    email = str(
        application_data.get(
            "email"
        )
        or ""
    ).strip().lower()

    national_id = str(
        application_data.get(
            "national_id"
        )
        or ""
    ).strip()

    keys = []

    if email:
        keys.append(
            "gm:sms:applications:submit:"
            f"email:{_digest('email', email)}"
        )

    if national_id:
        keys.append(
            "gm:sms:applications:submit:"
            f"national-id:"
            f"{_digest('national-id', national_id)}"
        )

    return sorted(
        set(keys)
    )


@contextmanager
def application_submission_guard(
    application_data: dict,
):
    keys = application_submission_lock_keys(
        application_data
    )

    if not keys:
        yield
        return

    stack = ExitStack()

    try:
        for key in keys:
            stack.enter_context(
                redis_processing_lock(
                    key,
                    ttl_seconds=120,
                    busy_message=(
                        "This application is already "
                        "being processed. Please wait "
                        "a moment and try again."
                    ),
                )
            )

    except RedisLockUnavailableError:
        stack.close()

        # PostgreSQL UNIQUE indexes remain the final
        # correctness layer, so a Redis outage must not
        # prevent a legitimate public application.
        yield
        return

    try:
        yield
    finally:
        stack.close()
