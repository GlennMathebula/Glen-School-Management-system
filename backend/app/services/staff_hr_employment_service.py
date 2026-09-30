from __future__ import annotations

from sqlalchemy import text

from app.database import engine
from app.services.staff_audit_service import (
    create_staff_audit_log,
)


ALLOWED_FIELDS = {
    "job_title",
    "department",
    "employment_type",
    "employment_status",
}


def _employee_columns(connection) -> set[str]:
    return set(
        connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'employees'
                """
            )
        ).scalars().all()
    )


def update_hr_employee_employment(
    *,
    actor_staff_code: str,
    employee_id: str,
    updates: dict,
) -> dict:
    with engine.begin() as connection:
        columns = _employee_columns(connection)

        if "id" not in columns:
            raise ValueError(
                "The employees table does not expose the expected id column."
            )

        clean = {
            key: value
            for key, value in updates.items()
            if (
                key in ALLOWED_FIELDS
                and key in columns
                and value is not None
            )
        }

        if not clean:
            raise ValueError(
                "No supported employment fields were supplied."
            )

        before = connection.execute(
            text(
                """
                SELECT *
                FROM public.employees
                WHERE id = CAST(:employee_id AS uuid)
                LIMIT 1
                """
            ),
            {"employee_id": employee_id},
        ).mappings().first()

        if not before:
            raise ValueError("Employee was not found.")

        sets = [
            f'"{key}" = :{key}'
            for key in clean
        ]

        if "updated_at" in columns:
            sets.append("updated_at = NOW()")

        row = connection.execute(
            text(
                f"""
                UPDATE public.employees
                SET {", ".join(sets)}
                WHERE id = CAST(:employee_id AS uuid)
                RETURNING *
                """
            ),
            {
                **clean,
                "employee_id": employee_id,
            },
        ).mappings().first()

    record = dict(row)

    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code="HR_EMPLOYMENT_UPDATED",
            module_code="HR_RECRUITMENT",
            entity_type="EMPLOYEE",
            entity_id=str(employee_id),
            description=(
                "HR updated employee employment information."
            ),
            before_data=dict(before),
            after_data=record,
            metadata={},
        )
    except Exception as error:
        print(
            "WARNING: Employment update succeeded but "
            f"audit logging failed: {error}"
        )

    return record
