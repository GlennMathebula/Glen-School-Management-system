from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from app.services.registration_service import (
    generate_student_enrolment_form,
)


APP_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = APP_DIR.parent
ENROLMENT_DIR = (
    APP_DIR
    / "generated_pdfs"
    / "enrolment_forms"
)


def _student_number(value: str) -> str:
    value = str(value or "").strip().upper()

    if not value:
        raise ValueError(
            "Student number is required."
        )

    if not re.fullmatch(
        r"[A-Z0-9_-]{3,40}",
        value,
    ):
        raise ValueError(
            "Invalid student number."
        )

    return value


def _safe_pdf_path(
    value: str | Path,
) -> Path:
    path = Path(value)

    candidates = []

    if path.is_absolute():
        candidates.append(path)
    else:
        candidates.extend(
            [
                BACKEND_DIR / path,
                APP_DIR / path,
                ENROLMENT_DIR / path.name,
            ]
        )

    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            continue

        if (
            resolved.exists()
            and resolved.is_file()
            and resolved.suffix.lower()
                == ".pdf"
        ):
            return resolved

    raise FileNotFoundError(
        "Generated enrolment form PDF "
        "could not be located."
    )


def get_latest_enrolment_form(
    student_number: str,
) -> dict | None:
    student_number = _student_number(
        student_number
    )

    ENROLMENT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pattern = (
        f"enrolment_form_"
        f"{student_number}_*.pdf"
    )

    matches = [
        path
        for path in ENROLMENT_DIR.glob(
            pattern
        )
        if path.is_file()
    ]

    if not matches:
        return None

    latest = max(
        matches,
        key=lambda item: (
            item.stat().st_mtime,
            item.name,
        ),
    )

    stat = latest.stat()

    return {
        "student_number": (
            student_number
        ),
        "available": True,
        "filename": latest.name,
        "pdf_path": str(
            latest.resolve()
        ),
        "generated_at": datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
        "size_bytes": stat.st_size,
        "requires_learner_signature": True,
        "requires_physical_learner_signature": True,
    }


def generate_admin_enrolment_form(
    student_number: str,
) -> dict:
    student_number = _student_number(
        student_number
    )

    result = (
        generate_student_enrolment_form(
            student_number
        )
    )

    pdf_path = _safe_pdf_path(
        result["pdf_path"]
    )

    return {
        "student_number": student_number,
        "generated": True,
        "available": True,
        "filename": pdf_path.name,
        "pdf_path": str(pdf_path),
        "requires_learner_signature": bool(
            result.get(
                "requires_learner_signature",
                True,
            )
        ),
        "requires_physical_learner_signature": bool(
            result.get(
                "requires_physical_learner_signature",
                True,
            )
        ),
    }


def require_latest_enrolment_form(
    student_number: str,
) -> dict:
    record = get_latest_enrolment_form(
        student_number
    )

    if not record:
        raise FileNotFoundError(
            "No generated enrolment form "
            "was found for this student."
        )

    return record
