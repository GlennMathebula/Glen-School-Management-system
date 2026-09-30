from __future__ import annotations

from sqlalchemy import text

from app.database import engine


def _fisa_competent(row: dict) -> bool:
    if row.get("fisa_status") != "Published":
        return False

    result = str(row.get("fisa_result") or "").strip().upper()
    if result in {"C", "COMPETENT", "PASSED", "PASS"}:
        return True

    mark = row.get("fisa_mark")
    pass_mark = row.get("fisa_pass_mark")

    if mark is None or pass_mark is None:
        return False

    try:
        return float(mark) >= float(pass_mark)
    except (TypeError, ValueError):
        return False


def list_eisa_learners(
    *,
    eligible: bool | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    filters = ["c.assessment_type = 'FISA_PLUS_EISA'"]
    params: dict = {"limit": limit, "offset": offset}

    if eligible is not None:
        filters.append(
            "COALESCE(r.eisa_eligible, FALSE) = :eligible"
        )
        params["eligible"] = bool(eligible)

    if search:
        filters.append(
            "("
            "r.student_number ILIKE :search "
            "OR a.first_name ILIKE :search "
            "OR a.last_name ILIKE :search "
            "OR c.course_name ILIKE :search"
            ")"
        )
        params["search"] = f"%{search.strip()}%"

    where_sql = "WHERE " + "\nAND ".join(filters)

    query = f"""
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.registration_status,
            r.course_code,
            r.cycle,
            r.eisa_eligible,

            a.first_name,
            a.middle_name,
            a.last_name,
            a.email,
            a.cell_number,

            c.course_name,
            c.nqf_level,
            c.credits,
            c.assessment_type,
            c.aqp_name,
            c.fisa_pass_mark,

            fisa.id AS fisa_id,
            fisa.mark AS fisa_mark,
            fisa.result AS fisa_result,
            fisa.status AS fisa_status,
            fisa.assessment_date AS fisa_date

        FROM public.registrations r

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        LEFT JOIN LATERAL (
            SELECT sa.*
            FROM public.summative_assessments sa
            WHERE sa.registration_id = r.id
              AND sa.assessment_type = 'FISA'
            ORDER BY
                sa.attempt_number DESC NULLS LAST,
                sa.updated_at DESC NULLS LAST,
                sa.created_at DESC NULLS LAST
            LIMIT 1
        ) fisa ON TRUE

        {where_sql}

        ORDER BY
            a.last_name,
            a.first_name,
            r.student_number

        LIMIT :limit
        OFFSET :offset
    """

    count_query = f"""
        SELECT COUNT(*)
        FROM public.registrations r
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        {where_sql}
    """

    with engine.connect() as connection:
        total = connection.execute(
            text(count_query),
            params,
        ).scalar_one()

        rows = connection.execute(
            text(query),
            params,
        ).mappings().all()

    learners = []
    for row in rows:
        item = dict(row)
        item["fisa_competent"] = _fisa_competent(item)
        item["ready_for_eisa_admin"] = bool(
            item["fisa_competent"]
            and item.get("registration_status")
            in {"Active", "Registered", "Completed"}
        )
        learners.append(item)

    return {
        "count": len(learners),
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "learners": learners,
    }


def set_eisa_eligibility(
    *,
    student_number: str,
    eligible: bool,
) -> dict:
    student_number = str(student_number or "").strip()

    with engine.begin() as connection:
        course = connection.execute(
            text(
                """
                SELECT
                    r.id AS registration_id,
                    c.assessment_type
                FROM public.registrations r
                JOIN public.courses c
                    ON c.course_code = r.course_code
                WHERE r.student_number = :student_number
                ORDER BY r.created_at DESC NULLS LAST
                LIMIT 1
                """
            ),
            {"student_number": student_number},
        ).mappings().first()

        if not course:
            raise ValueError("Registration not found.")

        if course["assessment_type"] != "FISA_PLUS_EISA":
            raise ValueError(
                "This qualification does not use "
                "the FISA + EISA pathway."
            )

        row = connection.execute(
            text(
                """
                UPDATE public.registrations
                SET
                    eisa_eligible = :eligible,
                    updated_at = NOW()
                WHERE id = :registration_id
                RETURNING
                    id AS registration_id,
                    student_number,
                    course_code,
                    registration_status,
                    eisa_eligible,
                    updated_at
                """
            ),
            {
                "eligible": bool(eligible),
                "registration_id": course["registration_id"],
            },
        ).mappings().first()

    return dict(row)

