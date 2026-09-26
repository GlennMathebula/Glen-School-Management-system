from datetime import date, datetime, time

from sqlalchemy import text

from app.database import engine

# ============================================================
# COMBINE SESSION DATE + TIME
# ============================================================

def combine_session_datetime(
    session_date: date,
    session_time: time,
) -> datetime:

    return datetime.combine(
        session_date,
        session_time,
    )


# ============================================================
# FORMAT SESSION
# ============================================================

def format_timetable_session(
    row: dict,
) -> dict:

    session_date = row[
        "session_date"
    ]

    start_time = row[
        "start_time"
    ]

    end_time = row[
        "end_time"
    ]

    start_datetime = (
        combine_session_datetime(
            session_date,
            start_time,
        )
    )

    end_datetime = (
        combine_session_datetime(
            session_date,
            end_time,
        )
    )

    return {
        "session_id": str(
            row[
                "session_id"
            ]
        ),

        "class_id": str(
            row[
                "class_id"
            ]
        ),

        "class_code": (
            row[
                "class_code"
            ]
        ),

        "class_name": (
            row[
                "class_name"
            ]
        ),

        "class_group": (
            row[
                "class_group"
            ]
        ),

        "session_title": (
            row[
                "session_title"
            ]
        ),

        "session_date": (
            session_date
        ),

        "start_time": (
            start_time
        ),

        "end_time": (
            end_time
        ),

        "start_datetime": (
            start_datetime
        ),

        "end_datetime": (
            end_datetime
        ),

        "delivery_mode": (
            row[
                "delivery_mode"
            ]
        ),

        "venue": (
            row[
                "venue"
            ]
        ),

        "meeting_link": (
            row[
                "meeting_link"
            ]
        ),

        "notes": (
            row[
                "notes"
            ]
        ),

        "module": {
            "module_id": (
                str(
                    row[
                        "module_id"
                    ]
                )
                if row[
                    "module_id"
                ]
                else None
            ),

            "module_code": (
                row[
                    "module_code"
                ]
            ),

            "module_name": (
                row[
                    "module_name"
                ]
            ),

            "module_type": (
                row[
                    "module_type"
                ]
            ),
        },

        "facilitator_code": (
            row[
                "facilitator_code"
            ]
        ),

        "assessor_code": (
            row[
                "assessor_code"
            ]
        ),
    }


# ============================================================
# GET STUDENT TIMETABLE
# ============================================================

def get_student_timetable(
    student_number: str,
) -> dict | None:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # STUDENT REGISTRATION
    # --------------------------------------------------------

    registration_query = text(
        """
        SELECT
            r.id AS registration_id,

            r.student_number,
            r.course_code,
            r.registration_status,
            r.cycle,
            r.program_start_date,
            r.expected_completion_date,

            c.course_name,
            c.nqf_level,

            a.class_group

        FROM public.registrations r

        JOIN public.courses c
            ON c.course_code = r.course_code

        JOIN public.applications a
            ON a.id = r.application_id

        WHERE
            r.student_number = :student_number

        LIMIT 1
        """
    )

    # --------------------------------------------------------
    # CLASS ASSIGNMENTS
    # --------------------------------------------------------

    classes_query = text(
        """
        SELECT
            cl.id,
            cl.class_code,
            cl.class_name,
            cl.course_code,
            cl.cycle_code,
            cl.class_group,
            cl.facilitator_code,
            cl.assessor_code,
            cl.status,

            ce.status AS enrolment_status

        FROM public.class_enrolments ce

        JOIN public.classes cl
            ON cl.id = ce.class_id

        WHERE
            ce.registration_id = :registration_id

            AND ce.status = 'Active'

            AND cl.status = 'Active'

        ORDER BY
            cl.class_code
        """
    )

    # --------------------------------------------------------
    # PUBLISHED SESSIONS
    # --------------------------------------------------------

    sessions_query = text(
        """
        SELECT
            ts.id AS session_id,

            ts.class_id,
            ts.session_title,

            ts.session_date,
            ts.start_time,
            ts.end_time,

            ts.delivery_mode,
            ts.venue,
            ts.meeting_link,
            ts.notes,

            cl.class_code,
            cl.class_name,
            cl.class_group,

            cl.facilitator_code,
            cl.assessor_code,

            m.id AS module_id,
            m.module_code,
            m.module_name,
            m.module_type

        FROM public.timetable_sessions ts

        JOIN public.classes cl
            ON cl.id = ts.class_id

        LEFT JOIN public.modules m
            ON m.id = ts.module_id

        JOIN public.class_enrolments ce
            ON ce.class_id = cl.id

        WHERE
            ce.registration_id = :registration_id

            AND ce.status = 'Active'

            AND cl.status = 'Active'

            AND ts.status = 'Published'

        ORDER BY
            ts.session_date ASC,
            ts.start_time ASC
        """
    )

    with engine.connect() as connection:

        registration_row = (
            connection.execute(
                registration_query,
                {
                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not registration_row:

            return None

        registration = dict(
            registration_row
        )

        registration_id = (
            registration[
                "registration_id"
            ]
        )

        class_rows = (
            connection.execute(
                classes_query,
                {
                    "registration_id": (
                        registration_id
                    ),
                },
            )
            .mappings()
            .all()
        )

        session_rows = (
            connection.execute(
                sessions_query,
                {
                    "registration_id": (
                        registration_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    # --------------------------------------------------------
    # CLASS LIST
    # --------------------------------------------------------

    classes = []

    for row in class_rows:

        item = dict(
            row
        )

        classes.append(
            {
                "class_id": str(
                    item[
                        "id"
                    ]
                ),

                "class_code": (
                    item[
                        "class_code"
                    ]
                ),

                "class_name": (
                    item[
                        "class_name"
                    ]
                ),

                "course_code": (
                    item[
                        "course_code"
                    ]
                ),

                "cycle_code": (
                    item[
                        "cycle_code"
                    ]
                ),

                "class_group": (
                    item[
                        "class_group"
                    ]
                ),

                "facilitator_code": (
                    item[
                        "facilitator_code"
                    ]
                ),

                "assessor_code": (
                    item[
                        "assessor_code"
                    ]
                ),
            }
        )

    # --------------------------------------------------------
    # SESSION GROUPING
    # --------------------------------------------------------

    today = date.today()

    today_sessions = []
    upcoming_sessions = []
    past_sessions = []

    all_sessions = []

    for row in session_rows:

        session = (
            format_timetable_session(
                dict(
                    row
                )
            )
        )

        all_sessions.append(
            session
        )

        session_date = (
            session[
                "session_date"
            ]
        )

        if session_date == today:

            today_sessions.append(
                session
            )

        elif session_date > today:

            upcoming_sessions.append(
                session
            )

        else:

            past_sessions.append(
                session
            )

    # Past should show most recent first.

    past_sessions.reverse()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "student_number": (
            registration[
                "student_number"
            ]
        ),

        "programme": {
            "course_code": (
                registration[
                    "course_code"
                ]
            ),

            "course_name": (
                registration[
                    "course_name"
                ]
            ),

            "nqf_level": (
                registration[
                    "nqf_level"
                ]
            ),

            "registration_status": (
                registration[
                    "registration_status"
                ]
            ),

            "cycle": (
                registration[
                    "cycle"
                ]
            ),

            "program_start_date": (
                registration[
                    "program_start_date"
                ]
            ),

            "expected_completion_date": (
                registration[
                    "expected_completion_date"
                ]
            ),
        },

        "application_class_group": (
            registration[
                "class_group"
            ]
        ),

        "assigned_classes": (
            classes
        ),

        "summary": {
            "assigned_classes": (
                len(
                    classes
                )
            ),

            "published_sessions": (
                len(
                    all_sessions
                )
            ),

            "today_sessions": (
                len(
                    today_sessions
                )
            ),

            "upcoming_sessions": (
                len(
                    upcoming_sessions
                )
            ),

            "past_sessions": (
                len(
                    past_sessions
                )
            ),
        },

        "today": (
            today_sessions
        ),

        "upcoming": (
            upcoming_sessions
        ),

        "past": (
            past_sessions
        ),

        "all_sessions": (
            all_sessions
        ),
    }