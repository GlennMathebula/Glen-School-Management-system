from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256

from app.redis_client import redis_processing_lock


def _digest(
    student_number: str,
    document_type: str,
) -> str:
    student_number = str(
        student_number or ""
    ).strip().upper()

    document_type = str(
        document_type or ""
    ).strip().upper()

    material = (
        f"{student_number}:"
        f"{document_type}"
    )

    return sha256(
        material.encode("utf-8")
    ).hexdigest()[:32]


def application_document_upload_lock_key(
    *,
    student_number: str,
    document_type: str,
) -> str:
    return (
        "gm:sms:applications:documents:"
        f"{_digest(student_number, document_type)}"
    )


@contextmanager
def application_document_upload_guard(
    *,
    student_number: str,
    document_type: str,
):
    key = application_document_upload_lock_key(
        student_number=student_number,
        document_type=document_type,
    )

    with redis_processing_lock(
        key,
        ttl_seconds=120,
        busy_message=(
            "This document upload is already "
            "being processed. Please wait a "
            "moment and try again."
        ),
    ):
        yield
