from datetime import time
from uuid import UUID

from sqlalchemy import text

from app.database import engine

# ============================================================
# HELPERS
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


def normalise_control_number(
    control_number: str,
) -> str:

    control_number = (
        control_number
        .strip()
        .upper()
    )

    if not control_number:

        raise ValueError(
            "Control number is required."
        )

    return control_number


def parse_optional_time(
    value: str | None,
) -> time | None:

    if value is None:

        return None

    value = (
        value
        .strip()
    )

    if not value:

        return None

    try:

        hour_text, minute_text = (
            value.split(
                ":",
                1,
            )
        )

        return time(
            hour=int(
                hour_text
            ),
            minute=int(
                minute_text
            ),
        )

    except Exception as error:

        raise ValueError(
            
                "Time must use HH:MM format, "
                "for example 08:15."
            
        ) from error


# ============================================================
# CONTROL NUMBER LOOKUP
# ============================================================

def get_weekly_attendance_batch(
    control_number: str,
) -> dict | None:

    control_number = (
        normalise_control_number(
            control_number
        )
    )

    query = text(
        """
        SELECT
            arb.id AS batch_id,

            arb.control_number,
            arb.week_start,
            arb.week_end,
            arb.status,

            arb.generated_by,
            arb.generated_at,

            arb.captured_by,
            arb.captured_at,

            arb.verified_by,
            arb.verified_at,

            arb.notes,

            cl.id AS class_id,
            cl.class_code,
            cl.class_name,
            cl.class_group,
            cl.course_code,
            cl.cycle_code,
            cl.facilitator_code,
            cl.assessor_code,

            c.course_name,
            c.nqf_level,
            c.credits

        FROM
            public.attendance_register_batches arb

        JOIN
            public.classes cl
            ON cl.id
            = arb.class_id

        JOIN
            public.courses c
            ON c.course_code
            = cl.course_code

        WHERE
            arb.control_number
            = :control_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "control_number": (
                        control_number
                    ),
                },
            )
            .mappings()
            .first()
        )

    return (
        dict(
            row
        )
        if row
        else None
    )


# ============================================================
# GET REGISTER DAYS
# ============================================================

def get_batch_days(
    batch_id: str,
) -> list[dict]:

    batch_id = validate_uuid(
        batch_id,
        "batch ID",
    )

    query = text(
        """
        SELECT
            id AS register_day_id,
            register_date,
            day_name,

            is_training_day,

            calendar_day_type,
            calendar_description,

            page_number

        FROM
            public.attendance_register_days

        WHERE
            batch_id = CAST(
                :batch_id
                AS uuid
            )

        ORDER BY
            register_date
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "batch_id": (
                        batch_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# GET CLASS LEARNERS
# ============================================================

def get_batch_students(
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

            a.national_id,
            a.alternate_id,
            a.alt_id_type,

            a.first_name,
            a.middle_name,
            a.last_name

        FROM
            public.class_enrolments ce

        JOIN
            public.registrations r
            ON r.id
            = ce.registration_id

        JOIN
            public.applications a
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

        rows = (
            connection.execute(
                query,
                {
                    "class_id": (
                        class_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# GET EXISTING WEEKLY CAPTURE
# ============================================================

def get_existing_capture_records(
    batch_id: str,
) -> list[dict]:

    batch_id = validate_uuid(
        batch_id,
        "batch ID",
    )

    query = text(
        """
        SELECT
            awcr.id,

            awcr.batch_id,
            awcr.register_day_id,
            awcr.registration_id,

            awcr.attendance_status,
            awcr.sign_in_time,
            awcr.sign_out_time,

            awcr.notes,

            awcr.captured_by,
            awcr.captured_at,
            awcr.updated_at

        FROM
            public.attendance_weekly_capture_records awcr

        WHERE
            awcr.batch_id = CAST(
                :batch_id
                AS uuid
            )
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "batch_id": (
                        batch_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# FULL CONTROL NUMBER LOOKUP
# ============================================================

def lookup_weekly_attendance_control(
    control_number: str,
) -> dict:

    batch = (
        get_weekly_attendance_batch(
            control_number
        )
    )

    if not batch:

        raise ValueError(
            "Attendance control number not found."
        )

    batch_id = str(
        batch[
            "batch_id"
        ]
    )

    class_id = str(
        batch[
            "class_id"
        ]
    )

    days = get_batch_days(
        batch_id
    )

    students = get_batch_students(
        class_id
    )

    existing = (
        get_existing_capture_records(
            batch_id
        )
    )

    existing_map = {
        (
            str(
                row[
                    "register_day_id"
                ]
            ),
            str(
                row[
                    "registration_id"
                ]
            ),
        ): row
        for row in existing
    }

    day_payload = []

    for day in days:

        learner_rows = []

        for student in students:

            key = (
                str(
                    day[
                        "register_day_id"
                    ]
                ),
                str(
                    student[
                        "registration_id"
                    ]
                ),
            )

            captured = (
                existing_map.get(
                    key
                )
            )

            learner_rows.append(
                {
                    "registration_id": (
                        str(
                            student[
                                "registration_id"
                            ]
                        )
                    ),

                    "student_number": (
                        student[
                            "student_number"
                        ]
                    ),

                    "national_id": (
                        student[
                            "national_id"
                        ]
                    ),

                    "alternate_id": (
                        student[
                            "alternate_id"
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
                        captured[
                            "attendance_status"
                        ]
                        if captured
                        else None
                    ),

                    "sign_in_time": (
                        captured[
                            "sign_in_time"
                        ]
                        if captured
                        else None
                    ),

                    "sign_out_time": (
                        captured[
                            "sign_out_time"
                        ]
                        if captured
                        else None
                    ),

                    "notes": (
                        captured[
                            "notes"
                        ]
                        if captured
                        else None
                    ),
                }
            )

        day_payload.append(
            {
                "register_day_id": (
                    str(
                        day[
                            "register_day_id"
                        ]
                    )
                ),

                "register_date": (
                    day[
                        "register_date"
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
                        "calendar_day_type"
                    ]
                ),

                "calendar_description": (
                    day[
                        "calendar_description"
                    ]
                ),

                "page_number": (
                    day[
                        "page_number"
                    ]
                ),

                "students": (
                    learner_rows
                ),
            }
        )

    return {
        "control_number": (
            batch[
                "control_number"
            ]
        ),

        "batch_status": (
            batch[
                "status"
            ]
        ),

        "week_start": (
            batch[
                "week_start"
            ]
        ),

        "week_end": (
            batch[
                "week_end"
            ]
        ),

        "class": {
            "class_id": (
                class_id
            ),

            "class_code": (
                batch[
                    "class_code"
                ]
            ),

            "class_name": (
                batch[
                    "class_name"
                ]
            ),

            "class_group": (
                batch[
                    "class_group"
                ]
            ),

            "course_code": (
                batch[
                    "course_code"
                ]
            ),

            "course_name": (
                batch[
                    "course_name"
                ]
            ),

            "nqf_level": (
                batch[
                    "nqf_level"
                ]
            ),

            "cycle_code": (
                batch[
                    "cycle_code"
                ]
            ),
        },

        "days": (
            day_payload
        ),
    }


# ============================================================
# SAVE WEEKLY CAPTURE
# ============================================================

def save_weekly_attendance_capture(
    control_number: str,
    captured_by: str,
    records: list[dict],
) -> dict:

    control_number = (
        normalise_control_number(
            control_number
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

    batch = (
        get_weekly_attendance_batch(
            control_number
        )
    )

    if not batch:

        raise ValueError(
            "Attendance control number not found."
        )

    if batch[
        "status"
    ] in {
        "Verified",
        "Archived",
        "Cancelled",
    }:

        raise ValueError(
            
                "This attendance batch can no "
                "longer be edited."
            
        )

    batch_id = str(
        batch[
            "batch_id"
        ]
    )

    class_id = str(
        batch[
            "class_id"
        ]
    )

    valid_days = {
        str(
            day[
                "register_day_id"
            ]
        ): day
        for day in get_batch_days(
            batch_id
        )
    }

    valid_students = {
        str(
            student[
                "registration_id"
            ]
        )
        for student in get_batch_students(
            class_id
        )
    }

    with engine.begin() as connection:

        for record in records:

            register_day_id = (
                validate_uuid(
                    record[
                        "register_day_id"
                    ],
                    "register day ID",
                )
            )

            registration_id = (
                validate_uuid(
                    record[
                        "registration_id"
                    ],
                    "registration ID",
                )
            )

            if (
                register_day_id
                not in valid_days
            ):

                raise ValueError(
                    
                        "A register day does not "
                        "belong to this control number."
                    
                )

            if not valid_days[
                register_day_id
            ][
                "is_training_day"
            ]:

                raise ValueError(
                    
                        "Attendance cannot be captured "
                        "for a non-training day."
                    
                )

            if (
                registration_id
                not in valid_students
            ):

                raise ValueError(
                    
                        "A learner does not belong "
                        "to this class."
                    
                )

            status = (
                record[
                    "attendance_status"
                ]
            )

            if status not in {
                "Present",
                "Absent",
                "Late",
                "Excused",
            }:

                raise ValueError(
                    "Invalid attendance status."
                )

            sign_in_time = (
                parse_optional_time(
                    record.get(
                        "sign_in_time"
                    )
                )
            )

            sign_out_time = (
                parse_optional_time(
                    record.get(
                        "sign_out_time"
                    )
                )
            )

            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.attendance_weekly_capture_records
                    (
                        batch_id,
                        register_day_id,
                        registration_id,

                        attendance_status,

                        sign_in_time,
                        sign_out_time,

                        notes,

                        captured_by
                    )

                    VALUES
                    (
                        CAST(
                            :batch_id
                            AS uuid
                        ),

                        CAST(
                            :register_day_id
                            AS uuid
                        ),

                        CAST(
                            :registration_id
                            AS uuid
                        ),

                        :attendance_status,

                        :sign_in_time,
                        :sign_out_time,

                        :notes,

                        :captured_by
                    )

                    ON CONFLICT
                    (
                        register_day_id,
                        registration_id
                    )

                    DO UPDATE SET
                        attendance_status
                            = EXCLUDED.attendance_status,

                        sign_in_time
                            = EXCLUDED.sign_in_time,

                        sign_out_time
                            = EXCLUDED.sign_out_time,

                        notes
                            = EXCLUDED.notes,

                        captured_by
                            = EXCLUDED.captured_by,

                        captured_at
                            = now(),

                        updated_at
                            = now()
                    """
                ),
                {
                    "batch_id": (
                        batch_id
                    ),

                    "register_day_id": (
                        register_day_id
                    ),

                    "registration_id": (
                        registration_id
                    ),

                    "attendance_status": (
                        status
                    ),

                    "sign_in_time": (
                        sign_in_time
                    ),

                    "sign_out_time": (
                        sign_out_time
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
                    public.attendance_register_batches

                SET
                    captured_by = :captured_by,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :batch_id
                        AS uuid
                    )
                """
            ),
            {
                "captured_by": (
                    captured_by
                ),

                "batch_id": (
                    batch_id
                ),
            },
        )

    return lookup_weekly_attendance_control(
        control_number
    )


# ============================================================
# SUBMIT WEEKLY CAPTURE
# ============================================================

def submit_weekly_attendance_capture(
    control_number: str,
    captured_by: str,
) -> dict:

    batch = (
        get_weekly_attendance_batch(
            control_number
        )
    )

    if not batch:

        raise ValueError(
            "Attendance control number not found."
        )

    batch_id = str(
        batch[
            "batch_id"
        ]
    )

    class_id = str(
        batch[
            "class_id"
        ]
    )

    days = [
        day
        for day in get_batch_days(
            batch_id
        )
        if day[
            "is_training_day"
        ]
    ]

    students = get_batch_students(
        class_id
    )

    existing = (
        get_existing_capture_records(
            batch_id
        )
    )

    captured_keys = {
        (
            str(
                record[
                    "register_day_id"
                ]
            ),
            str(
                record[
                    "registration_id"
                ]
            ),
        )
        for record in existing
    }

    missing = []

    for day in days:

        for student in students:

            key = (
                str(
                    day[
                        "register_day_id"
                    ]
                ),
                str(
                    student[
                        "registration_id"
                    ]
                ),
            )

            if key not in captured_keys:

                missing.append(
                    key
                )

    if missing:

        raise ValueError(
            
                "Attendance must be captured "
                "for every learner on every "
                "training day before submission."
            
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.attendance_register_batches

                SET
                    status = 'Captured',
                    captured_by = :captured_by,
                    captured_at = now(),
                    updated_at = now()

                WHERE
                    id = CAST(
                        :batch_id
                        AS uuid
                    )
                """
            ),
            {
                "captured_by": (
                    captured_by
                ),

                "batch_id": (
                    batch_id
                ),
            },
        )

    return lookup_weekly_attendance_control(
        control_number
    )


# ============================================================
# VERIFY + PUBLISH TO OFFICIAL ATTENDANCE
# ============================================================

def verify_weekly_attendance_capture(
    control_number: str,
    verified_by: str,
) -> dict:

    batch = (
        get_weekly_attendance_batch(
            control_number
        )
    )

    if not batch:

        raise ValueError(
            "Attendance control number not found."
        )

    if (
        batch[
            "status"
        ]
        != "Captured"
    ):

        raise ValueError(
            
                "Only a captured attendance "
                "batch can be verified."
            
        )

    batch_id = str(
        batch[
            "batch_id"
        ]
    )

    class_id = str(
        batch[
            "class_id"
        ]
    )

    records = (
        get_existing_capture_records(
            batch_id
        )
    )

    days = {
        str(
            day[
                "register_day_id"
            ]
        ): day
        for day in get_batch_days(
            batch_id
        )
    }

    with engine.begin() as connection:

        for record in records:

            day = days.get(
                str(
                    record[
                        "register_day_id"
                    ]
                )
            )

            if not day:

                continue

            register_date = (
                day[
                    "register_date"
                ]
            )

            timetable_sessions = (
                connection.execute(
                    text(
                        """
                        SELECT
                            id

                        FROM
                            public.timetable_sessions

                        WHERE
                            class_id = CAST(
                                :class_id
                                AS uuid
                            )

                            AND session_date
                                = :register_date

                            AND status = 'Published'
                        """
                    ),
                    {
                        "class_id": (
                            class_id
                        ),

                        "register_date": (
                            register_date
                        ),
                    },
                )
                .mappings()
                .all()
            )

            for timetable in timetable_sessions:

                timetable_session_id = (
                    str(
                        timetable[
                            "id"
                        ]
                    )
                )

                attendance_session = (
                    connection.execute(
                        text(
                            """
                            SELECT
                                id

                            FROM
                                public.attendance_sessions

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

                if attendance_session:

                    attendance_session_id = (
                        str(
                            attendance_session[
                                "id"
                            ]
                        )
                    )

                    connection.execute(
                        text(
                            """
                            UPDATE
                                public.attendance_sessions

                            SET
                                status = 'Rendered',
                                rendered_by = :verified_by,
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
                            "verified_by": (
                                verified_by
                            ),

                            "attendance_session_id": (
                                attendance_session_id
                            ),
                        },
                    )

                else:

                    created_session = (
                        connection.execute(
                            text(
                                """
                                INSERT INTO
                                    public.attendance_sessions
                                (
                                    timetable_session_id,
                                    status,
                                    captured_by,
                                    submitted_at,
                                    rendered_by,
                                    rendered_at
                                )

                                VALUES
                                (
                                    CAST(
                                        :timetable_session_id
                                        AS uuid
                                    ),

                                    'Rendered',

                                    :verified_by,

                                    now(),

                                    :verified_by,

                                    now()
                                )

                                RETURNING
                                    id
                                """
                            ),
                            {
                                "timetable_session_id": (
                                    timetable_session_id
                                ),

                                "verified_by": (
                                    verified_by
                                ),
                            },
                        )
                        .mappings()
                        .one()
                    )

                    attendance_session_id = (
                        str(
                            created_session[
                                "id"
                            ]
                        )
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

                            :notes,
                            :verified_by
                        )

                        ON CONFLICT
                        (
                            attendance_session_id,
                            registration_id
                        )

                        DO UPDATE SET
                            attendance_status
                                = EXCLUDED.attendance_status,

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
                            str(
                                record[
                                    "registration_id"
                                ]
                            )
                        ),

                        "attendance_status": (
                            record[
                                "attendance_status"
                            ]
                        ),

                        "notes": (
                            record[
                                "notes"
                            ]
                        ),

                        "verified_by": (
                            verified_by
                        ),
                    },
                )

        connection.execute(
            text(
                """
                UPDATE
                    public.attendance_register_batches

                SET
                    status = 'Verified',
                    verified_by = :verified_by,
                    verified_at = now(),
                    updated_at = now()

                WHERE
                    id = CAST(
                        :batch_id
                        AS uuid
                    )
                """
            ),
            {
                "verified_by": (
                    verified_by
                ),

                "batch_id": (
                    batch_id
                ),
            },
        )

    return lookup_weekly_attendance_control(
        control_number
    )