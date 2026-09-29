from sqlalchemy import text

from app.database import engine


# ============================================================
# GET FACILITATOR ATTENDANCE HISTORY
# ============================================================

def get_facilitator_attendance_history(
    staff_code: str,
) -> list[dict]:

    query = text(
        """
        SELECT
            ats.id AS attendance_session_id,
            ats.status,
            ats.captured_by,
            ats.submitted_at,
            ats.rendered_by,
            ats.rendered_at,
            ats.return_reason,
            ats.created_at,
            ats.updated_at,

            ts.id AS timetable_session_id,
            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,
            ts.delivery_mode,
            ts.venue,

            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,

            COUNT(
                ar.id
            ) AS learner_records,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Present'
            ) AS present_count,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Absent'
            ) AS absent_count,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Late'
            ) AS late_count,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Excused'
            ) AS excused_count

        FROM public.attendance_sessions ats

        JOIN public.timetable_sessions ts
            ON ts.id =
                ats.timetable_session_id

        JOIN public.classes c
            ON c.id = ts.class_id

        LEFT JOIN public.attendance_records ar
            ON ar.attendance_session_id =
                ats.id

        WHERE
            (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

        GROUP BY
            ats.id,
            ats.status,
            ats.captured_by,
            ats.submitted_at,
            ats.rendered_by,
            ats.rendered_at,
            ats.return_reason,
            ats.created_at,
            ats.updated_at,

            ts.id,
            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,
            ts.delivery_mode,
            ts.venue,

            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group

        ORDER BY
            ts.session_date DESC,
            ts.start_time DESC
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "staff_code": (
                    staff_code
                ),
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# GET CLASS ATTENDANCE HISTORY
# ============================================================

def get_facilitator_class_attendance_history(
    *,
    staff_code: str,
    class_code: str,
) -> list[dict] | None:

    ownership_query = text(
        """
        SELECT
            id

        FROM public.classes

        WHERE
            class_code = :class_code

            AND (
                facilitator_code = :staff_code
                OR assessor_code = :staff_code
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        class_row = connection.execute(
            ownership_query,
            {
                "class_code": (
                    class_code
                ),
                "staff_code": (
                    staff_code
                ),
            },
        ).mappings().first()

    if not class_row:

        return None

    history_query = text(
        """
        SELECT
            ats.id AS attendance_session_id,
            ats.status,
            ats.captured_by,
            ats.submitted_at,
            ats.rendered_by,
            ats.rendered_at,
            ats.return_reason,

            ts.id AS timetable_session_id,
            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,
            ts.delivery_mode,
            ts.venue,

            COUNT(
                ar.id
            ) AS learner_records,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Present'
            ) AS present_count,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Absent'
            ) AS absent_count,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Late'
            ) AS late_count,

            COUNT(
                ar.id
            ) FILTER (
                WHERE ar.attendance_status =
                    'Excused'
            ) AS excused_count

        FROM public.attendance_sessions ats

        JOIN public.timetable_sessions ts
            ON ts.id =
                ats.timetable_session_id

        LEFT JOIN public.attendance_records ar
            ON ar.attendance_session_id =
                ats.id

        WHERE
            ts.class_id = :class_id

        GROUP BY
            ats.id,
            ats.status,
            ats.captured_by,
            ats.submitted_at,
            ats.rendered_by,
            ats.rendered_at,
            ats.return_reason,

            ts.id,
            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,
            ts.delivery_mode,
            ts.venue

        ORDER BY
            ts.session_date DESC,
            ts.start_time DESC
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            history_query,
            {
                "class_id": (
                    class_row[
                        "id"
                    ]
                ),
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]