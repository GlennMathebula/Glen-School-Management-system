from sqlalchemy import text

from app.database import engine


# ============================================================
# GET FACILITATOR CLASSES
# ============================================================

def get_facilitator_classes(
    staff_code: str,
) -> list[dict]:

    query = text(
        """
        SELECT
            c.id,
            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,
            c.facilitator_code,
            c.assessor_code,
            c.status,

            COUNT(
                DISTINCT ce.id
            ) FILTER (
                WHERE ce.status = 'Active'
            ) AS learner_count,

            COUNT(
                DISTINCT ts.id
            ) AS timetable_session_count

        FROM public.classes c

        LEFT JOIN public.class_enrolments ce
            ON ce.class_id = c.id

        LEFT JOIN public.timetable_sessions ts
            ON ts.class_id = c.id

        WHERE
            (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

        GROUP BY
            c.id,
            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,
            c.facilitator_code,
            c.assessor_code,
            c.status

        ORDER BY
            c.status,
            c.class_code
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
# GET ONE FACILITATOR CLASS
# ============================================================

def get_facilitator_class(
    *,
    staff_code: str,
    class_code: str,
) -> dict | None:

    query = text(
        """
        SELECT
            c.id,
            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,
            c.facilitator_code,
            c.assessor_code,
            c.status,
            c.created_at,
            c.updated_at,

            COUNT(
                DISTINCT ce.id
            ) FILTER (
                WHERE ce.status = 'Active'
            ) AS learner_count,

            COUNT(
                DISTINCT ts.id
            ) AS timetable_session_count

        FROM public.classes c

        LEFT JOIN public.class_enrolments ce
            ON ce.class_id = c.id

        LEFT JOIN public.timetable_sessions ts
            ON ts.class_id = c.id

        WHERE
            c.class_code = :class_code

            AND (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

        GROUP BY
            c.id,
            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,
            c.facilitator_code,
            c.assessor_code,
            c.status,
            c.created_at,
            c.updated_at

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "staff_code": (
                    staff_code
                ),

                "class_code": (
                    class_code
                ),
            },
        ).mappings().first()

    return (
        dict(
            row
        )
        if row
        else None
    )


# ============================================================
# GET FACILITATOR CLASS LEARNERS
# ============================================================

def get_facilitator_class_learners(
    *,
    staff_code: str,
    class_code: str,
) -> list[dict] | None:

    class_query = text(
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
            class_query,
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

    learner_query = text(
        """
        SELECT
            ce.id AS class_enrolment_id,
            ce.status AS class_enrolment_status,
            ce.enrolled_at,

            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.registration_status,
            r.cycle,

            a.first_name,
            a.middle_name,
            a.last_name,
            a.email,
            a.cell_number

        FROM public.class_enrolments ce

        JOIN public.registrations r
            ON r.id = ce.registration_id

        JOIN public.applications a
            ON a.student_number =
                r.student_number

        WHERE
            ce.class_id = :class_id

        ORDER BY
            a.last_name,
            a.first_name,
            r.student_number
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            learner_query,
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


# ============================================================
# GET FACILITATOR TIMETABLE
# ============================================================

def get_facilitator_timetable(
    staff_code: str,
) -> list[dict]:

    query = text(
        """
        SELECT
            ts.id AS timetable_session_id,

            c.class_code,
            c.class_name,
            c.course_code,
            c.cycle_code,
            c.class_group,

            m.module_code,
            m.module_name,
            m.module_type,

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
            ts.cancelled_at

        FROM public.timetable_sessions ts

        JOIN public.classes c
            ON c.id = ts.class_id

        LEFT JOIN public.modules m
            ON m.id = ts.module_id

        WHERE
            (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

            AND ts.status IN (
                'Published',
                'Cancelled'
            )

        ORDER BY
            ts.session_date,
            ts.start_time,
            c.class_code
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
# GET FACILITATOR CLASS TIMETABLE
# ============================================================

def get_facilitator_class_timetable(
    *,
    staff_code: str,
    class_code: str,
) -> list[dict] | None:

    class_query = text(
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
            class_query,
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

    timetable_query = text(
        """
        SELECT
            ts.id AS timetable_session_id,

            m.module_code,
            m.module_name,
            m.module_type,

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
            ts.cancelled_at

        FROM public.timetable_sessions ts

        LEFT JOIN public.modules m
            ON m.id = ts.module_id

        WHERE
            ts.class_id = :class_id

            AND ts.status IN (
                'Published',
                'Cancelled'
            )

        ORDER BY
            ts.session_date,
            ts.start_time
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            timetable_query,
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


# ============================================================
# VERIFY FACILITATOR OWNS TIMETABLE SESSION
# ============================================================

def facilitator_owns_timetable_session(
    *,
    staff_code: str,
    timetable_session_id: str,
) -> bool:

    query = text(
        """
        SELECT
            ts.id

        FROM public.timetable_sessions ts

        JOIN public.classes c
            ON c.id = ts.class_id

        WHERE
            ts.id = CAST(
                :timetable_session_id
                AS uuid
            )

            AND (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "staff_code": (
                    staff_code
                ),

                "timetable_session_id": (
                    timetable_session_id
                ),
            },
        ).first()

    return row is not None


# ============================================================
# VERIFY FACILITATOR OWNS ATTENDANCE SESSION
# ============================================================

def facilitator_owns_attendance_session(
    *,
    staff_code: str,
    attendance_session_id: str,
) -> bool:

    query = text(
        """
        SELECT
            ats.id

        FROM public.attendance_sessions ats

        JOIN public.timetable_sessions ts
            ON ts.id =
                ats.timetable_session_id

        JOIN public.classes c
            ON c.id = ts.class_id

        WHERE
            ats.id = CAST(
                :attendance_session_id
                AS uuid
            )

            AND (
                c.facilitator_code = :staff_code
                OR c.assessor_code = :staff_code
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "staff_code": (
                    staff_code
                ),

                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        ).first()

    return row is not None