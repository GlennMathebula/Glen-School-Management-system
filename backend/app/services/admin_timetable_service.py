from __future__ import annotations

from datetime import date

from sqlalchemy import text

from app.database import engine


ALLOWED_SESSION_STATUSES = {
    "Draft",
    "Published",
    "Cancelled",
}


def list_admin_timetable(
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    class_code: str | None = None,
    course_code: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))

    filters: list[str] = []
    params: dict = {"limit": limit, "offset": offset}

    if date_from:
        filters.append("ts.session_date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        filters.append("ts.session_date <= :date_to")
        params["date_to"] = date_to

    if class_code:
        filters.append("c.class_code = :class_code")
        params["class_code"] = class_code.strip()

    if course_code:
        filters.append("c.course_code = :course_code")
        params["course_code"] = course_code.strip()

    if status:
        status = status.strip()
        if status not in ALLOWED_SESSION_STATUSES:
            raise ValueError("Invalid timetable session status.")
        filters.append("ts.status = :status")
        params["status"] = status

    where_sql = ""
    if filters:
        where_sql = "WHERE " + "\nAND ".join(filters)

    with engine.connect() as connection:
        total = connection.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM public.timetable_sessions ts
                JOIN public.classes c
                    ON c.id = ts.class_id
                {where_sql}
                """
            ),
            params,
        ).scalar_one()

        rows = connection.execute(
            text(
                f"""
                SELECT
                    ts.id AS timetable_session_id,
                    ts.session_title,
                    ts.session_date,
                    ts.start_time,
                    ts.end_time,
                    ts.delivery_mode,
                    ts.venue,
                    ts.meeting_link,
                    ts.notes,
                    ts.status,
                    ts.published_at,
                    ts.cancelled_at,

                    c.id AS class_id,
                    c.class_code,
                    c.class_name,
                    c.course_code,
                    c.cycle_code,
                    c.class_group,
                    c.facilitator_code,
                    c.assessor_code,

                    m.module_code,
                    m.module_name,
                    m.module_type

                FROM public.timetable_sessions ts

                JOIN public.classes c
                    ON c.id = ts.class_id

                LEFT JOIN public.modules m
                    ON m.id = ts.module_id

                {where_sql}

                ORDER BY
                    ts.session_date,
                    ts.start_time,
                    c.class_code

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
        "sessions": [dict(row) for row in rows],
    }


def update_timetable_session_status(
    *,
    timetable_session_id: str,
    new_status: str,
) -> dict:
    timetable_session_id = str(
        timetable_session_id or ""
    ).strip()
    new_status = str(new_status or "").strip()

    if new_status not in ALLOWED_SESSION_STATUSES:
        raise ValueError(
            "Status must be Draft, Published or Cancelled."
        )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.timetable_sessions
                SET
                    status = :new_status,
                    published_at = CASE
                        WHEN :new_status = 'Published'
                        THEN COALESCE(published_at, NOW())
                        ELSE published_at
                    END,
                    cancelled_at = CASE
                        WHEN :new_status = 'Cancelled'
                        THEN COALESCE(cancelled_at, NOW())
                        ELSE cancelled_at
                    END
                WHERE id = CAST(
                    :timetable_session_id
                    AS uuid
                )
                RETURNING *
                """
            ),
            {
                "timetable_session_id": timetable_session_id,
                "new_status": new_status,
            },
        ).mappings().first()

    if not row:
        raise ValueError("Timetable session not found.")

    return dict(row)

