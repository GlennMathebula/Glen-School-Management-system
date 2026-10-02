from __future__ import annotations

from sqlalchemy import text

from app.database import engine


COMPETENT_RESULTS = {
    "C",
    "COMPETENT",
    "PASS",
    "PASSED",
}


def _is_competent(
    result,
    mark,
    pass_mark,
    status,
) -> bool:
    if status != "Published":
        return False

    value = str(result or "").strip().upper()
    if value in COMPETENT_RESULTS:
        return True

    if mark is None or pass_mark is None:
        return False

    try:
        return float(mark) >= float(pass_mark)
    except (TypeError, ValueError):
        return False


def list_completion_status(
    *,
    search: str | None = None,
    course_code: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    filters = []
    params: dict = {"limit": limit, "offset": offset}

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

    if course_code:
        filters.append("r.course_code = :course_code")
        params["course_code"] = course_code.strip()

    where_sql = ""
    if filters:
        where_sql = "WHERE " + "\nAND ".join(filters)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT
                    r.id AS registration_id,
                    r.student_number,
                    r.course_code,
                    r.registration_status,
                    r.expected_completion_date,
                    r.eisa_eligible,

                    a.first_name,
                    a.middle_name,
                    a.last_name,

                    c.course_name,
                    c.assessment_type,
                    c.fisa_pass_mark,
                    c.aqp_name,

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
            ),
            params,
        ).mappings().all()

    items = []

    for row in rows:
        item = dict(row)
        fisa_competent = _is_competent(
            item.get("fisa_result"),
            item.get("fisa_mark"),
            item.get("fisa_pass_mark"),
            item.get("fisa_status"),
        )

        assessment_type = item.get("assessment_type")

        if (
            assessment_type == "FISA_ONLY"
            and fisa_competent
        ):
            state = "PROGRAMME_COMPLETE"
        elif assessment_type == "FISA_ONLY":
            state = "FISA_OUTSTANDING"
        elif (
            assessment_type == "FISA_PLUS_EISA"
            and item.get("eisa_eligible")
        ):
            state = "EISA_ADMISSION_READY"
        elif assessment_type == "FISA_PLUS_EISA":
            state = "EISA_NOT_YET_ELIGIBLE"
        else:
            state = "ASSESSMENT_PATHWAY_REVIEW"

        item["fisa_competent"] = fisa_competent
        item["completion_state"] = state
        item["final_completion_confirmed"] = (
            state == "PROGRAMME_COMPLETE"
        )

        if assessment_type == "FISA_PLUS_EISA":
            item["note"] = (
                "Final completion is not confirmed here. "
                "The external EISA outcome remains the final "
                "exit requirement."
            )

        items.append(item)

    return {
        "count": len(items),
        "limit": limit,
        "offset": offset,
        "records": items,
    }


def get_completion_record(
    student_number: str,
) -> dict | None:
    data = list_completion_status(
        search=student_number,
        limit=200,
        offset=0,
    )

    for record in data["records"]:
        if (
            record.get("student_number")
            == student_number
        ):
            return record

    return None



# ============================================================
# V3.8 DEFAULT PASS MARK FALLBACK
# ============================================================

from app.services.assessment_settings_service import (
    get_default_assessment_pass_mark as _v38_default_pass_mark,
)


def _is_competent(
    result,
    mark,
    pass_mark,
    status,
) -> bool:
    if status != "Published":
        return False

    value = str(result or "").strip().upper()

    if value in COMPETENT_RESULTS:
        return True

    if mark is None:
        return False

    if pass_mark is None:
        pass_mark = _v38_default_pass_mark()

    try:
        return float(mark) >= float(pass_mark)
    except (TypeError, ValueError):
        return False
