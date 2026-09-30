from uuid import UUID

from sqlalchemy import text

from app.database import engine
from app.services.staff_notification_service import (
    create_staff_notification,
)


ACADEMIC_SCOPED_ROLES = {
    "FACILITATOR",
    "ASSESSOR",
}

ANNOUNCEMENT_TYPES = {
    "General",
    "Academic",
    "Assessment",
    "Timetable",
    "Finance",
    "Documents",
    "Emergency",
}

ANNOUNCEMENT_PRIORITIES = {
    "Normal",
    "Important",
    "Urgent",
}

ANNOUNCEMENT_AUDIENCES = {
    "AllStudents",
    "Course",
    "Cycle",
    "Class",
    "IndividualStudent",
}


def _clean_staff_code(
    value: str,
) -> str:
    value = str(
        value
        or ""
    ).strip().upper()

    if not value:
        raise ValueError(
            "Staff code is required."
        )

    return value


def _clean_text(
    value: str,
    field_name: str,
) -> str:
    value = str(
        value
        or ""
    ).strip()

    if not value:
        raise ValueError(
            f"{field_name} is required."
        )

    return value


def _clean_uuid(
    value: str,
    field_name: str,
) -> str:
    value = str(
        value
        or ""
    ).strip()

    try:
        UUID(
            value
        )
    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as error:
        raise ValueError(
            f"Invalid {field_name}."
        ) from error

    return value


def _notify_staff(
    *,
    recipient_staff_code: str,
    notification_type: str,
    title: str,
    message: str,
    action_url: str | None,
    created_by_staff_code: str,
    metadata: dict | None = None,
) -> None:
    try:
        create_staff_notification(
            recipient_staff_code=(
                recipient_staff_code
            ),
            notification_type=(
                notification_type
            ),
            title=title,
            message=message,
            priority="Normal",
            action_url=action_url,
            metadata=(
                metadata
                or {}
            ),
            show_desktop_popup=True,
            created_by_staff_code=(
                created_by_staff_code
            ),
        )
    except Exception as error:
        print(
            "WARNING: Communication action "
            "succeeded but staff notification "
            "could not be created: "
            f"{error}"
        )


# ============================================================
# INTERNAL STAFF DIRECTORY
# ============================================================

def get_staff_message_directory(
    *,
    staff_code: str,
) -> list[dict]:
    staff_code = _clean_staff_code(
        staff_code
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    sa.staff_code,
                    sa.role_code,
                    e.employee_number,
                    e.first_name,
                    e.middle_name,
                    e.last_name,
                    e.job_title,
                    e.department
                FROM public.staff_accounts sa
                JOIN public.employees e
                    ON e.id = sa.employee_id
                WHERE sa.is_active = TRUE
                  AND sa.staff_code <> :staff_code
                ORDER BY
                    e.last_name,
                    e.first_name,
                    sa.staff_code
            """),
            {
                "staff_code": staff_code
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# STAFF-TO-STAFF MESSAGING
# ============================================================

def create_staff_message_thread(
    *,
    sender_staff_code: str,
    recipient_staff_code: str,
    subject: str,
    category: str,
    message_body: str,
) -> dict:
    sender_staff_code = _clean_staff_code(
        sender_staff_code
    )
    recipient_staff_code = _clean_staff_code(
        recipient_staff_code
    )
    subject = _clean_text(
        subject,
        "Subject",
    )
    category = _clean_text(
        category,
        "Category",
    )
    message_body = _clean_text(
        message_body,
        "Message",
    )

    if (
        sender_staff_code
        == recipient_staff_code
    ):
        raise ValueError(
            "You cannot start a staff "
            "message thread with yourself."
        )

    with engine.begin() as connection:
        recipient = connection.execute(
            text("""
                SELECT
                    staff_code
                FROM public.staff_accounts
                WHERE staff_code = :staff_code
                  AND is_active = TRUE
                LIMIT 1
            """),
            {
                "staff_code": (
                    recipient_staff_code
                )
            },
        ).first()

        if not recipient:
            raise ValueError(
                "Recipient staff account "
                "was not found or is inactive."
            )

        thread = connection.execute(
            text("""
                INSERT INTO public.staff_message_threads (
                    sender_staff_code,
                    recipient_staff_code,
                    subject,
                    category,
                    status
                )
                VALUES (
                    :sender_staff_code,
                    :recipient_staff_code,
                    :subject,
                    :category,
                    'Open'
                )
                RETURNING *
            """),
            {
                "sender_staff_code": (
                    sender_staff_code
                ),
                "recipient_staff_code": (
                    recipient_staff_code
                ),
                "subject": subject,
                "category": category,
            },
        ).mappings().first()

        connection.execute(
            text("""
                INSERT INTO public.staff_messages (
                    thread_id,
                    sender_staff_code,
                    message_body
                )
                VALUES (
                    :thread_id,
                    :sender_staff_code,
                    :message_body
                )
            """),
            {
                "thread_id": thread["id"],
                "sender_staff_code": (
                    sender_staff_code
                ),
                "message_body": message_body,
            },
        )

    _notify_staff(
        recipient_staff_code=(
            recipient_staff_code
        ),
        notification_type=(
            "STAFF_MESSAGE"
        ),
        title=(
            "New staff message"
        ),
        message=subject,
        action_url=(
            f"/staff/messages/{thread['id']}"
        ),
        created_by_staff_code=(
            sender_staff_code
        ),
        metadata={
            "thread_id": str(
                thread["id"]
            ),
        },
    )

    return dict(
        thread
    )


def get_staff_message_threads(
    *,
    staff_code: str,
) -> list[dict]:
    staff_code = _clean_staff_code(
        staff_code
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    t.*,

                    CASE
                        WHEN t.sender_staff_code =
                             :staff_code
                        THEN t.recipient_staff_code
                        ELSE t.sender_staff_code
                    END AS other_staff_code,

                    (
                        SELECT sm.message_body
                        FROM public.staff_messages sm
                        WHERE sm.thread_id = t.id
                        ORDER BY sm.sent_at DESC
                        LIMIT 1
                    ) AS last_message,

                    (
                        SELECT sm.sent_at
                        FROM public.staff_messages sm
                        WHERE sm.thread_id = t.id
                        ORDER BY sm.sent_at DESC
                        LIMIT 1
                    ) AS last_message_at,

                    (
                        SELECT COUNT(*)
                        FROM public.staff_messages sm
                        WHERE sm.thread_id = t.id
                          AND sm.sender_staff_code <>
                              :staff_code
                          AND sm.read_at IS NULL
                    ) AS unread_count

                FROM public.staff_message_threads t
                WHERE
                    t.sender_staff_code = :staff_code
                    OR t.recipient_staff_code =
                       :staff_code
                ORDER BY
                    COALESCE(
                        (
                            SELECT MAX(sm2.sent_at)
                            FROM public.staff_messages sm2
                            WHERE sm2.thread_id = t.id
                        ),
                        t.updated_at
                    ) DESC
            """),
            {
                "staff_code": staff_code
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_staff_message_thread(
    *,
    staff_code: str,
    thread_id: str,
) -> dict | None:
    staff_code = _clean_staff_code(
        staff_code
    )
    thread_id = _clean_uuid(
        thread_id,
        "thread ID",
    )

    with engine.begin() as connection:
        thread = connection.execute(
            text("""
                SELECT *
                FROM public.staff_message_threads
                WHERE id = CAST(
                    :thread_id
                    AS uuid
                )
                  AND (
                        sender_staff_code =
                            :staff_code
                        OR recipient_staff_code =
                            :staff_code
                  )
                LIMIT 1
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).mappings().first()

        if not thread:
            return None

        connection.execute(
            text("""
                UPDATE public.staff_messages
                SET read_at = COALESCE(
                    read_at,
                    NOW()
                )
                WHERE thread_id = CAST(
                    :thread_id
                    AS uuid
                )
                  AND sender_staff_code <>
                      :staff_code
                  AND read_at IS NULL
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        )

        messages = connection.execute(
            text("""
                SELECT
                    id,
                    thread_id,
                    sender_staff_code,
                    message_body,
                    sent_at,
                    read_at
                FROM public.staff_messages
                WHERE thread_id = CAST(
                    :thread_id
                    AS uuid
                )
                ORDER BY sent_at
            """),
            {
                "thread_id": thread_id
            },
        ).mappings().all()

    return {
        "thread": dict(
            thread
        ),
        "messages": [
            dict(
                row
            )
            for row in messages
        ],
    }


def reply_to_staff_message_thread(
    *,
    staff_code: str,
    thread_id: str,
    message_body: str,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )
    thread_id = _clean_uuid(
        thread_id,
        "thread ID",
    )
    message_body = _clean_text(
        message_body,
        "Message",
    )

    with engine.begin() as connection:
        thread = connection.execute(
            text("""
                SELECT *
                FROM public.staff_message_threads
                WHERE id = CAST(
                    :thread_id
                    AS uuid
                )
                  AND (
                        sender_staff_code =
                            :staff_code
                        OR recipient_staff_code =
                            :staff_code
                  )
                LIMIT 1
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).mappings().first()

        if not thread:
            raise ValueError(
                "Staff message thread "
                "was not found."
            )

        if (
            str(
                thread["status"]
            ).strip().lower()
            == "closed"
        ):
            raise ValueError(
                "This staff message "
                "thread is closed."
            )

        message = connection.execute(
            text("""
                INSERT INTO public.staff_messages (
                    thread_id,
                    sender_staff_code,
                    message_body
                )
                VALUES (
                    CAST(
                        :thread_id
                        AS uuid
                    ),
                    :staff_code,
                    :message_body
                )
                RETURNING *
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
                "message_body": message_body,
            },
        ).mappings().first()

        connection.execute(
            text("""
                UPDATE public.staff_message_threads
                SET updated_at = NOW()
                WHERE id = CAST(
                    :thread_id
                    AS uuid
                )
            """),
            {
                "thread_id": thread_id
            },
        )

    if (
        thread["sender_staff_code"]
        == staff_code
    ):
        recipient_staff_code = (
            thread[
                "recipient_staff_code"
            ]
        )
    else:
        recipient_staff_code = (
            thread[
                "sender_staff_code"
            ]
        )

    _notify_staff(
        recipient_staff_code=(
            recipient_staff_code
        ),
        notification_type=(
            "STAFF_MESSAGE_REPLY"
        ),
        title=(
            "Staff message reply"
        ),
        message=str(
            thread["subject"]
        ),
        action_url=(
            f"/staff/messages/{thread_id}"
        ),
        created_by_staff_code=(
            staff_code
        ),
        metadata={
            "thread_id": thread_id,
        },
    )

    return dict(
        message
    )


def close_staff_message_thread(
    *,
    staff_code: str,
    thread_id: str,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )
    thread_id = _clean_uuid(
        thread_id,
        "thread ID",
    )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                UPDATE public.staff_message_threads
                SET
                    status = 'Closed',
                    closed_at = COALESCE(
                        closed_at,
                        NOW()
                    ),
                    updated_at = NOW()
                WHERE id = CAST(
                    :thread_id
                    AS uuid
                )
                  AND (
                        sender_staff_code =
                            :staff_code
                        OR recipient_staff_code =
                            :staff_code
                  )
                RETURNING *
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "Staff message thread "
            "was not found."
        )

    return dict(
        row
    )


# ============================================================
# STUDENT MESSAGE SCOPE
# ============================================================

def _student_thread_scope_sql(
    *,
    role_code: str,
) -> str:
    role_code = str(
        role_code
        or ""
    ).strip().upper()

    if role_code not in ACADEMIC_SCOPED_ROLES:
        return "TRUE"

    return """
        (
            mt.assigned_staff_code =
                :staff_code
            OR (
                mt.assigned_staff_code IS NULL
                AND EXISTS (
                    SELECT 1
                    FROM public.class_enrolments ce
                    JOIN public.classes c
                        ON c.id = ce.class_id
                    WHERE
                        ce.registration_id =
                            mt.registration_id
                        AND ce.status = 'Active'
                        AND (
                            c.facilitator_code =
                                :staff_code
                            OR c.assessor_code =
                                :staff_code
                        )
                )
            )
        )
    """


def get_staff_student_message_threads(
    *,
    staff_code: str,
    role_code: str,
) -> list[dict]:
    staff_code = _clean_staff_code(
        staff_code
    )

    scope_sql = _student_thread_scope_sql(
        role_code=role_code
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(f"""
                SELECT
                    mt.id,
                    mt.student_number,
                    mt.registration_id,
                    mt.subject,
                    mt.category,
                    mt.assigned_staff_code,
                    mt.status,
                    mt.created_at,
                    mt.updated_at,
                    mt.closed_at,

                    a.first_name,
                    a.middle_name,
                    a.last_name,

                    (
                        SELECT m.message_body
                        FROM public.messages m
                        WHERE m.thread_id = mt.id
                        ORDER BY m.sent_at DESC
                        LIMIT 1
                    ) AS last_message,

                    (
                        SELECT m.sent_at
                        FROM public.messages m
                        WHERE m.thread_id = mt.id
                        ORDER BY m.sent_at DESC
                        LIMIT 1
                    ) AS last_message_at,

                    (
                        SELECT COUNT(*)
                        FROM public.messages m
                        WHERE m.thread_id = mt.id
                          AND m.sender_type = 'Student'
                          AND m.read_at IS NULL
                    ) AS unread_student_messages

                FROM public.message_threads mt
                JOIN public.applications a
                    ON a.student_number =
                       mt.student_number
                WHERE {scope_sql}
                ORDER BY
                    COALESCE(
                        (
                            SELECT MAX(m2.sent_at)
                            FROM public.messages m2
                            WHERE m2.thread_id =
                                  mt.id
                        ),
                        mt.updated_at
                    ) DESC
            """),
            {
                "staff_code": staff_code
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_staff_student_message_thread(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
) -> dict | None:
    staff_code = _clean_staff_code(
        staff_code
    )
    thread_id = _clean_uuid(
        thread_id,
        "thread ID",
    )

    scope_sql = _student_thread_scope_sql(
        role_code=role_code
    )

    with engine.begin() as connection:
        thread = connection.execute(
            text(f"""
                SELECT
                    mt.*,
                    a.first_name,
                    a.middle_name,
                    a.last_name
                FROM public.message_threads mt
                JOIN public.applications a
                    ON a.student_number =
                       mt.student_number
                WHERE
                    mt.id = CAST(
                        :thread_id
                        AS uuid
                    )
                    AND {scope_sql}
                LIMIT 1
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).mappings().first()

        if not thread:
            return None

        connection.execute(
            text("""
                UPDATE public.messages
                SET read_at = COALESCE(
                    read_at,
                    NOW()
                )
                WHERE thread_id = CAST(
                    :thread_id
                    AS uuid
                )
                  AND sender_type = 'Student'
                  AND read_at IS NULL
            """),
            {
                "thread_id": thread_id
            },
        )

        messages = connection.execute(
            text("""
                SELECT
                    id,
                    thread_id,
                    sender_type,
                    sender_code,
                    message_body,
                    sent_at,
                    read_at
                FROM public.messages
                WHERE thread_id = CAST(
                    :thread_id
                    AS uuid
                )
                ORDER BY sent_at
            """),
            {
                "thread_id": thread_id
            },
        ).mappings().all()

    return {
        "thread": dict(
            thread
        ),
        "messages": [
            dict(
                row
            )
            for row in messages
        ],
    }


def reply_to_student_message_thread(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
    message_body: str,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )
    thread_id = _clean_uuid(
        thread_id,
        "thread ID",
    )
    message_body = _clean_text(
        message_body,
        "Message",
    )

    scope_sql = _student_thread_scope_sql(
        role_code=role_code
    )

    with engine.begin() as connection:
        thread = connection.execute(
            text(f"""
                SELECT mt.*
                FROM public.message_threads mt
                WHERE
                    mt.id = CAST(
                        :thread_id
                        AS uuid
                    )
                    AND {scope_sql}
                LIMIT 1
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).mappings().first()

        if not thread:
            raise ValueError(
                "Student message thread "
                "was not found or is outside "
                "your permitted learner scope."
            )

        if (
            str(
                thread["status"]
            ).strip()
            in {
                "Resolved",
                "Closed",
            }
        ):
            raise ValueError(
                "This student message "
                "thread is closed."
            )

        message = connection.execute(
            text("""
                INSERT INTO public.messages (
                    thread_id,
                    sender_type,
                    sender_code,
                    message_body
                )
                VALUES (
                    CAST(
                        :thread_id
                        AS uuid
                    ),
                    'Staff',
                    :staff_code,
                    :message_body
                )
                RETURNING *
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
                "message_body": message_body,
            },
        ).mappings().first()

        connection.execute(
            text("""
                UPDATE public.message_threads
                SET
                    assigned_staff_code =
                        COALESCE(
                            assigned_staff_code,
                            :staff_code
                        ),
                    status = 'AwaitingStudent',
                    updated_at = NOW()
                WHERE id = CAST(
                    :thread_id
                    AS uuid
                )
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        )

    return dict(
        message
    )


def resolve_student_message_thread(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )
    thread_id = _clean_uuid(
        thread_id,
        "thread ID",
    )

    scope_sql = _student_thread_scope_sql(
        role_code=role_code
    )

    with engine.begin() as connection:
        allowed = connection.execute(
            text(f"""
                SELECT mt.id
                FROM public.message_threads mt
                WHERE
                    mt.id = CAST(
                        :thread_id
                        AS uuid
                    )
                    AND {scope_sql}
                LIMIT 1
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).first()

        if not allowed:
            raise ValueError(
                "Student message thread "
                "was not found or is outside "
                "your permitted learner scope."
            )

        row = connection.execute(
            text("""
                UPDATE public.message_threads
                SET
                    assigned_staff_code =
                        COALESCE(
                            assigned_staff_code,
                            :staff_code
                        ),
                    status = 'Resolved',
                    closed_at = COALESCE(
                        closed_at,
                        NOW()
                    ),
                    updated_at = NOW()
                WHERE id = CAST(
                    :thread_id
                    AS uuid
                )
                RETURNING *
            """),
            {
                "thread_id": thread_id,
                "staff_code": staff_code,
            },
        ).mappings().first()

    return dict(
        row
    )


# ============================================================
# ANNOUNCEMENTS
# ============================================================

def _validate_announcement_scope(
    *,
    staff_code: str,
    role_code: str,
    audience_type: str,
    course_code: str | None,
    cycle_code: str | None,
    class_id: str | None,
    student_number: str | None,
) -> None:
    role_code = str(
        role_code
        or ""
    ).strip().upper()

    if (
        role_code
        not in ACADEMIC_SCOPED_ROLES
    ):
        return

    if audience_type == "AllStudents":
        raise ValueError(
            "Facilitators and Assessors "
            "cannot create an All Students "
            "announcement."
        )

    with engine.connect() as connection:
        if audience_type == "Class":
            if not class_id:
                raise ValueError(
                    "Class ID is required for "
                    "a Class announcement."
                )

            class_id = _clean_uuid(
                class_id,
                "class ID",
            )

            allowed = connection.execute(
                text("""
                    SELECT 1
                    FROM public.classes
                    WHERE id = CAST(
                        :class_id
                        AS uuid
                    )
                      AND (
                            facilitator_code =
                                :staff_code
                            OR assessor_code =
                                :staff_code
                      )
                    LIMIT 1
                """),
                {
                    "class_id": class_id,
                    "staff_code": staff_code,
                },
            ).first()

        elif audience_type == "Course":
            course_code = _clean_text(
                course_code,
                "Course code",
            )

            allowed = connection.execute(
                text("""
                    SELECT 1
                    FROM public.classes
                    WHERE course_code =
                          :course_code
                      AND (
                            facilitator_code =
                                :staff_code
                            OR assessor_code =
                                :staff_code
                      )
                    LIMIT 1
                """),
                {
                    "course_code": course_code,
                    "staff_code": staff_code,
                },
            ).first()

        elif audience_type == "Cycle":
            cycle_code = _clean_text(
                cycle_code,
                "Cycle code",
            )

            allowed = connection.execute(
                text("""
                    SELECT 1
                    FROM public.classes
                    WHERE cycle_code =
                          :cycle_code
                      AND (
                            facilitator_code =
                                :staff_code
                            OR assessor_code =
                                :staff_code
                      )
                    LIMIT 1
                """),
                {
                    "cycle_code": cycle_code,
                    "staff_code": staff_code,
                },
            ).first()

        elif (
            audience_type
            == "IndividualStudent"
        ):
            student_number = _clean_text(
                student_number,
                "Student number",
            )

            allowed = connection.execute(
                text("""
                    SELECT 1
                    FROM public.registrations r
                    JOIN public.class_enrolments ce
                        ON ce.registration_id =
                           r.id
                    JOIN public.classes c
                        ON c.id = ce.class_id
                    WHERE
                        r.student_number =
                            :student_number
                        AND ce.status = 'Active'
                        AND (
                            c.facilitator_code =
                                :staff_code
                            OR c.assessor_code =
                                :staff_code
                        )
                    LIMIT 1
                """),
                {
                    "student_number": (
                        student_number
                    ),
                    "staff_code": staff_code,
                },
            ).first()

        else:
            allowed = None

    if not allowed:
        raise ValueError(
            "The selected announcement "
            "audience is outside your "
            "assigned academic scope."
        )


def get_staff_announcements(
    *,
    staff_code: str,
    role_code: str,
) -> list[dict]:
    staff_code = _clean_staff_code(
        staff_code
    )
    role_code = str(
        role_code
        or ""
    ).strip().upper()

    params = {
        "staff_code": staff_code
    }

    if (
        role_code
        in ACADEMIC_SCOPED_ROLES
    ):
        scope_sql = """
            (
                an.created_by_staff_code =
                    :staff_code

                OR an.audience_type =
                    'AllStudents'

                OR (
                    an.audience_type = 'Class'
                    AND EXISTS (
                        SELECT 1
                        FROM public.classes c
                        WHERE c.id = an.class_id
                          AND (
                                c.facilitator_code =
                                    :staff_code
                                OR c.assessor_code =
                                    :staff_code
                          )
                    )
                )

                OR (
                    an.audience_type = 'Course'
                    AND EXISTS (
                        SELECT 1
                        FROM public.classes c
                        WHERE c.course_code =
                              an.course_code
                          AND (
                                c.facilitator_code =
                                    :staff_code
                                OR c.assessor_code =
                                    :staff_code
                          )
                    )
                )

                OR (
                    an.audience_type = 'Cycle'
                    AND EXISTS (
                        SELECT 1
                        FROM public.classes c
                        WHERE c.cycle_code =
                              an.cycle_code
                          AND (
                                c.facilitator_code =
                                    :staff_code
                                OR c.assessor_code =
                                    :staff_code
                          )
                    )
                )

                OR (
                    an.audience_type =
                        'IndividualStudent'
                    AND EXISTS (
                        SELECT 1
                        FROM public.registrations r
                        JOIN public.class_enrolments ce
                            ON ce.registration_id =
                               r.id
                        JOIN public.classes c
                            ON c.id = ce.class_id
                        WHERE
                            r.student_number =
                                an.student_number
                            AND ce.status = 'Active'
                            AND (
                                c.facilitator_code =
                                    :staff_code
                                OR c.assessor_code =
                                    :staff_code
                            )
                    )
                )
            )
        """
    else:
        scope_sql = "TRUE"

    with engine.connect() as connection:
        rows = connection.execute(
            text(f"""
                SELECT
                    an.*
                FROM public.announcements an
                WHERE {scope_sql}
                ORDER BY
                    an.created_at DESC
            """),
            params,
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def create_staff_announcement(
    *,
    staff_code: str,
    role_code: str,
    title: str,
    message: str,
    announcement_type: str,
    priority: str,
    audience_type: str,
    course_code: str | None = None,
    cycle_code: str | None = None,
    class_id: str | None = None,
    student_number: str | None = None,
    expires_at=None,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )
    title = _clean_text(
        title,
        "Title",
    )
    message = _clean_text(
        message,
        "Message",
    )

    announcement_type = str(
        announcement_type
        or "General"
    ).strip()

    priority = str(
        priority
        or "Normal"
    ).strip()

    audience_type = str(
        audience_type
        or "AllStudents"
    ).strip()

    if (
        announcement_type
        not in ANNOUNCEMENT_TYPES
    ):
        raise ValueError(
            "Invalid announcement type."
        )

    if (
        priority
        not in ANNOUNCEMENT_PRIORITIES
    ):
        raise ValueError(
            "Invalid announcement priority."
        )

    if (
        audience_type
        not in ANNOUNCEMENT_AUDIENCES
    ):
        raise ValueError(
            "Invalid announcement audience."
        )

    if audience_type == "Course":
        course_code = _clean_text(
            course_code,
            "Course code",
        )
    elif audience_type == "Cycle":
        cycle_code = _clean_text(
            cycle_code,
            "Cycle code",
        )
    elif audience_type == "Class":
        class_id = _clean_uuid(
            class_id,
            "class ID",
        )
    elif (
        audience_type
        == "IndividualStudent"
    ):
        student_number = _clean_text(
            student_number,
            "Student number",
        )

    _validate_announcement_scope(
        staff_code=staff_code,
        role_code=role_code,
        audience_type=audience_type,
        course_code=course_code,
        cycle_code=cycle_code,
        class_id=class_id,
        student_number=student_number,
    )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                INSERT INTO public.announcements (
                    title,
                    message,
                    announcement_type,
                    priority,
                    audience_type,
                    course_code,
                    cycle_code,
                    class_id,
                    student_number,
                    expires_at,
                    status,
                    created_by_staff_code
                )
                VALUES (
                    :title,
                    :message,
                    :announcement_type,
                    :priority,
                    :audience_type,
                    :course_code,
                    :cycle_code,
                    CASE
                        WHEN :class_id IS NULL
                        THEN NULL
                        ELSE CAST(
                            :class_id
                            AS uuid
                        )
                    END,
                    :student_number,
                    :expires_at,
                    'Draft',
                    :staff_code
                )
                RETURNING *
            """),
            {
                "title": title,
                "message": message,
                "announcement_type": (
                    announcement_type
                ),
                "priority": priority,
                "audience_type": (
                    audience_type
                ),
                "course_code": course_code,
                "cycle_code": cycle_code,
                "class_id": class_id,
                "student_number": (
                    student_number
                ),
                "expires_at": expires_at,
                "staff_code": staff_code,
            },
        ).mappings().first()

    return dict(
        row
    )


def publish_staff_announcement(
    *,
    staff_code: str,
    announcement_id: str,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )
    announcement_id = _clean_uuid(
        announcement_id,
        "announcement ID",
    )

    with engine.begin() as connection:
        row = connection.execute(
            text("""
                UPDATE public.announcements
                SET
                    status = 'Published',
                    published_by =
                        :staff_code,
                    published_at = NOW(),
                    updated_at = NOW()
                WHERE id = CAST(
                    :announcement_id
                    AS uuid
                )
                  AND status = 'Draft'
                RETURNING *
            """),
            {
                "announcement_id": (
                    announcement_id
                ),
                "staff_code": staff_code,
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "Announcement was not found "
            "or is not in Draft status."
        )

    return dict(
        row
    )

