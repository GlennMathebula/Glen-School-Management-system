from sqlalchemy import text

from app.database import engine
from app.services.attendance_service import (
    get_attendance_roster,
    render_attendance,
    return_attendance,
)
from app.services.staff_audit_service import (
    create_staff_audit_log,
)


ALLOWED_REVIEW_STATUSES = {
    "Draft",
    "Submitted",
    "Returned",
    "Rendered",
}


def _clean_limit(value) -> int:
    try:
        value = int(value)
    except (TypeError, ValueError):
        value = 200
    return max(1, min(value, 500))


def _write_audit(
    *,
    actor_staff_code: str,
    action_code: str,
    attendance_session_id: str,
    description: str,
    metadata: dict | None = None,
):
    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code=action_code,
            module_code="ATTENDANCE",
            entity_type="ATTENDANCE_SESSION",
            entity_id=attendance_session_id,
            description=description,
            before_data=None,
            after_data=None,
            metadata=metadata or {},
        )
    except Exception as error:
        print(
            "WARNING: Attendance review action succeeded but audit "
            f"logging failed: {error}"
        )


def _attendance_summary_query(
    *,
    attendance_session_id: str | None = None,
    status: str | None = None,
    limit: int = 200,
):
    filters = []
    params = {"limit": _clean_limit(limit)}

    if attendance_session_id:
        filters.append(
            "ats.id = CAST(:attendance_session_id AS uuid)"
        )
        params["attendance_session_id"] = str(
            attendance_session_id
        ).strip()

    if status:
        status = str(status).strip().title()
        if status not in ALLOWED_REVIEW_STATUSES:
            raise ValueError("Invalid attendance status.")
        filters.append("ats.status = :status")
        params["status"] = status

    where_sql = (
        "WHERE " + " AND ".join(filters)
        if filters
        else ""
    )

    return (
        text(
            f"""
            SELECT
                ats.id AS attendance_session_id,
                ats.status,
                ats.captured_by,
                ats.submitted_at,
                ats.rendered_by,
                ats.rendered_at,
                ats.return_reason,
                ts.id AS timetable_session_id,
                ts.session_date,
                ts.start_time,
                ts.end_time,
                ts.session_title,
                ts.venue,
                cl.id AS class_id,
                cl.class_code,
                cl.class_name,
                cl.class_group,
                cl.course_code,
                cl.cycle_code,
                c.course_name,
                m.module_code,
                m.module_name,
                CONCAT_WS(
                    ' ',
                    e.first_name,
                    e.middle_name,
                    e.last_name
                ) AS submitted_by_name,
                COUNT(ar.id) AS learner_count,
                COUNT(ar.id) FILTER (
                    WHERE ar.attendance_status = 'Present'
                ) AS present_count,
                COUNT(ar.id) FILTER (
                    WHERE ar.attendance_status = 'Absent'
                ) AS absent_count,
                COUNT(ar.id) FILTER (
                    WHERE ar.attendance_status = 'Late'
                ) AS late_count,
                COUNT(ar.id) FILTER (
                    WHERE ar.attendance_status = 'Excused'
                ) AS excused_count
            FROM public.attendance_sessions ats
            JOIN public.timetable_sessions ts
                ON ts.id = ats.timetable_session_id
            JOIN public.classes cl
                ON cl.id = ts.class_id
            LEFT JOIN public.courses c
                ON c.course_code = cl.course_code
            LEFT JOIN public.modules m
                ON m.id = ts.module_id
            LEFT JOIN public.staff_accounts sa
                ON sa.staff_code = ats.captured_by
            LEFT JOIN public.employees e
                ON e.id = sa.employee_id
            LEFT JOIN public.attendance_records ar
                ON ar.attendance_session_id = ats.id
            {where_sql}
            GROUP BY
                ats.id,
                ts.id,
                cl.id,
                c.course_name,
                m.module_code,
                m.module_name,
                e.first_name,
                e.middle_name,
                e.last_name
            ORDER BY
                ats.submitted_at DESC NULLS LAST,
                ts.session_date DESC,
                cl.class_code
            LIMIT :limit
            """
        ),
        params,
    )


def list_attendance_reviews(
    *,
    status: str | None = "Submitted",
    limit: int = 200,
) -> list[dict]:
    statement, params = _attendance_summary_query(
        status=status,
        limit=limit,
    )
    with engine.connect() as connection:
        rows = connection.execute(
            statement,
            params,
        ).mappings().all()
    return [dict(row) for row in rows]


def get_attendance_review(
    attendance_session_id: str,
) -> dict:
    statement, params = _attendance_summary_query(
        attendance_session_id=attendance_session_id,
        status=None,
        limit=1,
    )
    with engine.connect() as connection:
        row = connection.execute(
            statement,
            params,
        ).mappings().first()
    if not row:
        raise ValueError("Attendance session was not found.")
    roster = get_attendance_roster(attendance_session_id)
    return {
        "attendance": dict(row),
        "students": roster["students"],
    }


def confirm_attendance_review(
    *,
    attendance_session_id: str,
    confirmed_by: str,
) -> dict:
    before = get_attendance_review(attendance_session_id)
    if before["attendance"]["status"] != "Submitted":
        raise ValueError(
            "Only Submitted attendance can be confirmed."
        )
    render_attendance(
        attendance_session_id=attendance_session_id,
        rendered_by=confirmed_by,
    )
    _write_audit(
        actor_staff_code=confirmed_by,
        action_code="ATTENDANCE_CONFIRMED",
        attendance_session_id=attendance_session_id,
        description="Submitted attendance was confirmed by Admin.",
        metadata={
            "submitted_by": before["attendance"]["captured_by"],
        },
    )
    return get_attendance_review(attendance_session_id)


def return_attendance_review(
    *,
    attendance_session_id: str,
    returned_by: str,
    reason: str,
) -> dict:
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("A return reason is required.")
    before = get_attendance_review(attendance_session_id)
    if before["attendance"]["status"] != "Submitted":
        raise ValueError(
            "Only Submitted attendance can be returned."
        )
    return_attendance(
        attendance_session_id=attendance_session_id,
        returned_by=returned_by,
        reason=reason,
    )
    _write_audit(
        actor_staff_code=returned_by,
        action_code="ATTENDANCE_RETURNED",
        attendance_session_id=attendance_session_id,
        description="Submitted attendance was returned for correction.",
        metadata={
            "reason": reason,
            "submitted_by": before["attendance"]["captured_by"],
        },
    )
    return get_attendance_review(attendance_session_id)
