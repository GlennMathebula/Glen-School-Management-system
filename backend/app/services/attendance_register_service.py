from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

from app.database import engine
from app.pdfs.attendance.attendance_register_pdf import (
    generate_attendance_register_pdf,
)
from app.services.academic_calendar_service import (
    ensure_calendar_year,
)

# ============================================================
# UUID VALIDATION
# ============================================================

def validate_class_id(
    class_id: str,
) -> str:

    try:

        return str(
            UUID(
                class_id
            )
        )

    except ValueError as error:

        raise ValueError(
            "Invalid class ID."
        ) from error


# ============================================================
# WEEK VALIDATION
# ============================================================

def get_monday(
    week_start: date,
) -> date:

    if week_start.weekday() != 0:

        raise ValueError(
            "week_start must be a Monday."
        )

    return week_start


# ============================================================
# CLASS INFORMATION
# ============================================================

def get_class_information(
    class_id: str,
) -> dict:

    class_id = validate_class_id(
        class_id
    )

    query = text(
        """
        SELECT
            cl.id AS class_id,
            cl.class_code,
            cl.class_name,
            cl.course_code,
            cl.cycle_code,
            cl.class_group,

            cl.facilitator_code,
            cl.assessor_code,

            c.course_name,
            c.qualification_type,
            c.nqf_level,
            c.credits,
            c.sdp_code

        FROM public.classes cl

        JOIN public.courses c
            ON c.course_code
            = cl.course_code

        WHERE
            cl.id = CAST(
                :class_id
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "class_id": class_id,
            },
        ).mappings().first()

    if not row:

        raise ValueError(
            "Class not found."
        )

    return dict(
        row
    )


# ============================================================
# CLASS LEARNERS
# ============================================================

def get_class_learners(
    class_id: str,
) -> list[dict]:

    class_id = validate_class_id(
        class_id
    )

    query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,

            a.national_id,
            a.alternate_id,
            a.alt_id_type,

            a.first_name,
            a.middle_name,
            a.last_name

        FROM public.class_enrolments ce

        JOIN public.registrations r
            ON r.id
            = ce.registration_id

        JOIN public.applications a
            ON a.id
            = r.application_id

        WHERE
            ce.class_id = CAST(
                :class_id
                AS uuid
            )

            AND ce.status = 'Active'

            AND r.registration_status
                IN (
                    'Registered',
                    'In Progress'
                )

        ORDER BY
            a.last_name,
            a.first_name,
            a.middle_name,
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
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# WEEK CALENDAR
# ============================================================

def get_week_calendar(
    week_start: date,
) -> list[dict]:

    monday = get_monday(
        week_start
    )

    ensure_calendar_year(
        monday.year
    )

    friday = (
        monday
        + timedelta(
            days=4
        )
    )

    if friday.year != monday.year:

        ensure_calendar_year(
            friday.year
        )

    query = text(
        """
        SELECT
            calendar_date,
            day_type,
            description,
            is_training_day,
            source,
            is_manual_override

        FROM
            public.academic_calendar_dates

        WHERE
            calendar_date
            BETWEEN :monday
            AND :friday

        ORDER BY
            calendar_date
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "monday": monday,
                "friday": friday,
            },
        ).mappings().all()

    calendar_by_date = {
        row[
            "calendar_date"
        ]: dict(row)
        for row in rows
    }

    days = []

    for offset in range(
        5
    ):

        current_date = (
            monday
            + timedelta(
                days=offset
            )
        )

        calendar_day = (
            calendar_by_date.get(
                current_date
            )
        )

        if calendar_day:

            days.append(
                {
                    "date": (
                        current_date
                    ),
                    "day_type": (
                        calendar_day[
                            "day_type"
                        ]
                    ),
                    "description": (
                        calendar_day[
                            "description"
                        ]
                    ),
                    "is_training_day": (
                        bool(
                            calendar_day[
                                "is_training_day"
                            ]
                        )
                    ),
                    "source": (
                        calendar_day[
                            "source"
                        ]
                    ),
                }
            )

        else:

            days.append(
                {
                    "date": (
                        current_date
                    ),
                    "day_type": (
                        "Training Day"
                    ),
                    "description": (
                        "Available training day"
                    ),
                    "is_training_day": (
                        True
                    ),
                    "source": (
                        "System"
                    ),
                }
            )

    return days


# ============================================================
# WEEK MODULES / VENUES
# ============================================================

def get_week_sessions(
    class_id: str,
    week_start: date,
) -> list[dict]:

    class_id = validate_class_id(
        class_id
    )

    monday = get_monday(
        week_start
    )

    friday = (
        monday
        + timedelta(
            days=4
        )
    )

    query = text(
        """
        SELECT
            ts.id,
            ts.session_title,
            ts.session_date,
            ts.start_time,
            ts.end_time,

            ts.delivery_mode,
            ts.venue,

            m.module_code,
            m.module_name,
            m.module_type

        FROM
            public.timetable_sessions ts

        LEFT JOIN
            public.modules m
            ON m.id
            = ts.module_id

        WHERE
            ts.class_id = CAST(
                :class_id
                AS uuid
            )

            AND ts.status = 'Published'

            AND ts.session_date
                BETWEEN :monday
                AND :friday

        ORDER BY
            ts.session_date,
            ts.start_time
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "class_id": class_id,
                "monday": monday,
                "friday": friday,
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# MODULE SUMMARY
# ============================================================

def build_modules_text(
    sessions: list[dict],
) -> str:

    modules = []

    seen = set()

    for session in sessions:

        module_code = (
            session.get(
                "module_code"
            )
        )

        module_name = (
            session.get(
                "module_name"
            )
        )

        if not module_code:

            continue

        key = (
            module_code,
            module_name,
        )

        if key in seen:

            continue

        seen.add(
            key
        )

        if module_name:

            modules.append(
                f"{module_code} - "
                f"{module_name}"
            )

        else:

            modules.append(
                module_code
            )

    if not modules:

        return "No published module sessions"

    return "; ".join(
        modules
    )


# ============================================================
# VENUE SUMMARY
# ============================================================

def build_venue_text(
    sessions: list[dict],
) -> str:

    venues = []

    seen = set()

    for session in sessions:

        venue = (
            session.get(
                "venue"
            )
        )

        if not venue:

            continue

        venue = (
            str(
                venue
            )
            .strip()
        )

        if not venue:

            continue

        if venue in seen:

            continue

        seen.add(
            venue
        )

        venues.append(
            venue
        )

    if not venues:

        return "As per timetable"

    return ", ".join(
        venues
    )


# ============================================================
# BUILD REGISTER DATA
# ============================================================

def build_attendance_register_data(
    class_id: str,
    week_start: date,
) -> dict:

    monday = get_monday(
        week_start
    )

    friday = (
        monday
        + timedelta(
            days=4
        )
    )

    class_info = (
        get_class_information(
            class_id
        )
    )

    students = (
        get_class_learners(
            class_id
        )
    )

    calendar_days = (
        get_week_calendar(
            monday
        )
    )

    sessions = (
        get_week_sessions(
            class_id,
            monday,
        )
    )

    return {
        "programme": {
            "course_code": (
                class_info[
                    "course_code"
                ]
            ),
            "course_name": (
                class_info[
                    "course_name"
                ]
            ),
            "qualification_type": (
                class_info[
                    "qualification_type"
                ]
            ),
            "nqf_level": (
                class_info[
                    "nqf_level"
                ]
            ),
            "credits": (
                class_info[
                    "credits"
                ]
            ),
            "sdp_code": (
                class_info[
                    "sdp_code"
                ]
            ),
        },

        "class": {
            "class_id": (
                str(
                    class_info[
                        "class_id"
                    ]
                )
            ),
            "class_code": (
                class_info[
                    "class_code"
                ]
            ),
            "class_name": (
                class_info[
                    "class_name"
                ]
            ),
            "cycle_code": (
                class_info[
                    "cycle_code"
                ]
            ),
            "class_group": (
                class_info[
                    "class_group"
                ]
            ),
            "facilitator_code": (
                class_info[
                    "facilitator_code"
                ]
            ),
            "assessor_code": (
                class_info[
                    "assessor_code"
                ]
            ),
        },

        "week": {
            "start_date": (
                monday
            ),
            "end_date": (
                friday
            ),
        },

        "week_days": (
            calendar_days
        ),

        "students": (
            students
        ),

        "sessions": (
            sessions
        ),

        "modules_text": (
            build_modules_text(
                sessions
            )
        ),

        "venue": (
            build_venue_text(
                sessions
            )
        ),
    }


# ============================================================
# GENERATE WEEKLY REGISTER
# ============================================================

def generate_weekly_attendance_register(
    class_id: str,
    week_start: date,
) -> Path:

    data = (
        build_attendance_register_data(
            class_id,
            week_start,
        )
    )

    output_directory = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "attendance"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    class_code = (
        data[
            "class"
        ][
            "class_code"
        ]
    )

    safe_class_code = (
        class_code
        .replace(
            "/",
            "-"
        )
        .replace(
            "\\",
            "-"
        )
        .replace(
            " ",
            "_"
        )
    )

    week_text = (
        week_start.strftime(
            "%Y-%m-%d"
        )
    )

    filename = (
        f"Attendance_Register_"
        f"{safe_class_code}_"
        f"{week_text}.pdf"
    )

    output_path = (
        output_directory
        / filename
    )

    return (
        generate_attendance_register_pdf(
            output_path,
            data,
        )
    )