from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text

from app.database import engine


# ============================================================
# HELPERS
# ============================================================

def validate_uuid(
    value: str,
    field_name: str,
) -> str:

    try:

        return str(
            UUID(
                str(
                    value
                )
            )
        )

    except Exception as error:

        raise ValueError(
            f"Invalid {field_name}."
        ) from error


def clean_required_text(
    value: str,
    field_name: str,
) -> str:

    value = (
        value
        or ""
    ).strip()

    if not value:

        raise ValueError(
            f"{field_name} is required."
        )

    return value


def clean_optional_text(
    value: str | None,
) -> str | None:

    if value is None:

        return None

    value = (
        value
        .strip()
    )

    return (
        value
        if value
        else None
    )


# ============================================================
# STAFF VALIDATION
# ============================================================

def validate_active_staff(
    staff_code: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        staff_code,
                        role_code,
                        is_active

                    FROM public.staff_accounts

                    WHERE
                        staff_code = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Staff account not found."
        )

    if not row[
        "is_active"
    ]:

        raise ValueError(
            "Staff account is not active."
        )

    return dict(
        row
    )


# ============================================================
# VALIDATE ANNOUNCEMENT AUDIENCE
# ============================================================

def validate_announcement_audience(
    *,
    audience_type: str,
    course_code: str | None,
    cycle_code: str | None,
    class_id: str | None,
    student_number: str | None,
) -> tuple[
    str | None,
    str | None,
    str | None,
    str | None,
]:

    valid_audiences = {
        "AllStudents",
        "Course",
        "Cycle",
        "Class",
        "IndividualStudent",
    }

    if (
        audience_type
        not in valid_audiences
    ):

        raise ValueError(
            "Invalid announcement audience."
        )

    course_code = (
        clean_optional_text(
            course_code
        )
    )

    cycle_code = (
        clean_optional_text(
            cycle_code
        )
    )

    student_number = (
        clean_optional_text(
            student_number
        )
    )

    if class_id:

        class_id = validate_uuid(
            class_id,
            "class ID",
        )

    # --------------------------------------------------------
    # ALL STUDENTS
    # --------------------------------------------------------

    if (
        audience_type
        == "AllStudents"
    ):

        return (
            None,
            None,
            None,
            None,
        )

    # --------------------------------------------------------
    # COURSE
    # --------------------------------------------------------

    if (
        audience_type
        == "Course"
    ):

        if not course_code:

            raise ValueError(
                "Course code is required "
                "for a Course announcement."
            )

        with engine.connect() as connection:

            exists = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM public.courses

                        WHERE
                            course_code
                            = :course_code

                        LIMIT 1
                        """
                    ),
                    {
                        "course_code": (
                            course_code
                        ),
                    },
                )
                .first()
            )

        if not exists:

            raise ValueError(
                "Course not found."
            )

        return (
            course_code,
            None,
            None,
            None,
        )

    # --------------------------------------------------------
    # CYCLE
    # --------------------------------------------------------

    if (
        audience_type
        == "Cycle"
    ):

        if not cycle_code:

            raise ValueError(
                "Cycle code is required "
                "for a Cycle announcement."
            )

        with engine.connect() as connection:

            exists = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM public.cycles

                        WHERE
                            cycle_code
                            = :cycle_code

                        LIMIT 1
                        """
                    ),
                    {
                        "cycle_code": (
                            cycle_code
                        ),
                    },
                )
                .first()
            )

        if not exists:

            raise ValueError(
                "Cycle not found."
            )

        return (
            None,
            cycle_code,
            None,
            None,
        )

    # --------------------------------------------------------
    # CLASS
    # --------------------------------------------------------

    if (
        audience_type
        == "Class"
    ):

        if not class_id:

            raise ValueError(
                "Class ID is required "
                "for a Class announcement."
            )

        with engine.connect() as connection:

            exists = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM public.classes

                        WHERE
                            id = CAST(
                                :class_id
                                AS uuid
                            )

                        LIMIT 1
                        """
                    ),
                    {
                        "class_id": (
                            class_id
                        ),
                    },
                )
                .first()
            )

        if not exists:

            raise ValueError(
                "Class not found."
            )

        return (
            None,
            None,
            class_id,
            None,
        )

    # --------------------------------------------------------
    # INDIVIDUAL STUDENT
    # --------------------------------------------------------

    if (
        audience_type
        == "IndividualStudent"
    ):

        if not student_number:

            raise ValueError(
                "Student number is required "
                "for an individual announcement."
            )

        with engine.connect() as connection:

            exists = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM public.applications

                        WHERE
                            student_number
                            = :student_number

                        LIMIT 1
                        """
                    ),
                    {
                        "student_number": (
                            student_number
                        ),
                    },
                )
                .first()
            )

        if not exists:

            raise ValueError(
                "Student not found."
            )

        return (
            None,
            None,
            None,
            student_number,
        )

    raise ValueError(
        "Invalid announcement audience."
    )


# ============================================================
# FORMAT ANNOUNCEMENT
# ============================================================

def format_announcement(
    row,
) -> dict:

    row = dict(
        row
    )

    return {
        "announcement_id": str(
            row[
                "id"
            ]
        ),

        "title": (
            row[
                "title"
            ]
        ),

        "message": (
            row[
                "message"
            ]
        ),

        "announcement_type": (
            row[
                "announcement_type"
            ]
        ),

        "priority": (
            row[
                "priority"
            ]
        ),

        "audience_type": (
            row[
                "audience_type"
            ]
        ),

        "course_code": (
            row[
                "course_code"
            ]
        ),

        "cycle_code": (
            row[
                "cycle_code"
            ]
        ),

        "class_id": (
            str(
                row[
                    "class_id"
                ]
            )
            if row[
                "class_id"
            ]
            else None
        ),

        "student_number": (
            row[
                "student_number"
            ]
        ),

        "created_by_staff_code": (
            row.get(
                "created_by_staff_code"
            )
        ),

        "published_by": (
            row[
                "published_by"
            ]
        ),

        "published_at": (
            row[
                "published_at"
            ]
        ),

        "expires_at": (
            row[
                "expires_at"
            ]
        ),

        "status": (
            row[
                "status"
            ]
        ),

        "created_at": (
            row[
                "created_at"
            ]
        ),

        "updated_at": (
            row[
                "updated_at"
            ]
        ),

        "read_count": (
            row.get(
                "read_count",
                0,
            )
            or 0
        ),
    }


# ============================================================
# CREATE ANNOUNCEMENT DRAFT
# ============================================================

def create_staff_announcement(
    *,
    staff_code: str,
    title: str,
    message: str,
    announcement_type: str,
    priority: str,
    audience_type: str,
    course_code: str | None,
    cycle_code: str | None,
    class_id: str | None,
    student_number: str | None,
    expires_at: datetime | None,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    title = clean_required_text(
        title,
        "Title",
    )

    message = clean_required_text(
        message,
        "Message",
    )

    validate_active_staff(
        staff_code
    )

    (
        course_code,
        cycle_code,
        class_id,
        student_number,
    ) = (
        validate_announcement_audience(
            audience_type=(
                audience_type
            ),

            course_code=(
                course_code
            ),

            cycle_code=(
                cycle_code
            ),

            class_id=(
                class_id
            ),

            student_number=(
                student_number
            ),
        )
    )

    with engine.begin() as connection:

        announcement_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.announcements
                    (
                        title,
                        message,
                        announcement_type,
                        priority,
                        audience_type,

                        course_code,
                        cycle_code,
                        class_id,
                        student_number,

                        created_by_staff_code,

                        expires_at,

                        status
                    )

                    VALUES
                    (
                        :title,
                        :message,
                        :announcement_type,
                        :priority,
                        :audience_type,

                        :course_code,
                        :cycle_code,
                        CAST(
                            :class_id
                            AS uuid
                        ),
                        :student_number,

                        :staff_code,

                        :expires_at,

                        'Draft'
                    )

                    RETURNING id
                    """
                ),
                {
                    "title": (
                        title
                    ),

                    "message": (
                        message
                    ),

                    "announcement_type": (
                        announcement_type
                    ),

                    "priority": (
                        priority
                    ),

                    "audience_type": (
                        audience_type
                    ),

                    "course_code": (
                        course_code
                    ),

                    "cycle_code": (
                        cycle_code
                    ),

                    "class_id": (
                        class_id
                    ),

                    "student_number": (
                        student_number
                    ),

                    "staff_code": (
                        staff_code
                    ),

                    "expires_at": (
                        expires_at
                    ),
                },
            )
            .scalar_one()
        )

    return get_staff_announcement(
        staff_code=(
            staff_code
        ),

        announcement_id=str(
            announcement_id
        ),
    )


# ============================================================
# LIST ANNOUNCEMENTS
# ============================================================

def get_staff_announcements(
    *,
    staff_code: str,
) -> list[dict]:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        a.id,
                        a.title,
                        a.message,
                        a.announcement_type,
                        a.priority,
                        a.audience_type,
                        a.course_code,
                        a.cycle_code,
                        a.class_id,
                        a.student_number,
                        a.created_by_staff_code,
                        a.published_by,
                        a.published_at,
                        a.expires_at,
                        a.status,
                        a.created_at,
                        a.updated_at,

                        COUNT(
                            ar.id
                        ) AS read_count

                    FROM
                        public.announcements a

                    LEFT JOIN
                        public.announcement_reads ar
                    ON
                        ar.announcement_id = a.id

                    WHERE
                        a.created_by_staff_code
                            = :staff_code

                        OR

                        a.published_by
                            = :staff_code

                    GROUP BY
                        a.id

                    ORDER BY
                        a.created_at DESC
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        format_announcement(
            row
        )
        for row in rows
    ]


# ============================================================
# GET ONE ANNOUNCEMENT
# ============================================================

def get_staff_announcement(
    *,
    staff_code: str,
    announcement_id: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    announcement_id = validate_uuid(
        announcement_id,
        "announcement ID",
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        a.id,
                        a.title,
                        a.message,
                        a.announcement_type,
                        a.priority,
                        a.audience_type,
                        a.course_code,
                        a.cycle_code,
                        a.class_id,
                        a.student_number,
                        a.created_by_staff_code,
                        a.published_by,
                        a.published_at,
                        a.expires_at,
                        a.status,
                        a.created_at,
                        a.updated_at,

                        COUNT(
                            ar.id
                        ) AS read_count

                    FROM
                        public.announcements a

                    LEFT JOIN
                        public.announcement_reads ar
                    ON
                        ar.announcement_id = a.id

                    WHERE
                        a.id = CAST(
                            :announcement_id
                            AS uuid
                        )

                        AND
                        (
                            a.created_by_staff_code
                                = :staff_code

                            OR

                            a.published_by
                                = :staff_code
                        )

                    GROUP BY
                        a.id

                    LIMIT 1
                    """
                ),
                {
                    "announcement_id": (
                        announcement_id
                    ),

                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Announcement not found."
        )

    return format_announcement(
        row
    )


# ============================================================
# UPDATE ANNOUNCEMENT DRAFT
# ============================================================

def update_staff_announcement(
    *,
    staff_code: str,
    announcement_id: str,
    updates: dict,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    announcement_id = validate_uuid(
        announcement_id,
        "announcement ID",
    )

    current = (
        get_staff_announcement(
            staff_code=(
                staff_code
            ),

            announcement_id=(
                announcement_id
            ),
        )
    )

    if (
        current[
            "status"
        ]
        != "Draft"
    ):

        raise ValueError(
            "Only draft announcements "
            "can be edited."
        )

    title = (
        updates.get(
            "title"
        )
        if updates.get(
            "title"
        )
        is not None
        else current[
            "title"
        ]
    )

    message = (
        updates.get(
            "message"
        )
        if updates.get(
            "message"
        )
        is not None
        else current[
            "message"
        ]
    )

    announcement_type = (
        updates.get(
            "announcement_type"
        )
        if updates.get(
            "announcement_type"
        )
        is not None
        else current[
            "announcement_type"
        ]
    )

    priority = (
        updates.get(
            "priority"
        )
        if updates.get(
            "priority"
        )
        is not None
        else current[
            "priority"
        ]
    )

    audience_type = (
        updates.get(
            "audience_type"
        )
        if updates.get(
            "audience_type"
        )
        is not None
        else current[
            "audience_type"
        ]
    )

    course_code = (
        updates.get(
            "course_code"
        )
        if "course_code"
        in updates
        else current[
            "course_code"
        ]
    )

    cycle_code = (
        updates.get(
            "cycle_code"
        )
        if "cycle_code"
        in updates
        else current[
            "cycle_code"
        ]
    )

    class_id = (
        updates.get(
            "class_id"
        )
        if "class_id"
        in updates
        else current[
            "class_id"
        ]
    )

    student_number = (
        updates.get(
            "student_number"
        )
        if "student_number"
        in updates
        else current[
            "student_number"
        ]
    )

    expires_at = (
        updates.get(
            "expires_at"
        )
        if "expires_at"
        in updates
        else current[
            "expires_at"
        ]
    )

    (
        course_code,
        cycle_code,
        class_id,
        student_number,
    ) = (
        validate_announcement_audience(
            audience_type=(
                audience_type
            ),

            course_code=(
                course_code
            ),

            cycle_code=(
                cycle_code
            ),

            class_id=(
                class_id
            ),

            student_number=(
                student_number
            ),
        )
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.announcements

                SET
                    title = :title,
                    message = :message,
                    announcement_type
                        = :announcement_type,
                    priority = :priority,
                    audience_type
                        = :audience_type,

                    course_code
                        = :course_code,
                    cycle_code
                        = :cycle_code,
                    class_id = CAST(
                        :class_id
                        AS uuid
                    ),
                    student_number
                        = :student_number,

                    expires_at
                        = :expires_at,

                    updated_at
                        = now()

                WHERE
                    id = CAST(
                        :announcement_id
                        AS uuid
                    )
                """
            ),
            {
                "announcement_id": (
                    announcement_id
                ),

                "title": (
                    clean_required_text(
                        title,
                        "Title",
                    )
                ),

                "message": (
                    clean_required_text(
                        message,
                        "Message",
                    )
                ),

                "announcement_type": (
                    announcement_type
                ),

                "priority": (
                    priority
                ),

                "audience_type": (
                    audience_type
                ),

                "course_code": (
                    course_code
                ),

                "cycle_code": (
                    cycle_code
                ),

                "class_id": (
                    class_id
                ),

                "student_number": (
                    student_number
                ),

                "expires_at": (
                    expires_at
                ),
            },
        )

    return get_staff_announcement(
        staff_code=(
            staff_code
        ),

        announcement_id=(
            announcement_id
        ),
    )


# ============================================================
# PUBLISH ANNOUNCEMENT
# ============================================================

def publish_staff_announcement(
    *,
    staff_code: str,
    announcement_id: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    announcement_id = validate_uuid(
        announcement_id,
        "announcement ID",
    )

    current = (
        get_staff_announcement(
            staff_code=(
                staff_code
            ),

            announcement_id=(
                announcement_id
            ),
        )
    )

    if (
        current[
            "status"
        ]
        == "Archived"
    ):

        raise ValueError(
            "Archived announcements "
            "cannot be published."
        )

    if (
        current[
            "status"
        ]
        == "Cancelled"
    ):

        raise ValueError(
            "Cancelled announcements "
            "cannot be published."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.announcements

                SET
                    status = 'Published',
                    published_by = :staff_code,
                    published_at = now(),
                    updated_at = now()

                WHERE
                    id = CAST(
                        :announcement_id
                        AS uuid
                    )
                """
            ),
            {
                "announcement_id": (
                    announcement_id
                ),

                "staff_code": (
                    staff_code
                ),
            },
        )

    return get_staff_announcement(
        staff_code=(
            staff_code
        ),

        announcement_id=(
            announcement_id
        ),
    )


# ============================================================
# ARCHIVE ANNOUNCEMENT
# ============================================================

def archive_staff_announcement(
    *,
    staff_code: str,
    announcement_id: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    announcement_id = validate_uuid(
        announcement_id,
        "announcement ID",
    )

    get_staff_announcement(
        staff_code=(
            staff_code
        ),

        announcement_id=(
            announcement_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.announcements

                SET
                    status = 'Archived',
                    updated_at = now()

                WHERE
                    id = CAST(
                        :announcement_id
                        AS uuid
                    )
                """
            ),
            {
                "announcement_id": (
                    announcement_id
                ),
            },
        )

    return get_staff_announcement(
        staff_code=(
            staff_code
        ),

        announcement_id=(
            announcement_id
        ),
    )