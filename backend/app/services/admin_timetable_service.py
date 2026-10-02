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
                    status = CAST(:new_status AS varchar),
                    published_at = CASE
                        WHEN CAST(:new_status AS varchar) = 'Published'
                        THEN COALESCE(published_at, NOW())
                        ELSE published_at
                    END,
                    cancelled_at = CASE
                        WHEN CAST(:new_status AS varchar) = 'Cancelled'
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




# ============================================================
# ADMIN TIMETABLE CRUD
# ============================================================

ALLOWED_DELIVERY_MODES = {"Physical", "Online", "Blended"}

def _resolve_class(connection, class_code: str) -> dict:
    class_code = str(class_code or "").strip()
    if not class_code:
        raise ValueError("Class code is required.")
    row = connection.execute(
        text("""
            SELECT id, class_code, class_name, course_code, cycle_code, status
            FROM public.classes
            WHERE class_code = :class_code
            LIMIT 1
        """),
        {"class_code": class_code},
    ).mappings().first()
    if not row:
        raise ValueError("Class was not found.")
    return dict(row)

def _resolve_module(connection, *, course_code: str, module_code: str | None):
    module_code = str(module_code or "").strip()
    if not module_code:
        return None
    row = connection.execute(
        text("""
            SELECT id, module_code, module_name, course_code
            FROM public.modules
            WHERE module_code = :module_code
              AND course_code = :course_code
            LIMIT 1
        """),
        {"module_code": module_code, "course_code": course_code},
    ).mappings().first()
    if not row:
        raise ValueError("Module was not found for the selected class course.")
    return dict(row)

def _validate_session_values(*, start_time, end_time, delivery_mode: str, status: str):
    if start_time is not None and end_time is not None and end_time <= start_time:
        raise ValueError("Session end time must be after start time.")
    if delivery_mode not in ALLOWED_DELIVERY_MODES:
        raise ValueError("Delivery mode must be Physical, Online or Blended.")
    if status not in ALLOWED_SESSION_STATUSES:
        raise ValueError("Status must be Draft, Published or Cancelled.")

def get_timetable_options() -> dict:
    with engine.connect() as connection:
        classes = connection.execute(
            text("""
                SELECT id, class_code, class_name, course_code, cycle_code, status
                FROM public.classes
                ORDER BY cycle_code, course_code, class_code
            """)
        ).mappings().all()
        modules = connection.execute(
            text("""
                SELECT id, course_code, module_code, module_name, module_type, status
                FROM public.modules
                ORDER BY course_code, module_type, module_code
            """)
        ).mappings().all()
    return {
        "classes": [dict(row) for row in classes],
        "modules": [dict(row) for row in modules],
        "delivery_modes": sorted(ALLOWED_DELIVERY_MODES),
        "statuses": ["Draft", "Published", "Cancelled"],
    }

def create_timetable_session(
    *,
    actor_staff_code: str,
    class_code: str,
    module_code: str | None,
    session_title: str | None,
    session_date,
    start_time,
    end_time,
    delivery_mode: str,
    venue: str | None,
    meeting_link: str | None,
    notes: str | None,
    status: str,
) -> dict:
    delivery_mode = str(delivery_mode or "Physical").strip().title()
    status = str(status or "Draft").strip().title()
    _validate_session_values(
        start_time=start_time,
        end_time=end_time,
        delivery_mode=delivery_mode,
        status=status,
    )
    with engine.begin() as connection:
        class_record = _resolve_class(connection, class_code)
        module_record = _resolve_module(
            connection,
            course_code=class_record["course_code"],
            module_code=module_code,
        )
        row = connection.execute(
            text("""
                INSERT INTO public.timetable_sessions (
                    class_id, module_id, session_title, session_date,
                    start_time, end_time, delivery_mode, venue,
                    meeting_link, notes, status, created_by,
                    published_at, cancelled_at, updated_at
                )
                VALUES (
                    CAST(:class_id AS uuid),
                    CASE WHEN :module_id IS NULL THEN NULL ELSE CAST(:module_id AS uuid) END,
                    :session_title, :session_date, :start_time, :end_time,
                    :delivery_mode, :venue, :meeting_link, :notes, :status,
                    :created_by,
                    CASE WHEN :status = 'Published' THEN NOW() ELSE NULL END,
                    CASE WHEN :status = 'Cancelled' THEN NOW() ELSE NULL END,
                    NOW()
                )
                RETURNING *
            """),
            {
                "class_id": str(class_record["id"]),
                "module_id": str(module_record["id"]) if module_record else None,
                "session_title": str(session_title or "").strip() or None,
                "session_date": session_date,
                "start_time": start_time,
                "end_time": end_time,
                "delivery_mode": delivery_mode,
                "venue": str(venue or "").strip() or None,
                "meeting_link": str(meeting_link or "").strip() or None,
                "notes": str(notes or "").strip() or None,
                "status": status,
                "created_by": actor_staff_code,
            },
        ).mappings().one()
    return dict(row)

def update_timetable_session(*, timetable_session_id: str, changes: dict) -> dict:
    timetable_session_id = str(timetable_session_id or "").strip()
    if not timetable_session_id:
        raise ValueError("Timetable session ID is required.")
    with engine.begin() as connection:
        current = connection.execute(
            text("""
                SELECT ts.*, c.class_code, c.course_code
                FROM public.timetable_sessions ts
                JOIN public.classes c ON c.id = ts.class_id
                WHERE ts.id = CAST(:session_id AS uuid)
                LIMIT 1
            """),
            {"session_id": timetable_session_id},
        ).mappings().first()
        if not current:
            raise ValueError("Timetable session was not found.")
        class_record = _resolve_class(
            connection,
            changes.get("class_code") or current["class_code"],
        )
        if "module_code" in changes:
            module_record = _resolve_module(
                connection,
                course_code=class_record["course_code"],
                module_code=changes.get("module_code"),
            )
            module_id = str(module_record["id"]) if module_record else None
        else:
            module_id = str(current["module_id"]) if current["module_id"] else None
        start_time = changes.get("start_time", current["start_time"])
        end_time = changes.get("end_time", current["end_time"])
        delivery_mode = str(
            changes.get("delivery_mode", current["delivery_mode"]) or "Physical"
        ).strip().title()
        status = str(current["status"] or "Draft").strip().title()
        _validate_session_values(
            start_time=start_time,
            end_time=end_time,
            delivery_mode=delivery_mode,
            status=status,
        )
        row = connection.execute(
            text("""
                UPDATE public.timetable_sessions
                SET
                    class_id = CAST(:class_id AS uuid),
                    module_id = CASE WHEN :module_id IS NULL THEN NULL ELSE CAST(:module_id AS uuid) END,
                    session_title = :session_title,
                    session_date = :session_date,
                    start_time = :start_time,
                    end_time = :end_time,
                    delivery_mode = :delivery_mode,
                    venue = :venue,
                    meeting_link = :meeting_link,
                    notes = :notes,
                    updated_at = NOW()
                WHERE id = CAST(:session_id AS uuid)
                RETURNING *
            """),
            {
                "class_id": str(class_record["id"]),
                "module_id": module_id,
                "session_title": changes.get("session_title", current["session_title"]),
                "session_date": changes.get("session_date", current["session_date"]),
                "start_time": start_time,
                "end_time": end_time,
                "delivery_mode": delivery_mode,
                "venue": changes.get("venue", current["venue"]),
                "meeting_link": changes.get("meeting_link", current["meeting_link"]),
                "notes": changes.get("notes", current["notes"]),
                "session_id": timetable_session_id,
            },
        ).mappings().one()
    return dict(row)

def delete_timetable_session(timetable_session_id: str) -> dict:
    timetable_session_id = str(timetable_session_id or "").strip()
    with engine.begin() as connection:
        current = connection.execute(
            text("""
                SELECT id, session_title, status
                FROM public.timetable_sessions
                WHERE id = CAST(:session_id AS uuid)
                LIMIT 1
            """),
            {"session_id": timetable_session_id},
        ).mappings().first()
        if not current:
            raise ValueError("Timetable session was not found.")
        if current["status"] != "Draft":
            raise ValueError(
                "Only Draft timetable sessions can be deleted. "
                "Published sessions should be Cancelled."
            )
        connection.execute(
            text("""
                DELETE FROM public.timetable_sessions
                WHERE id = CAST(:session_id AS uuid)
            """),
            {"session_id": timetable_session_id},
        )
    return dict(current)
