from datetime import date
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
                str(
                    value
                )
            )
        )

    except (
        ValueError,
        TypeError,
    ) as error:

        raise ValueError(
            f"Invalid {label}."
        ) from error


def clean_required_text(
    value,
    label: str,
) -> str:

    value = str(
        value or ""
    ).strip()

    if not value:

        raise ValueError(
            f"{label} is required."
        )

    return value


# ============================================================
# CURRENT REGISTRATION
# ============================================================

def get_student_current_registration(
    student_number: str,
) -> dict:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        r.id,
                        r.student_number,
                        r.course_code,
                        r.cycle,
                        r.registration_status,
                        r.registration_date,
                        r.program_start_date,
                        r.expected_completion_date,

                        c.course_name

                    FROM
                        public.registrations r

                    LEFT JOIN
                        public.courses c
                        ON c.course_code = r.course_code

                    WHERE
                        r.student_number = :student_number

                    ORDER BY
                        r.registration_date DESC,
                        r.created_at DESC

                    LIMIT 1
                    """
                ),
                {
                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "No student registration was found."
        )

    return dict(
        row
    )


def ensure_messages_available(
    registration: dict,
) -> None:

    completion_date = (
        registration.get(
            "expected_completion_date"
        )
    )

    if (
        completion_date
        and completion_date < date.today()
    ):

        raise ValueError(
            
                "Messaging is no longer available "
                "because this programme has ended."
            
        )


# ============================================================
# ANNOUNCEMENTS
# ============================================================

def get_student_announcements(
    student_number: str,
) -> list[dict]:

    registration = (
        get_student_current_registration(
            student_number
        )
    )

    registration_id = (
        str(
            registration[
                "id"
            ]
        )
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
                        a.published_by,
                        a.published_at,
                        a.expires_at,

                        CASE
                            WHEN ar.id IS NULL
                                THEN false
                            ELSE true
                        END AS is_read,

                        ar.read_at

                    FROM
                        public.announcements a

                    LEFT JOIN
                        public.announcement_reads ar
                        ON ar.announcement_id = a.id
                        AND ar.student_number = :student_number

                    WHERE
                        a.status = 'Published'

                        AND a.published_at IS NOT NULL

                        AND a.published_at <= now()

                        AND a.published_at >=
                            now() - interval '30 days'

                        AND (
                            a.expires_at IS NULL
                            OR a.expires_at > now()
                        )

                        AND (
                            a.audience_type = 'AllStudents'

                            OR (
                                a.audience_type = 'Course'
                                AND a.course_code = :course_code
                            )

                            OR (
                                a.audience_type = 'Cycle'
                                AND a.cycle_code = :cycle_code
                            )

                            OR (
                                a.audience_type = 'IndividualStudent'
                                AND a.student_number = :student_number
                            )

                            OR (
                                a.audience_type = 'Class'

                                AND EXISTS (
                                    SELECT
                                        1

                                    FROM
                                        public.class_enrolments ce

                                    WHERE
                                        ce.class_id = a.class_id

                                        AND ce.registration_id =
                                            CAST(
                                                :registration_id
                                                AS uuid
                                            )

                                        AND ce.status = 'Active'
                                )
                            )
                        )

                    ORDER BY
                        CASE a.priority
                            WHEN 'Urgent'
                                THEN 1
                            WHEN 'Important'
                                THEN 2
                            ELSE 3
                        END,

                        a.published_at DESC
                    """
                ),
                {
                    "student_number": (
                        student_number
                    ),

                    "course_code": (
                        registration.get(
                            "course_code"
                        )
                    ),

                    "cycle_code": (
                        registration.get(
                            "cycle"
                        )
                    ),

                    "registration_id": (
                        registration_id
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


def get_student_announcement(
    student_number: str,
    announcement_id: str,
) -> dict:

    announcement_id = validate_uuid(
        announcement_id,
        "announcement ID",
    )

    announcements = (
        get_student_announcements(
            student_number
        )
    )

    for announcement in announcements:

        if (
            str(
                announcement[
                    "id"
                ]
            )
            == announcement_id
        ):

            return announcement

    raise ValueError(
        
            "Announcement was not found "
            "or is not available to this student."
        
    )


def mark_announcement_read(
    student_number: str,
    announcement_id: str,
) -> dict:

    announcement = (
        get_student_announcement(
            student_number,
            announcement_id,
        )
    )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.announcement_reads (
                            announcement_id,
                            student_number,
                            read_at
                        )

                    VALUES (
                        CAST(
                            :announcement_id
                            AS uuid
                        ),
                        :student_number,
                        now()
                    )

                    ON CONFLICT (
                        announcement_id,
                        student_number
                    )

                    DO UPDATE SET
                        read_at =
                            public.announcement_reads.read_at

                    RETURNING
                        announcement_id,
                        student_number,
                        read_at
                    """
                ),
                {
                    "announcement_id": (
                        str(
                            announcement[
                                "id"
                            ]
                        )
                    ),

                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .first()
        )

    return dict(
        row
    )


# ============================================================
# MESSAGE THREADS
# ============================================================

def get_student_message_threads(
    student_number: str,
) -> list[dict]:

    registration = (
        get_student_current_registration(
            student_number
        )
    )

    completion_date = (
        registration.get(
            "expected_completion_date"
        )
    )

    if (
        completion_date
        and completion_date < date.today()
    ):

        return []

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        mt.id,
                        mt.subject,
                        mt.category,
                        mt.status,
                        mt.assigned_staff_code,
                        mt.created_at,
                        mt.updated_at,
                        mt.closed_at,

                        (
                            SELECT
                                m.message_body

                            FROM
                                public.messages m

                            WHERE
                                m.thread_id = mt.id

                            ORDER BY
                                m.sent_at DESC

                            LIMIT 1
                        ) AS last_message,

                        (
                            SELECT
                                m.sent_at

                            FROM
                                public.messages m

                            WHERE
                                m.thread_id = mt.id

                            ORDER BY
                                m.sent_at DESC

                            LIMIT 1
                        ) AS last_message_at,

                        (
                            SELECT
                                COUNT(*)

                            FROM
                                public.messages m

                            WHERE
                                m.thread_id = mt.id

                                AND m.sender_type <> 'Student'

                                AND m.read_at IS NULL
                        ) AS unread_count

                    FROM
                        public.message_threads mt

                    WHERE
                        mt.student_number =
                            :student_number

                        AND mt.registration_id =
                            CAST(
                                :registration_id
                                AS uuid
                            )

                    ORDER BY
                        mt.updated_at DESC,
                        mt.created_at DESC
                    """
                ),
                {
                    "student_number": (
                        student_number
                    ),

                    "registration_id": (
                        str(
                            registration[
                                "id"
                            ]
                        )
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


def get_student_message_thread(
    student_number: str,
    thread_id: str,
    mark_staff_messages_read: bool = True,
) -> dict:

    thread_id = validate_uuid(
        thread_id,
        "message thread ID",
    )

    registration = (
        get_student_current_registration(
            student_number
        )
    )

    ensure_messages_available(
        registration
    )

    with engine.begin() as connection:

        thread = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        registration_id,
                        student_number,
                        subject,
                        category,
                        status,
                        assigned_staff_code,
                        created_at,
                        updated_at,
                        closed_at

                    FROM
                        public.message_threads

                    WHERE
                        id = CAST(
                            :thread_id
                            AS uuid
                        )

                        AND student_number =
                            :student_number

                        AND registration_id =
                            CAST(
                                :registration_id
                                AS uuid
                            )
                    """
                ),
                {
                    "thread_id": (
                        thread_id
                    ),

                    "student_number": (
                        student_number
                    ),

                    "registration_id": (
                        str(
                            registration[
                                "id"
                            ]
                        )
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not thread:

            raise ValueError(
                "Message thread was not found."
            )

        messages = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        thread_id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at

                    FROM
                        public.messages

                    WHERE
                        thread_id = CAST(
                            :thread_id
                            AS uuid
                        )

                    ORDER BY
                        sent_at ASC
                    """
                ),
                {
                    "thread_id": (
                        thread_id
                    ),
                },
            )
            .mappings()
            .all()
        )

        if mark_staff_messages_read:

            connection.execute(
                text(
                    """
                    UPDATE
                        public.messages

                    SET
                        read_at = now()

                    WHERE
                        thread_id = CAST(
                            :thread_id
                            AS uuid
                        )

                        AND sender_type <> 'Student'

                        AND read_at IS NULL
                    """
                ),
                {
                    "thread_id": (
                        thread_id
                    ),
                },
            )

    return {
        "thread": dict(
            thread
        ),

        "messages": [
            dict(
                message
            )
            for message in messages
        ],
    }


# ============================================================
# CREATE MESSAGE THREAD
# ============================================================

def create_student_message_thread(
    student_number: str,
    subject: str,
    category: str,
    message: str,
) -> dict:

    subject = clean_required_text(
        subject,
        "Subject",
    )

    message = clean_required_text(
        message,
        "Message",
    )

    registration = (
        get_student_current_registration(
            student_number
        )
    )

    ensure_messages_available(
        registration
    )

    with engine.begin() as connection:

        thread = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.message_threads (
                            registration_id,
                            student_number,
                            subject,
                            category,
                            status,
                            created_at,
                            updated_at
                        )

                    VALUES (
                        CAST(
                            :registration_id
                            AS uuid
                        ),
                        :student_number,
                        :subject,
                        :category,
                        'AwaitingStaff',
                        now(),
                        now()
                    )

                    RETURNING
                        id,
                        registration_id,
                        student_number,
                        subject,
                        category,
                        status,
                        created_at,
                        updated_at
                    """
                ),
                {
                    "registration_id": (
                        str(
                            registration[
                                "id"
                            ]
                        )
                    ),

                    "student_number": (
                        student_number
                    ),

                    "subject": (
                        subject
                    ),

                    "category": (
                        category
                    ),
                },
            )
            .mappings()
            .first()
        )

        first_message = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.messages (
                            thread_id,
                            sender_type,
                            sender_code,
                            message_body,
                            sent_at
                        )

                    VALUES (
                        CAST(
                            :thread_id
                            AS uuid
                        ),
                        'Student',
                        :student_number,
                        :message_body,
                        now()
                    )

                    RETURNING
                        id,
                        thread_id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at
                    """
                ),
                {
                    "thread_id": (
                        str(
                            thread[
                                "id"
                            ]
                        )
                    ),

                    "student_number": (
                        student_number
                    ),

                    "message_body": (
                        message
                    ),
                },
            )
            .mappings()
            .first()
        )

    return {
        "thread": dict(
            thread
        ),

        "message": dict(
            first_message
        ),
    }


# ============================================================
# REPLY TO THREAD
# ============================================================

def reply_to_student_message_thread(
    student_number: str,
    thread_id: str,
    message: str,
) -> dict:

    thread_id = validate_uuid(
        thread_id,
        "message thread ID",
    )

    message = clean_required_text(
        message,
        "Message",
    )

    registration = (
        get_student_current_registration(
            student_number
        )
    )

    ensure_messages_available(
        registration
    )

    with engine.begin() as connection:

        thread = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        status

                    FROM
                        public.message_threads

                    WHERE
                        id = CAST(
                            :thread_id
                            AS uuid
                        )

                        AND student_number =
                            :student_number

                        AND registration_id =
                            CAST(
                                :registration_id
                                AS uuid
                            )

                    FOR UPDATE
                    """
                ),
                {
                    "thread_id": (
                        thread_id
                    ),

                    "student_number": (
                        student_number
                    ),

                    "registration_id": (
                        str(
                            registration[
                                "id"
                            ]
                        )
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not thread:

            raise ValueError(
                "Message thread was not found."
            )

        if thread[
            "status"
        ] == "Closed":

            raise ValueError(
                
                    "This message thread is closed. "
                    "Please create a new query if "
                    "you still need assistance."
                
            )

        new_message = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.messages (
                            thread_id,
                            sender_type,
                            sender_code,
                            message_body,
                            sent_at
                        )

                    VALUES (
                        CAST(
                            :thread_id
                            AS uuid
                        ),
                        'Student',
                        :student_number,
                        :message_body,
                        now()
                    )

                    RETURNING
                        id,
                        thread_id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at
                    """
                ),
                {
                    "thread_id": (
                        thread_id
                    ),

                    "student_number": (
                        student_number
                    ),

                    "message_body": (
                        message
                    ),
                },
            )
            .mappings()
            .first()
        )

        connection.execute(
            text(
                """
                UPDATE
                    public.message_threads

                SET
                    status = 'AwaitingStaff',
                    updated_at = now(),
                    closed_at = null

                WHERE
                    id = CAST(
                        :thread_id
                        AS uuid
                    )
                """
            ),
            {
                "thread_id": (
                    thread_id
                ),
            },
        )

    return dict(
        new_message
    )