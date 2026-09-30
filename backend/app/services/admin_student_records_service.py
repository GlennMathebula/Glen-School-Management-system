from __future__ import annotations

from sqlalchemy import text

from app.database import engine


def _clean(value: str | None) -> str | None:
    value = str(value or "").strip()
    return value or None


def list_students(
    *,
    search: str | None = None,
    course_code: str | None = None,
    registration_status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    search = _clean(search)
    course_code = _clean(course_code)
    registration_status = _clean(registration_status)
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    filters: list[str] = []
    params: dict = {"limit": limit, "offset": offset}

    if search:
        filters.append(
            "("
            "a.student_number ILIKE :search "
            "OR a.first_name ILIKE :search "
            "OR a.last_name ILIKE :search "
            "OR a.email ILIKE :search "
            "OR a.national_id ILIKE :search"
            ")"
        )
        params["search"] = f"%{search}%"

    if course_code:
        filters.append("r.course_code = :course_code")
        params["course_code"] = course_code

    if registration_status:
        filters.append(
            "r.registration_status = :registration_status"
        )
        params["registration_status"] = registration_status

    where_sql = ""
    if filters:
        where_sql = "WHERE " + "\nAND ".join(filters)

    base_sql = f"""
        FROM public.applications a

        LEFT JOIN LATERAL (
            SELECT rr.*
            FROM public.registrations rr
            WHERE rr.student_number = a.student_number
            ORDER BY rr.created_at DESC NULLS LAST
            LIMIT 1
        ) r ON TRUE

        LEFT JOIN public.courses c
            ON c.course_code = r.course_code

        LEFT JOIN public.student_accounts sa
            ON sa.student_number = a.student_number

        {where_sql}
    """

    with engine.connect() as connection:
        total = connection.execute(
            text(f"SELECT COUNT(*) {base_sql}"),
            params,
        ).scalar_one()

        rows = connection.execute(
            text(
                f"""
                SELECT
                    a.id AS application_id,
                    a.student_number,
                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    a.email,
                    a.cell_number,
                    a.national_id,
                    a.app_status,
                    a.created_at AS application_created_at,

                    r.id AS registration_id,
                    r.course_code,
                    c.course_name,
                    c.assessment_type,
                    r.registration_status,
                    r.cycle,
                    r.program_start_date,
                    r.expected_completion_date,
                    r.eisa_eligible,

                    sa.account_status

                {base_sql}

                ORDER BY
                    a.last_name,
                    a.first_name,
                    a.student_number

                LIMIT :limit
                OFFSET :offset
                """
            ),
            params,
        ).mappings().all()

    return {
        "count": len(rows),
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "students": [dict(row) for row in rows],
    }


def get_student_record(student_number: str) -> dict | None:
    student_number = str(student_number or "").strip()

    if not student_number:
        raise ValueError("Student number is required.")

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    a.*,

                    r.id AS registration_id,
                    r.course_code,
                    r.registration_date,
                    r.registration_status,
                    r.funding_type,
                    r.cycle,
                    r.program_start_date,
                    r.expected_completion_date,
                    r.eisa_eligible,

                    c.course_name,
                    c.qualification_type,
                    c.nqf_level,
                    c.credits,
                    c.assessment_type,
                    c.sdp_code,
                    c.aqp_name,

                    sa.account_status,
                    sa.created_at AS student_account_created_at

                FROM public.applications a

                LEFT JOIN LATERAL (
                    SELECT rr.*
                    FROM public.registrations rr
                    WHERE rr.student_number = a.student_number
                    ORDER BY rr.created_at DESC NULLS LAST
                    LIMIT 1
                ) r ON TRUE

                LEFT JOIN public.courses c
                    ON c.course_code = r.course_code

                LEFT JOIN public.student_accounts sa
                    ON sa.student_number = a.student_number

                WHERE a.student_number = :student_number
                LIMIT 1
                """
            ),
            {"student_number": student_number},
        ).mappings().first()

    return dict(row) if row else None


def get_student_document_inventory(
    student_number: str,
) -> dict:
    student_number = str(student_number or "").strip()

    if not student_number:
        raise ValueError("Student number is required.")

    preferred_columns = [
        "id",
        "student_number",
        "document_type",
        "document_name",
        "document_code",
        "file_name",
        "filename",
        "mime_type",
        "status",
        "verification_status",
        "file_path",
        "storage_path",
        "uploaded_at",
        "created_at",
        "updated_at",
    ]

    with engine.connect() as connection:
        tables = connection.execute(
            text(
                """
                SELECT DISTINCT c.table_name
                FROM information_schema.columns c
                WHERE c.table_schema = 'public'
                  AND c.column_name = 'student_number'
                  AND (
                        c.table_name ILIKE '%document%'
                        OR c.table_name ILIKE '%file%'
                  )
                ORDER BY c.table_name
                """
            )
        ).scalars().all()

        records: list[dict] = []

        for table_name in tables:
            column_rows = connection.execute(
                text(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                    ORDER BY ordinal_position
                    """
                ),
                {"table_name": table_name},
            ).scalars().all()

            selected = [
                name
                for name in preferred_columns
                if name in set(column_rows)
            ]

            if "student_number" not in selected:
                selected.insert(0, "student_number")

            quoted_table = '"' + table_name.replace('"', '""') + '"'
            select_sql = ", ".join(
                '"' + name.replace('"', '""') + '"'
                for name in selected
            )

            rows = connection.execute(
                text(
                    f"""
                    SELECT {select_sql}
                    FROM public.{quoted_table}
                    WHERE student_number = :student_number
                    LIMIT 100
                    """
                ),
                {"student_number": student_number},
            ).mappings().all()

            records.append(
                {
                    "source_table": table_name,
                    "count": len(rows),
                    "documents": [dict(row) for row in rows],
                }
            )

    return {
        "student_number": student_number,
        "sources": records,
        "total_documents": sum(
            item["count"] for item in records
        ),
    }

