from __future__ import annotations

from sqlalchemy import text

from app.database import engine
from app.services.staff_audit_service import create_staff_audit_log


def _student_exists(connection, student_number: str) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT 1
                FROM public.applications
                WHERE student_number = :student_number
                LIMIT 1
                """
            ),
            {"student_number": student_number},
        ).first()
    )


def _get_record(connection, student_number: str):
    return connection.execute(
        text(
            """
            SELECT *
            FROM public.certification_tracking
            WHERE student_number = :student_number
            LIMIT 1
            """
        ),
        {"student_number": student_number},
    ).mappings().first()


def _ensure_record(connection, student_number: str, staff_code: str):
    connection.execute(
        text(
            """
            INSERT INTO public.certification_tracking (
                student_number,
                completion_status,
                graduation_status,
                certificate_status,
                updated_by
            )
            VALUES (
                :student_number,
                'Pending',
                'Pending',
                'Pending',
                :staff_code
            )
            ON CONFLICT (student_number)
            DO NOTHING
            """
        ),
        {
            "student_number": student_number,
            "staff_code": staff_code,
        },
    )


def get_completion_tracking(student_number: str) -> dict:
    student_number = str(student_number or "").strip()

    with engine.connect() as connection:
        row = _get_record(connection, student_number)

    return dict(row) if row else {
        "student_number": student_number,
        "completion_status": "Pending",
        "graduation_status": "Pending",
        "certificate_status": "Pending",
    }


def update_completion_status(
    *,
    actor_staff_code: str,
    student_number: str,
    completion_status: str,
    completion_date,
    notes: str | None,
) -> dict:
    student_number = str(student_number or "").strip()
    completion_status = str(completion_status or "").strip()

    with engine.begin() as connection:
        if not _student_exists(connection, student_number):
            raise ValueError("Student was not found.")

        _ensure_record(connection, student_number, actor_staff_code)
        before = _get_record(connection, student_number)

        row = connection.execute(
            text(
                """
                UPDATE public.certification_tracking
                SET
                    completion_status = :completion_status,
                    completion_date = :completion_date,
                    notes = COALESCE(:notes, notes),
                    updated_by = :staff_code,
                    updated_at = NOW()
                WHERE student_number = :student_number
                RETURNING *
                """
            ),
            {
                "completion_status": completion_status,
                "completion_date": completion_date,
                "notes": str(notes or "").strip() or None,
                "staff_code": actor_staff_code,
                "student_number": student_number,
            },
        ).mappings().first()

    record = dict(row)

    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code="ADMIN_COMPLETION_UPDATED",
            module_code="ADMIN_COMPLETION",
            entity_type="STUDENT_COMPLETION",
            entity_id=student_number,
            description="Admin updated learner completion status.",
            before_data=dict(before) if before else None,
            after_data=record,
            metadata={},
        )
    except Exception as error:
        print(f"WARNING: completion audit log failed: {error}")

    return record


def update_certification(
    *,
    actor_staff_code: str,
    student_number: str,
    certificate_status: str,
    certificate_number: str | None,
    certificate_date,
    certificate_received_date,
    certificate_issued_date,
    notes: str | None,
) -> dict:
    student_number = str(student_number or "").strip()

    with engine.begin() as connection:
        if not _student_exists(connection, student_number):
            raise ValueError("Student was not found.")

        _ensure_record(connection, student_number, actor_staff_code)
        before = _get_record(connection, student_number)

        row = connection.execute(
            text(
                """
                UPDATE public.certification_tracking
                SET
                    certificate_status = :certificate_status,
                    certificate_number = :certificate_number,
                    certificate_date = :certificate_date,
                    certificate_received_date = :certificate_received_date,
                    certificate_issued_date = :certificate_issued_date,
                    notes = COALESCE(:notes, notes),
                    updated_by = :staff_code,
                    updated_at = NOW()
                WHERE student_number = :student_number
                RETURNING *
                """
            ),
            {
                "certificate_status": str(certificate_status or "").strip(),
                "certificate_number": str(certificate_number or "").strip() or None,
                "certificate_date": certificate_date,
                "certificate_received_date": certificate_received_date,
                "certificate_issued_date": certificate_issued_date,
                "notes": str(notes or "").strip() or None,
                "staff_code": actor_staff_code,
                "student_number": student_number,
            },
        ).mappings().first()

    record = dict(row)

    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code="ADMIN_CERTIFICATION_UPDATED",
            module_code="ADMIN_COMPLETION",
            entity_type="STUDENT_CERTIFICATION",
            entity_id=student_number,
            description="Admin updated learner certification tracking.",
            before_data=dict(before) if before else None,
            after_data=record,
            metadata={},
        )
    except Exception as error:
        print(f"WARNING: certification audit log failed: {error}")

    return record


def update_graduation(
    *,
    actor_staff_code: str,
    student_number: str,
    graduation_status: str,
    graduation_date,
    notes: str | None,
) -> dict:
    student_number = str(student_number or "").strip()

    with engine.begin() as connection:
        if not _student_exists(connection, student_number):
            raise ValueError("Student was not found.")

        _ensure_record(connection, student_number, actor_staff_code)
        before = _get_record(connection, student_number)

        row = connection.execute(
            text(
                """
                UPDATE public.certification_tracking
                SET
                    graduation_status = :graduation_status,
                    graduation_date = :graduation_date,
                    notes = COALESCE(:notes, notes),
                    updated_by = :staff_code,
                    updated_at = NOW()
                WHERE student_number = :student_number
                RETURNING *
                """
            ),
            {
                "graduation_status": str(graduation_status or "").strip(),
                "graduation_date": graduation_date,
                "notes": str(notes or "").strip() or None,
                "staff_code": actor_staff_code,
                "student_number": student_number,
            },
        ).mappings().first()

        application_columns = set(
            connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'applications'
                    """
                )
            ).scalars().all()
        )

        if "graduation_date" in application_columns and graduation_date:
            connection.execute(
                text(
                    """
                    UPDATE public.applications
                    SET graduation_date = :graduation_date
                    WHERE student_number = :student_number
                    """
                ),
                {
                    "graduation_date": graduation_date,
                    "student_number": student_number,
                },
            )

    record = dict(row)

    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code="ADMIN_GRADUATION_UPDATED",
            module_code="ADMIN_COMPLETION",
            entity_type="STUDENT_GRADUATION",
            entity_id=student_number,
            description="Admin updated learner graduation tracking.",
            before_data=dict(before) if before else None,
            after_data=record,
            metadata={},
        )
    except Exception as error:
        print(f"WARNING: graduation audit log failed: {error}")

    return record
