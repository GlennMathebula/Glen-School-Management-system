from datetime import date, timedelta
from pathlib import Path
from uuid import UUID

from sqlalchemy import text

from app.database import engine
from app.pdfs.attendance.daily_attendance_register_pdf import (
    generate_daily_attendance_pack_pdf,
)
from app.services.academic_calendar_service import (
    ensure_calendar_year,
)

# ============================================================
# VALIDATE CLASS ID
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
# VALIDATE MONDAY
# ============================================================

def validate_week_start(
    week_start: date,
) -> date:

    if week_start.weekday() != 0:

        raise ValueError(
            "week_start must be a Monday."
        )

    return week_start


# ============================================================
# GET CLASS
# ============================================================

def get_class_data(
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
# GET STUDENTS
# ============================================================

def get_class_students(
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
# GET CALENDAR WEEK
# ============================================================

def get_week_days(
    week_start: date,
) -> list[dict]:

    monday = validate_week_start(
        week_start
    )

    friday = (
        monday
        + timedelta(
            days=4
        )
    )

    ensure_calendar_year(
        monday.year
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
            source

        FROM public.academic_calendar_dates

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

    by_date = {
        row[
            "calendar_date"
        ]: dict(
            row
        )
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
            by_date.get(
                current_date
            )
        )

        if calendar_day:

            days.append(
                {
                    "date": (
                        current_date
                    ),

                    "day_name": (
                        current_date.strftime(
                            "%A"
                        )
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
                }
            )

        else:

            days.append(
                {
                    "date": (
                        current_date
                    ),

                    "day_name": (
                        current_date.strftime(
                            "%A"
                        )
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
                }
            )

    return days


# ============================================================
# GET DAILY TIMETABLE DETAILS
# ============================================================

def get_daily_sessions(
    class_id: str,
    register_date: date,
) -> list[dict]:

    class_id = validate_class_id(
        class_id
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

        FROM public.timetable_sessions ts

        LEFT JOIN public.modules m
            ON m.id = ts.module_id

        WHERE
            ts.class_id = CAST(
                :class_id
                AS uuid
            )

            AND ts.session_date
                = :register_date

            AND ts.status = 'Published'

        ORDER BY
            ts.start_time
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "class_id": class_id,
                "register_date": (
                    register_date
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
# FORMAT DAILY MODULES
# ============================================================

def build_modules_text(
    sessions: list[dict],
) -> str:

    result = []

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

            result.append(
                f"{module_code} - "
                f"{module_name}"
            )

        else:

            result.append(
                module_code
            )

    if not result:

        return "As per timetable"

    return "; ".join(
        result
    )


# ============================================================
# FORMAT VENUE
# ============================================================

def build_venue_text(
    sessions: list[dict],
) -> str:

    venues = []

    seen = set()

    for session in sessions:

        venue = session.get(
            "venue"
        )

        if not venue:

            continue

        venue = str(
            venue
        ).strip()

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
# CREATE / GET WEEKLY BATCH
# ============================================================

def get_or_create_weekly_batch(
    class_id: str,
    week_start: date,
    generated_by: str,
) -> dict:

    class_id = validate_class_id(
        class_id
    )

    monday = validate_week_start(
        week_start
    )

    friday = (
        monday
        + timedelta(
            days=4
        )
    )

    generated_by = (
        generated_by
        .strip()
    )

    with engine.begin() as connection:

        existing = (
            connection.execute(
                text(
                    """
                    SELECT
                        *

                    FROM
                        public.attendance_register_batches

                    WHERE
                        class_id = CAST(
                            :class_id
                            AS uuid
                        )

                        AND week_start
                            = :week_start

                    LIMIT 1
                    """
                ),
                {
                    "class_id": (
                        class_id
                    ),

                    "week_start": (
                        monday
                    ),
                },
            )
            .mappings()
            .first()
        )

        if existing:

            return dict(
                existing
            )

        control_number = (
            connection.execute(
                text(
                    """
                    SELECT
                        public.next_attendance_control_number(
                            :target_year
                        )
                    """
                ),
                {
                    "target_year": (
                        monday.year
                    ),
                },
            )
            .scalar_one()
        )

        batch = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.attendance_register_batches
                    (
                        control_number,
                        class_id,
                        week_start,
                        week_end,
                        status,
                        generated_by
                    )

                    VALUES
                    (
                        :control_number,

                        CAST(
                            :class_id
                            AS uuid
                        ),

                        :week_start,
                        :week_end,

                        'Generated',

                        :generated_by
                    )

                    RETURNING
                        *
                    """
                ),
                {
                    "control_number": (
                        control_number
                    ),

                    "class_id": (
                        class_id
                    ),

                    "week_start": (
                        monday
                    ),

                    "week_end": (
                        friday
                    ),

                    "generated_by": (
                        generated_by
                    ),
                },
            )
            .mappings()
            .one()
        )

    return dict(
        batch
    )


# ============================================================
# SAVE REGISTER DAYS
# ============================================================

def save_register_days(
    batch_id: str,
    days: list[dict],
) -> None:

    page_number = 0

    with engine.begin() as connection:

        for day in days:

            if day[
                "is_training_day"
            ]:

                page_number += 1

                pdf_page_number = (
                    page_number
                )

            else:

                pdf_page_number = None

            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.attendance_register_days
                    (
                        batch_id,
                        register_date,
                        day_name,
                        is_training_day,
                        calendar_day_type,
                        calendar_description,
                        page_number
                    )

                    VALUES
                    (
                        CAST(
                            :batch_id
                            AS uuid
                        ),

                        :register_date,
                        :day_name,
                        :is_training_day,
                        :calendar_day_type,
                        :calendar_description,
                        :page_number
                    )

                    ON CONFLICT
                    (
                        batch_id,
                        register_date
                    )

                    DO UPDATE SET
                        day_name
                            = EXCLUDED.day_name,

                        is_training_day
                            = EXCLUDED.is_training_day,

                        calendar_day_type
                            = EXCLUDED.calendar_day_type,

                        calendar_description
                            = EXCLUDED.calendar_description,

                        page_number
                            = EXCLUDED.page_number
                    """
                ),
                {
                    "batch_id": (
                        batch_id
                    ),

                    "register_date": (
                        day[
                            "date"
                        ]
                    ),

                    "day_name": (
                        day[
                            "day_name"
                        ]
                    ),

                    "is_training_day": (
                        day[
                            "is_training_day"
                        ]
                    ),

                    "calendar_day_type": (
                        day[
                            "day_type"
                        ]
                    ),

                    "calendar_description": (
                        day[
                            "description"
                        ]
                    ),

                    "page_number": (
                        pdf_page_number
                    ),
                },
            )


# ============================================================
# BUILD PACK DATA
# ============================================================

def build_daily_attendance_pack_data(
    class_id: str,
    week_start: date,
    generated_by: str,
) -> dict:

    monday = validate_week_start(
        week_start
    )

    class_data = get_class_data(
        class_id
    )

    students = get_class_students(
        class_id
    )

    if not students:

        raise ValueError(
            "This class has no active learners."
        )

    days = get_week_days(
        monday
    )

    batch = get_or_create_weekly_batch(
        class_id,
        monday,
        generated_by,
    )

    save_register_days(
        str(
            batch[
                "id"
            ]
        ),
        days,
    )

    enriched_days = []

    for day in days:

        sessions = get_daily_sessions(
            class_id,
            day[
                "date"
            ],
        )

        enriched_days.append(
            {
                **day,

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

                "sessions": (
                    sessions
                ),
            }
        )

    return {
        "batch_id": (
            str(
                batch[
                    "id"
                ]
            )
        ),

        "control_number": (
            batch[
                "control_number"
            ]
        ),

        "week_start": (
            monday
        ),

        "week_end": (
            monday
            + timedelta(
                days=4
            )
        ),

        "status": (
            batch[
                "status"
            ]
        ),

        "programme": {
            "course_code": (
                class_data[
                    "course_code"
                ]
            ),

            "course_name": (
                class_data[
                    "course_name"
                ]
            ),

            "qualification_type": (
                class_data[
                    "qualification_type"
                ]
            ),

            "nqf_level": (
                class_data[
                    "nqf_level"
                ]
            ),

            "credits": (
                class_data[
                    "credits"
                ]
            ),

            "sdp_code": (
                class_data[
                    "sdp_code"
                ]
            ),
        },

        "class": {
            "class_id": (
                str(
                    class_data[
                        "class_id"
                    ]
                )
            ),

            "class_code": (
                class_data[
                    "class_code"
                ]
            ),

            "class_name": (
                class_data[
                    "class_name"
                ]
            ),

            "cycle_code": (
                class_data[
                    "cycle_code"
                ]
            ),

            "class_group": (
                class_data[
                    "class_group"
                ]
            ),

            "facilitator_code": (
                class_data[
                    "facilitator_code"
                ]
            ),

            "assessor_code": (
                class_data[
                    "assessor_code"
                ]
            ),
        },

        "students": (
            students
        ),

        "days": (
            enriched_days
        ),
    }


# ============================================================
# GENERATE PDF PACK
# ============================================================

def generate_daily_attendance_pack(
    class_id: str,
    week_start: date,
    generated_by: str,
) -> Path:

    data = (
        build_daily_attendance_pack_data(
            class_id,
            week_start,
            generated_by,
        )
    )

    output_directory = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "attendance"
        / "daily"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    control_number = (
        data[
            "control_number"
        ]
    )

    safe_control_number = (
        control_number
        .replace(
            "/",
            "-"
        )
        .replace(
            "\\",
            "-"
        )
    )

    filename = (
        f"Attendance_Pack_"
        f"{safe_control_number}.pdf"
    )

    output_path = (
        output_directory
        / filename
    )

    return (
        generate_daily_attendance_pack_pdf(
            output_path,
            data,
        )
    )