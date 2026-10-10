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


# ============================================================
# STUDENT ACCESS SCOPE
# ============================================================

def staff_can_access_student(
    *,
    staff_code: str,
    role_code: str,
    registration_id: str,
) -> bool:

    registration_id = validate_uuid(
        registration_id,
        "registration ID",
    )

    role_code = (
        role_code
        or ""
    ).strip().upper()

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if role_code == "ADMIN":

        return True

    # --------------------------------------------------------
    # FACILITATOR
    # --------------------------------------------------------

    if role_code == "FACILITATOR":

        with engine.connect() as connection:

            exists = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM public.class_enrolments ce

                        JOIN public.classes c
                            ON c.id = ce.class_id

                        WHERE
                            ce.registration_id
                                = CAST(
                                    :registration_id
                                    AS uuid
                                )

                            AND ce.status
                                = 'Active'

                            AND c.facilitator_code
                                = :staff_code

                        LIMIT 1
                        """
                    ),
                    {
                        "registration_id": (
                            registration_id
                        ),

                        "staff_code": (
                            staff_code
                        ),
                    },
                )
                .first()
            )

        return bool(
            exists
        )

    # --------------------------------------------------------
    # ASSESSOR
    # --------------------------------------------------------

    if role_code == "ASSESSOR":

        with engine.connect() as connection:

            exists = (
                connection.execute(
                    text(
                        """
                        SELECT 1

                        FROM public.class_enrolments ce

                        JOIN public.classes c
                            ON c.id = ce.class_id

                        WHERE
                            ce.registration_id
                                = CAST(
                                    :registration_id
                                    AS uuid
                                )

                            AND ce.status
                                = 'Active'

                            AND c.assessor_code
                                = :staff_code

                        LIMIT 1
                        """
                    ),
                    {
                        "registration_id": (
                            registration_id
                        ),

                        "staff_code": (
                            staff_code
                        ),
                    },
                )
                .first()
            )

        return bool(
            exists
        )

    # --------------------------------------------------------
    # OTHER ROLES
    # --------------------------------------------------------
    # We will expand this through the permission system later.
    # Do not automatically expose all learner communications.

    return False


# ============================================================
# FORMAT STUDENT MESSAGE THREAD
# ============================================================

def format_student_message_thread(
    row,
) -> dict:

    row = dict(
        row
    )

    return {
        "thread_id": str(
            row[
                "id"
            ]
        ),

        "registration_id": str(
            row[
                "registration_id"
            ]
        ),

        "student_number": (
            row[
                "student_number"
            ]
        ),

        "subject": (
            row[
                "subject"
            ]
        ),

        "category": (
            row[
                "category"
            ]
        ),

        "assigned_staff_code": (
            row[
                "assigned_staff_code"
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

        "closed_at": (
            row[
                "closed_at"
            ]
        ),

        "unread_count": (
            row.get(
                "unread_count",
                0,
            )
            or 0
        ),
    }


# ============================================================
# LIST STUDENT MESSAGE THREADS
# ============================================================

def get_staff_student_message_threads(
    *,
    staff_code: str,
    role_code: str,
) -> list[dict]:

    role_code = (
        role_code
        or ""
    ).strip().upper()

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if role_code == "ADMIN":

        scope_sql = """
            TRUE
        """

    # --------------------------------------------------------
    # FACILITATOR
    # --------------------------------------------------------

    elif role_code == "FACILITATOR":

        scope_sql = """
            EXISTS
            (
                SELECT 1

                FROM public.class_enrolments ce

                JOIN public.classes c
                    ON c.id = ce.class_id

                WHERE
                    ce.registration_id
                        = t.registration_id

                    AND ce.status
                        = 'Active'

                    AND c.facilitator_code
                        = :staff_code
            )
        """

    # --------------------------------------------------------
    # ASSESSOR
    # --------------------------------------------------------

    elif role_code == "ASSESSOR":

        scope_sql = """
            EXISTS
            (
                SELECT 1

                FROM public.class_enrolments ce

                JOIN public.classes c
                    ON c.id = ce.class_id

                WHERE
                    ce.registration_id
                        = t.registration_id

                    AND ce.status
                        = 'Active'

                    AND c.assessor_code
                        = :staff_code
            )
        """

    else:

        return []

    query = text(
        f"""
        SELECT
            t.id,
            t.registration_id,
            t.student_number,
            t.subject,
            t.category,
            t.assigned_staff_code,
            t.status,
            t.created_at,
            t.updated_at,
            t.closed_at,

            COUNT(
                m.id
            ) FILTER (
                WHERE
                    m.sender_type = 'Student'
                    AND m.read_at IS NULL
            ) AS unread_count

        FROM public.message_threads t

        LEFT JOIN public.messages m
            ON m.thread_id = t.id

        WHERE
            {scope_sql}

        GROUP BY
            t.id

        ORDER BY
            t.updated_at DESC
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
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
        format_student_message_thread(
            row
        )
        for row in rows
    ]


# ============================================================
# GET ONE STUDENT MESSAGE THREAD
# ============================================================

def get_staff_student_message_thread(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
) -> dict:

    thread_id = validate_uuid(
        thread_id,
        "thread ID",
    )

    with engine.connect() as connection:

        thread_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        registration_id,
                        student_number,
                        subject,
                        category,
                        assigned_staff_code,
                        status,
                        created_at,
                        updated_at,
                        closed_at

                    FROM public.message_threads

                    WHERE
                        id = CAST(
                            :thread_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "thread_id": (
                        thread_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not thread_row:

        raise ValueError(
            "Student message thread not found."
        )

    if not staff_can_access_student(
        staff_code=(
            staff_code
        ),
        role_code=(
            role_code
        ),
        registration_id=str(
            thread_row[
                "registration_id"
            ]
        ),
    ):

        raise ValueError(
            "You do not have access to "
            "this student's messages."
        )

    with engine.connect() as connection:

        message_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at

                    FROM public.messages

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

    result = (
        format_student_message_thread(
            thread_row
        )
    )

    result[
        "messages"
    ] = [
        {
            "message_id": str(
                row[
                    "id"
                ]
            ),

            "sender_type": (
                row[
                    "sender_type"
                ]
            ),

            "sender_code": (
                row[
                    "sender_code"
                ]
            ),

            "message_body": (
                row[
                    "message_body"
                ]
            ),

            "sent_at": (
                row[
                    "sent_at"
                ]
            ),

            "read_at": (
                row[
                    "read_at"
                ]
            ),

            "is_mine": (
                row[
                    "sender_type"
                ]
                == "Staff"

                and row[
                    "sender_code"
                ]
                == staff_code
            ),
        }
        for row in message_rows
    ]

    return result


# ============================================================
# REPLY TO STUDENT MESSAGE THREAD
# ============================================================

def reply_to_student_message_thread(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
    message_body: str,
) -> dict:

    message_body = (
        clean_required_text(
            message_body,
            "Message",
        )
    )

    current = (
        get_staff_student_message_thread(
            staff_code=(
                staff_code
            ),

            role_code=(
                role_code
            ),

            thread_id=(
                thread_id
            ),
        )
    )

    if (
        current[
            "status"
        ]
        == "Closed"
    ):

        raise ValueError(
            "This student message thread "
            "is closed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO public.messages
                (
                    thread_id,
                    sender_type,
                    sender_code,
                    message_body
                )

                VALUES
                (
                    CAST(
                        :thread_id
                        AS uuid
                    ),
                    'Staff',
                    :staff_code,
                    :message_body
                )
                """
            ),
            {
                "thread_id": (
                    thread_id
                ),

                "staff_code": (
                    staff_code
                ),

                "message_body": (
                    message_body
                ),
            },
        )

        connection.execute(
            text(
                """
                UPDATE public.message_threads

                SET
                    assigned_staff_code
                        = COALESCE(
                            assigned_staff_code,
                            :staff_code
                        ),

                    status = 'AwaitingStudent',

                    updated_at = now()

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

                "staff_code": (
                    staff_code
                ),
            },
        )

    return get_staff_student_message_thread(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        thread_id=(
            thread_id
        ),
    )


# ============================================================
# MARK STUDENT MESSAGES READ
# ============================================================

def mark_student_message_thread_read(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
) -> dict:

    get_staff_student_message_thread(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        thread_id=(
            thread_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.messages

                SET
                    read_at = COALESCE(
                        read_at,
                        now()
                    )

                WHERE
                    thread_id = CAST(
                        :thread_id
                        AS uuid
                    )

                    AND sender_type = 'Student'

                    AND read_at IS NULL
                """
            ),
            {
                "thread_id": (
                    thread_id
                ),
            },
        )

    return get_staff_student_message_thread(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        thread_id=(
            thread_id
        ),
    )


# ============================================================
# CLOSE STUDENT MESSAGE THREAD
# ============================================================

def close_student_message_thread(
    *,
    staff_code: str,
    role_code: str,
    thread_id: str,
) -> dict:

    get_staff_student_message_thread(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        thread_id=(
            thread_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.message_threads

                SET
                    status = 'Closed',
                    closed_at = now(),
                    updated_at = now()

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

    return get_staff_student_message_thread(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        thread_id=(
            thread_id
        ),
    )


# ============================================================
# FORMAT STUDENT SUPPORT TICKET
# ============================================================

def format_student_support_ticket(
    row,
) -> dict:

    row = dict(
        row
    )

    return {
        "ticket_id": str(
            row[
                "id"
            ]
        ),

        "ticket_number": (
            row[
                "ticket_number"
            ]
        ),

        "registration_id": str(
            row[
                "registration_id"
            ]
        ),

        "student_number": (
            row[
                "student_number"
            ]
        ),

        "category": (
            row[
                "category"
            ]
        ),

        "subject": (
            row[
                "subject"
            ]
        ),

        "description": (
            row[
                "description"
            ]
        ),

        "priority": (
            row[
                "priority"
            ]
        ),

        "status": (
            row[
                "status"
            ]
        ),

        "assigned_staff_code": (
            row[
                "assigned_staff_code"
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

        "resolved_at": (
            row[
                "resolved_at"
            ]
        ),

        "resolved_by": (
            row[
                "resolved_by"
            ]
        ),

        "resolution_notes": (
            row[
                "resolution_notes"
            ]
        ),

        "closed_at": (
            row[
                "closed_at"
            ]
        ),
    }


# ============================================================
# LIST STUDENT SUPPORT TICKETS
# ============================================================

def get_staff_student_support_tickets(
    *,
    staff_code: str,
    role_code: str,
) -> list[dict]:

    role_code = (
        role_code
        or ""
    ).strip().upper()

    if role_code == "ADMIN":

        scope_sql = "TRUE"

    elif role_code == "FACILITATOR":

        scope_sql = """
            EXISTS
            (
                SELECT 1

                FROM public.class_enrolments ce

                JOIN public.classes c
                    ON c.id = ce.class_id

                WHERE
                    ce.registration_id
                        = t.registration_id

                    AND ce.status = 'Active'

                    AND c.facilitator_code
                        = :staff_code
            )
        """

    elif role_code == "ASSESSOR":

        scope_sql = """
            EXISTS
            (
                SELECT 1

                FROM public.class_enrolments ce

                JOIN public.classes c
                    ON c.id = ce.class_id

                WHERE
                    ce.registration_id
                        = t.registration_id

                    AND ce.status = 'Active'

                    AND c.assessor_code
                        = :staff_code
            )
        """

    else:

        return []

    query = text(
        f"""
        SELECT
            t.id,
            t.ticket_number,
            t.registration_id,
            t.student_number,
            t.category,
            t.subject,
            t.description,
            t.priority,
            t.status,
            t.assigned_staff_code,
            t.created_at,
            t.updated_at,
            t.resolved_at,
            t.resolved_by,
            t.resolution_notes,
            t.closed_at

        FROM public.support_tickets t

        WHERE
            {scope_sql}

        ORDER BY
            t.updated_at DESC
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
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
        format_student_support_ticket(
            row
        )
        for row in rows
    ]


# ============================================================
# GET ONE STUDENT SUPPORT TICKET
# ============================================================

def get_staff_student_support_ticket(
    *,
    staff_code: str,
    role_code: str,
    ticket_id: str,
) -> dict:

    ticket_id = validate_uuid(
        ticket_id,
        "ticket ID",
    )

    with engine.connect() as connection:

        ticket_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        ticket_number,
                        registration_id,
                        student_number,
                        category,
                        subject,
                        description,
                        priority,
                        status,
                        assigned_staff_code,
                        created_at,
                        updated_at,
                        resolved_at,
                        resolved_by,
                        resolution_notes,
                        closed_at

                    FROM public.support_tickets

                    WHERE
                        id = CAST(
                            :ticket_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "ticket_id": (
                        ticket_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not ticket_row:

        raise ValueError(
            "Student support ticket not found."
        )

    if not staff_can_access_student(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        registration_id=str(
            ticket_row[
                "registration_id"
            ]
        ),
    ):

        raise ValueError(
            "You do not have access to "
            "this student's support ticket."
        )

    with engine.connect() as connection:

        message_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at

                    FROM
                        public.support_ticket_messages

                    WHERE
                        ticket_id = CAST(
                            :ticket_id
                            AS uuid
                        )

                    ORDER BY
                        sent_at ASC
                    """
                ),
                {
                    "ticket_id": (
                        ticket_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    result = (
        format_student_support_ticket(
            ticket_row
        )
    )

    result[
        "messages"
    ] = [
        {
            "message_id": str(
                row[
                    "id"
                ]
            ),

            "sender_type": (
                row[
                    "sender_type"
                ]
            ),

            "sender_code": (
                row[
                    "sender_code"
                ]
            ),

            "message_body": (
                row[
                    "message_body"
                ]
            ),

            "sent_at": (
                row[
                    "sent_at"
                ]
            ),

            "read_at": (
                row[
                    "read_at"
                ]
            ),

            "is_mine": (
                row[
                    "sender_type"
                ]
                == "Staff"

                and row[
                    "sender_code"
                ]
                == staff_code
            ),
        }
        for row in message_rows
    ]

    return result


# ============================================================
# REPLY TO STUDENT SUPPORT TICKET
# ============================================================

def reply_to_student_support_ticket(
    *,
    staff_code: str,
    role_code: str,
    ticket_id: str,
    message_body: str,
) -> dict:

    message_body = (
        clean_required_text(
            message_body,
            "Message",
        )
    )

    current = (
        get_staff_student_support_ticket(
            staff_code=(
                staff_code
            ),

            role_code=(
                role_code
            ),

            ticket_id=(
                ticket_id
            ),
        )
    )

    if (
        current[
            "status"
        ]
        == "Closed"
    ):

        raise ValueError(
            "This student support ticket "
            "is closed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO
                    public.support_ticket_messages
                (
                    ticket_id,
                    sender_type,
                    sender_code,
                    message_body
                )

                VALUES
                (
                    CAST(
                        :ticket_id
                        AS uuid
                    ),
                    'Staff',
                    :staff_code,
                    :message_body
                )
                """
            ),
            {
                "ticket_id": (
                    ticket_id
                ),

                "staff_code": (
                    staff_code
                ),

                "message_body": (
                    message_body
                ),
            },
        )

        connection.execute(
            text(
                """
                UPDATE public.support_tickets

                SET
                    assigned_staff_code
                        = COALESCE(
                            assigned_staff_code,
                            :staff_code
                        ),

                    status = 'AwaitingStudent',

                    updated_at = now()

                WHERE
                    id = CAST(
                        :ticket_id
                        AS uuid
                    )
                """
            ),
            {
                "ticket_id": (
                    ticket_id
                ),

                "staff_code": (
                    staff_code
                ),
            },
        )

    return get_staff_student_support_ticket(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        ticket_id=(
            ticket_id
        ),
    )


# ============================================================
# MARK STUDENT SUPPORT READ
# ============================================================

def mark_student_support_ticket_read(
    *,
    staff_code: str,
    role_code: str,
    ticket_id: str,
) -> dict:

    get_staff_student_support_ticket(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        ticket_id=(
            ticket_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.support_ticket_messages

                SET
                    read_at = COALESCE(
                        read_at,
                        now()
                    )

                WHERE
                    ticket_id = CAST(
                        :ticket_id
                        AS uuid
                    )

                    AND sender_type = 'Student'

                    AND read_at IS NULL
                """
            ),
            {
                "ticket_id": (
                    ticket_id
                ),
            },
        )

    return get_staff_student_support_ticket(
        staff_code=(
            staff_code
        ),

        role_code=(
            role_code
        ),

        ticket_id=(
            ticket_id
        ),
    )