from uuid import UUID

from sqlalchemy import text

from app.database import engine
from app.services.academic_calendar_service import (
    require_training_day,
)

# ============================================================
# UUID VALIDATION
# ============================================================

def validate_uuid(
    value: str,
    label: str,
) -> str:

    try:

        return str(
            UUID(
                value
            )
        )

    except ValueError as error:

        raise ValueError(
            f"Invalid {label}."
        ) from error


# ============================================================
# GET TIMETABLE SESSION
# ============================================================

def get_timetable_session(
    timetable_session_id: str,
) -> dict | None:

    timetable_session_id = (
        validate_uuid(
            timetable_session_id,
            "timetable session ID",
        )
    )

    query = text(
        """
        SELECT
            ts.id,
            ts.class_id,
            ts.module_id,

            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,

            ts.delivery_mode,
            ts.venue,
            ts.meeting_link,

            ts.status,

            cl.class_code,
            cl.class_name,
            cl.course_code,
            cl.class_group,
            cl.facilitator_code,
            cl.assessor_code

        FROM public.timetable_sessions ts

        JOIN public.classes cl
            ON cl.id = ts.class_id

        WHERE
            ts.id = CAST(
                :timetable_session_id
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "timetable_session_id": (
                    timetable_session_id
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# GET ATTENDANCE SESSION
# ============================================================

def get_attendance_session(
    attendance_session_id: str,
) -> dict | None:

    attendance_session_id = (
        validate_uuid(
            attendance_session_id,
            "attendance session ID",
        )
    )

    query = text(
        """
        SELECT
            ats.id,
            ats.timetable_session_id,
            ats.status,
            ats.captured_by,
            ats.submitted_at,
            ats.rendered_by,
            ats.rendered_at,
            ats.return_reason,
            ats.created_at,
            ats.updated_at,

            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,

            cl.class_code,
            cl.class_name,
            cl.course_code,
            cl.class_group

        FROM public.attendance_sessions ats

        JOIN public.timetable_sessions ts
            ON ts.id = ats.timetable_session_id

        JOIN public.classes cl
            ON cl.id = ts.class_id

        WHERE
            ats.id = CAST(
                :attendance_session_id
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# GET CLASS STUDENTS
# ============================================================

def get_class_students(
    class_id: str,
) -> list[dict]:

    class_id = validate_uuid(
        class_id,
        "class ID",
    )

    query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.registration_status,

            a.first_name,
            a.middle_name,
            a.last_name

        FROM public.class_enrolments ce

        JOIN public.registrations r
            ON r.id = ce.registration_id

        JOIN public.applications a
            ON a.id = r.application_id

        WHERE
            ce.class_id = CAST(
                :class_id
                AS uuid
            )

            AND ce.status = 'Active'

        ORDER BY
            a.last_name,
            a.first_name,
            r.student_number
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "class_id": class_id,
            },
        ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# CREATE ATTENDANCE SESSION
# ============================================================

def create_attendance_session(
    timetable_session_id: str,
    captured_by: str,
) -> dict:

    timetable_session_id = (
        validate_uuid(
            timetable_session_id,
            "timetable session ID",
        )
    )

    captured_by = (
        captured_by
        .strip()
    )

    if not captured_by:

        raise ValueError(
            "Captured by is required."
        )

    timetable_session = (
        get_timetable_session(
            timetable_session_id
        )
    )

    if not timetable_session:

        raise ValueError(
            "Timetable session not found."
        )

    if (
        timetable_session[
            "status"
        ]
        != "Published"
    ):

        raise ValueError(
            "Attendance can only be created "
            "for a published timetable session."
        )

    require_training_day(
        timetable_session[
            "session_date"
        ]
    )

    with engine.begin() as connection:

        existing = (
            connection.execute(
                text(
                    """
                    SELECT
                        id

                    FROM public.attendance_sessions

                    WHERE
                        timetable_session_id
                        = CAST(
                            :timetable_session_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "timetable_session_id": (
                        timetable_session_id
                    ),
                },
            )
            .mappings()
            .first()
        )

        if existing:

            attendance_session_id = (
                existing[
                    "id"
                ]
            )

        else:

            row = (
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            public.attendance_sessions
                        (
                            timetable_session_id,
                            status,
                            captured_by
                        )

                        VALUES
                        (
                            CAST(
                                :timetable_session_id
                                AS uuid
                            ),

                            'Draft',

                            :captured_by
                        )

                        RETURNING
                            id
                        """
                    ),
                    {
                        "timetable_session_id": (
                            timetable_session_id
                        ),

                        "captured_by": (
                            captured_by
                        ),
                    },
                )
                .mappings()
                .one()
            )

            attendance_session_id = (
                row[
                    "id"
                ]
            )

    result = get_attendance_session(
        str(
            attendance_session_id
        )
    )

    if not result:

        raise RuntimeError(
            "Attendance session was created "
            "but could not be retrieved."
        )

    return result


# ============================================================
# GET ATTENDANCE ROSTER
# ============================================================

def get_attendance_roster(
    attendance_session_id: str,
) -> dict:

    attendance_session = (
        get_attendance_session(
            attendance_session_id
        )
    )

    if not attendance_session:

        raise ValueError(
            "Attendance session not found."
        )

    timetable_session = (
        get_timetable_session(
            str(
                attendance_session[
                    "timetable_session_id"
                ]
            )
        )
    )

    if not timetable_session:

        raise ValueError(
            "Timetable session not found."
        )

    students = get_class_students(
        str(
            timetable_session[
                "class_id"
            ]
        )
    )

    existing_query = text(
        """
        SELECT
            ar.registration_id,
            ar.attendance_status,
            ar.minutes_late,
            ar.notes

        FROM public.attendance_records ar

        WHERE
            ar.attendance_session_id
            = CAST(
                :attendance_session_id
                AS uuid
            )
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            existing_query,
            {
                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        ).mappings().all()

    existing_records = {
        str(
            row[
                "registration_id"
            ]
        ): dict(row)
        for row in rows
    }

    roster = []

    for student in students:

        registration_id = str(
            student[
                "registration_id"
            ]
        )

        existing = (
            existing_records.get(
                registration_id
            )
        )

        roster.append(
            {
                "registration_id": (
                    registration_id
                ),

                "student_number": (
                    student[
                        "student_number"
                    ]
                ),

                "first_name": (
                    student[
                        "first_name"
                    ]
                ),

                "middle_name": (
                    student[
                        "middle_name"
                    ]
                ),

                "last_name": (
                    student[
                        "last_name"
                    ]
                ),

                "attendance_status": (
                    existing[
                        "attendance_status"
                    ]
                    if existing
                    else None
                ),

                "minutes_late": (
                    existing[
                        "minutes_late"
                    ]
                    if existing
                    else None
                ),

                "notes": (
                    existing[
                        "notes"
                    ]
                    if existing
                    else None
                ),
            }
        )

    return {
        "attendance_session": (
            attendance_session
        ),

        "students": (
            roster
        ),
    }


# ============================================================
# CAPTURE BULK ATTENDANCE
# ============================================================

def capture_attendance(
    attendance_session_id: str,
    captured_by: str,
    records: list[dict],
) -> dict:

    attendance_session_id = (
        validate_uuid(
            attendance_session_id,
            "attendance session ID",
        )
    )

    attendance_session = (
        get_attendance_session(
            attendance_session_id
        )
    )

    if not attendance_session:

        raise ValueError(
            "Attendance session not found."
        )

    if attendance_session[
        "status"
    ] not in {
        "Draft",
        "Returned",
    }:

        raise ValueError(
            "Attendance can only be edited "
            "while Draft or Returned."
        )

    allowed_statuses = {
        "Present",
        "Absent",
        "Late",
        "Excused",
    }

    with engine.begin() as connection:

        for record in records:

            registration_id = (
                validate_uuid(
                    record[
                        "registration_id"
                    ],
                    "registration ID",
                )
            )

            attendance_status = (
                record[
                    "attendance_status"
                ]
            )

            if (
                attendance_status
                not in allowed_statuses
            ):

                raise ValueError(
                    "Invalid attendance status."
                )

            minutes_late = (
                record.get(
                    "minutes_late"
                )
            )

            if (
                attendance_status
                != "Late"
            ):

                minutes_late = None

            if (
                attendance_status
                == "Late"
                and minutes_late is None
            ):

                minutes_late = 0

            # Verify learner belongs to this class.

            valid_student = (
                connection.execute(
                    text(
                        """
                        SELECT
                            ce.id

                        FROM public.class_enrolments ce

                        JOIN public.attendance_sessions ats
                            ON ats.id = CAST(
                                :attendance_session_id
                                AS uuid
                            )

                        JOIN public.timetable_sessions ts
                            ON ts.id
                            = ats.timetable_session_id

                        WHERE
                            ce.class_id = ts.class_id

                            AND ce.registration_id
                                = CAST(
                                    :registration_id
                                    AS uuid
                                )

                            AND ce.status = 'Active'

                        LIMIT 1
                        """
                    ),
                    {
                        "attendance_session_id": (
                            attendance_session_id
                        ),

                        "registration_id": (
                            registration_id
                        ),
                    },
                )
                .first()
            )

            if not valid_student:

                raise ValueError(
                    "One of the students does not "
                    "belong to this class."
                )

            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.attendance_records
                    (
                        attendance_session_id,
                        registration_id,

                        attendance_status,
                        minutes_late,
                        notes,

                        captured_by
                    )

                    VALUES
                    (
                        CAST(
                            :attendance_session_id
                            AS uuid
                        ),

                        CAST(
                            :registration_id
                            AS uuid
                        ),

                        :attendance_status,
                        :minutes_late,
                        :notes,

                        :captured_by
                    )

                    ON CONFLICT
                    (
                        attendance_session_id,
                        registration_id
                    )

                    DO UPDATE SET
                        attendance_status
                            = EXCLUDED.attendance_status,

                        minutes_late
                            = EXCLUDED.minutes_late,

                        notes
                            = EXCLUDED.notes,

                        captured_by
                            = EXCLUDED.captured_by,

                        updated_at
                            = now()
                    """
                ),
                {
                    "attendance_session_id": (
                        attendance_session_id
                    ),

                    "registration_id": (
                        registration_id
                    ),

                    "attendance_status": (
                        attendance_status
                    ),

                    "minutes_late": (
                        minutes_late
                    ),

                    "notes": (
                        record.get(
                            "notes"
                        )
                    ),

                    "captured_by": (
                        captured_by
                    ),
                },
            )

        connection.execute(
            text(
                """
                UPDATE
                    public.attendance_sessions

                SET
                    captured_by = :captured_by,
                    status = 'Draft',
                    return_reason = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :attendance_session_id
                        AS uuid
                    )
                """
            ),
            {
                "captured_by": (
                    captured_by
                ),

                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        )

    return get_attendance_roster(
        attendance_session_id
    )


# ============================================================
# SUBMIT ATTENDANCE
# ============================================================

def submit_attendance(
    attendance_session_id: str,
    submitted_by: str,
) -> dict:

    attendance_session_id = (
        validate_uuid(
            attendance_session_id,
            "attendance session ID",
        )
    )

    attendance_session = (
        get_attendance_session(
            attendance_session_id
        )
    )

    if not attendance_session:

        raise ValueError(
            "Attendance session not found."
        )

    if attendance_session[
        "status"
    ] not in {
        "Draft",
        "Returned",
    }:

        raise ValueError(
            "Only Draft or Returned attendance "
            "can be submitted."
        )

    roster = get_attendance_roster(
        attendance_session_id
    )

    students = roster[
        "students"
    ]

    if not students:

        raise ValueError(
            "This class has no active students."
        )

    incomplete = [
        student
        for student in students
        if not student[
            "attendance_status"
        ]
    ]

    if incomplete:

        raise ValueError(
            "Attendance must be captured for "
            "every active student before submission."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.attendance_sessions

                SET
                    status = 'Submitted',
                    captured_by = :submitted_by,
                    submitted_at = now(),
                    return_reason = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :attendance_session_id
                        AS uuid
                    )
                """
            ),
            {
                "submitted_by": (
                    submitted_by
                ),

                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        )

    result = get_attendance_session(
        attendance_session_id
    )

    if not result:

        raise RuntimeError(
            "Attendance submission failed."
        )

    return result


# ============================================================
# RENDER ATTENDANCE
# ============================================================

def render_attendance(
    attendance_session_id: str,
    rendered_by: str,
) -> dict:

    attendance_session_id = (
        validate_uuid(
            attendance_session_id,
            "attendance session ID",
        )
    )

    attendance_session = (
        get_attendance_session(
            attendance_session_id
        )
    )

    if not attendance_session:

        raise ValueError(
            "Attendance session not found."
        )

    if (
        attendance_session[
            "status"
        ]
        != "Submitted"
    ):

        raise ValueError(
            "Only Submitted attendance "
            "can be rendered."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.attendance_sessions

                SET
                    status = 'Rendered',
                    rendered_by = :rendered_by,
                    rendered_at = now(),
                    return_reason = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :attendance_session_id
                        AS uuid
                    )
                """
            ),
            {
                "rendered_by": (
                    rendered_by
                ),

                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        )

    result = get_attendance_session(
        attendance_session_id
    )

    if not result:

        raise RuntimeError(
            "Attendance rendering failed."
        )

    return result


# ============================================================
# RETURN ATTENDANCE
# ============================================================

def return_attendance(
    attendance_session_id: str,
    returned_by: str,
    reason: str,
) -> dict:

    attendance_session_id = (
        validate_uuid(
            attendance_session_id,
            "attendance session ID",
        )
    )

    reason = (
        reason
        .strip()
    )

    if not reason:

        raise ValueError(
            "Return reason is required."
        )

    attendance_session = (
        get_attendance_session(
            attendance_session_id
        )
    )

    if not attendance_session:

        raise ValueError(
            "Attendance session not found."
        )

    if (
        attendance_session[
            "status"
        ]
        != "Submitted"
    ):

        raise ValueError(
            "Only Submitted attendance "
            "can be returned."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.attendance_sessions

                SET
                    status = 'Returned',
                    rendered_by = :returned_by,
                    rendered_at = NULL,
                    return_reason = :reason,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :attendance_session_id
                        AS uuid
                    )
                """
            ),
            {
                "returned_by": (
                    returned_by
                ),

                "reason": (
                    reason
                ),

                "attendance_session_id": (
                    attendance_session_id
                ),
            },
        )

    result = get_attendance_session(
        attendance_session_id
    )

    if not result:

        raise RuntimeError(
            "Attendance return failed."
        )

    return result