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
# VALIDATE ACTIVE STAFF
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
# GENERATE TICKET NUMBER
# ============================================================

def generate_staff_ticket_number() -> str:

    now = datetime.now(
        timezone.utc
    )

    prefix = (
        f"STF-{now.year}-"
    )

    with engine.connect() as connection:

        count = (
            connection.execute(
                text(
                    """
                    SELECT
                        COUNT(*)

                    FROM
                        public.staff_support_tickets

                    WHERE
                        ticket_number
                        LIKE :prefix
                    """
                ),
                {
                    "prefix": (
                        f"{prefix}%"
                    ),
                },
            )
            .scalar_one()
        )

    sequence_number = (
        int(
            count
        )
        + 1
    )

    return (
        f"{prefix}"
        f"{sequence_number:05d}"
    )


# ============================================================
# FORMAT SUPPORT TICKET
# ============================================================

def format_support_ticket(
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

        "created_by_staff_code": (
            row[
                "created_by_staff_code"
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

        "unread_count": (
            row.get(
                "unread_count",
                0,
            )
            or 0
        ),
    }


# ============================================================
# CREATE SUPPORT TICKET
# ============================================================

def create_staff_support_ticket(
    *,
    staff_code: str,
    category: str,
    subject: str,
    description: str,
    priority: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    category = clean_required_text(
        category,
        "Category",
    )

    subject = clean_required_text(
        subject,
        "Subject",
    )

    description = clean_required_text(
        description,
        "Description",
    )

    priority = clean_required_text(
        priority,
        "Priority",
    )

    validate_active_staff(
        staff_code
    )

    # Retry in the unlikely event that two
    # tickets are created at the same time.
    for _ in range(
        3
    ):

        ticket_number = (
            generate_staff_ticket_number()
        )

        try:

            with engine.begin() as connection:

                ticket_id = (
                    connection.execute(
                        text(
                            """
                            INSERT INTO
                                public.staff_support_tickets
                            (
                                ticket_number,
                                created_by_staff_code,
                                category,
                                subject,
                                description,
                                priority,
                                status
                            )

                            VALUES
                            (
                                :ticket_number,
                                :staff_code,
                                :category,
                                :subject,
                                :description,
                                :priority,
                                'Open'
                            )

                            RETURNING id
                            """
                        ),
                        {
                            "ticket_number": (
                                ticket_number
                            ),

                            "staff_code": (
                                staff_code
                            ),

                            "category": (
                                category
                            ),

                            "subject": (
                                subject
                            ),

                            "description": (
                                description
                            ),

                            "priority": (
                                priority
                            ),
                        },
                    )
                    .scalar_one()
                )

            return (
                get_staff_support_ticket(
                    staff_code=(
                        staff_code
                    ),

                    ticket_id=str(
                        ticket_id
                    ),
                )
            )

        except Exception as error:

            if (
                "ticket_number"
                not in str(
                    error
                ).lower()
            ):

                raise

    raise RuntimeError(
        "A unique support ticket number "
        "could not be generated."
    )


# ============================================================
# LIST SUPPORT TICKETS
# ============================================================

def get_staff_support_tickets(
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
                        t.id,
                        t.ticket_number,
                        t.created_by_staff_code,
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
                        t.closed_at,

                        COUNT(
                            m.id
                        ) FILTER (
                            WHERE
                                m.sender_staff_code
                                    <> :staff_code

                                AND m.read_at
                                    IS NULL
                        ) AS unread_count

                    FROM
                        public.staff_support_tickets t

                    LEFT JOIN
                        public.staff_support_ticket_messages m
                    ON
                        m.ticket_id = t.id

                    WHERE
                        t.created_by_staff_code
                            = :staff_code

                        OR

                        t.assigned_staff_code
                            = :staff_code

                    GROUP BY
                        t.id

                    ORDER BY
                        t.updated_at DESC
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
        format_support_ticket(
            row
        )
        for row in rows
    ]


# ============================================================
# GET ONE SUPPORT TICKET
# ============================================================

def get_staff_support_ticket(
    *,
    staff_code: str,
    ticket_id: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

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
                        created_by_staff_code,
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

                    FROM
                        public.staff_support_tickets

                    WHERE
                        id = CAST(
                            :ticket_id
                            AS uuid
                        )

                        AND
                        (
                            created_by_staff_code
                                = :staff_code

                            OR

                            assigned_staff_code
                                = :staff_code
                        )

                    LIMIT 1
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
            .mappings()
            .first()
        )

        if not ticket_row:

            raise ValueError(
                "Support ticket not found."
            )

        message_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        sender_staff_code,
                        message_body,
                        sent_at,
                        read_at

                    FROM
                        public.staff_support_ticket_messages

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

    ticket = (
        format_support_ticket(
            ticket_row
        )
    )

    ticket[
        "messages"
    ] = [
        {
            "message_id": str(
                row[
                    "id"
                ]
            ),

            "sender_staff_code": (
                row[
                    "sender_staff_code"
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
                    "sender_staff_code"
                ]
                == staff_code
            ),
        }
        for row in message_rows
    ]

    return ticket


# ============================================================
# REPLY TO SUPPORT TICKET
# ============================================================

def reply_to_staff_support_ticket(
    *,
    staff_code: str,
    ticket_id: str,
    message_body: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    ticket_id = validate_uuid(
        ticket_id,
        "ticket ID",
    )

    message_body = clean_required_text(
        message_body,
        "Message",
    )

    current_ticket = (
        get_staff_support_ticket(
            staff_code=(
                staff_code
            ),

            ticket_id=(
                ticket_id
            ),
        )
    )

    if (
        current_ticket[
            "status"
        ]
        == "Closed"
    ):

        raise ValueError(
            "This support ticket is closed."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO
                    public.staff_support_ticket_messages
                (
                    ticket_id,
                    sender_staff_code,
                    message_body
                )

                VALUES
                (
                    CAST(
                        :ticket_id
                        AS uuid
                    ),

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

        new_status = (
            "AwaitingStaff"
            if current_ticket[
                "created_by_staff_code"
            ]
            == staff_code
            else "InProgress"
        )

        connection.execute(
            text(
                """
                UPDATE
                    public.staff_support_tickets

                SET
                    status = :status,
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

                "status": (
                    new_status
                ),
            },
        )

    return get_staff_support_ticket(
        staff_code=(
            staff_code
        ),

        ticket_id=(
            ticket_id
        ),
    )


# ============================================================
# MARK SUPPORT TICKET AS READ
# ============================================================

def mark_staff_support_ticket_read(
    *,
    staff_code: str,
    ticket_id: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    ticket_id = validate_uuid(
        ticket_id,
        "ticket ID",
    )

    get_staff_support_ticket(
        staff_code=(
            staff_code
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
                    public.staff_support_ticket_messages

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

                    AND sender_staff_code
                        <> :staff_code

                    AND read_at
                        IS NULL
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

    return get_staff_support_ticket(
        staff_code=(
            staff_code
        ),

        ticket_id=(
            ticket_id
        ),
    )


# ============================================================
# ASSIGN SUPPORT TICKET
# ============================================================

def assign_staff_support_ticket(
    *,
    staff_code: str,
    ticket_id: str,
    assigned_staff_code: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    ticket_id = validate_uuid(
        ticket_id,
        "ticket ID",
    )

    assigned_staff_code = (
        clean_required_text(
            assigned_staff_code,
            "Assigned staff code",
        )
    )

    validate_active_staff(
        assigned_staff_code
    )

    # For now, assignment is allowed only if the
    # current staff member can already access ticket.
    # Later this will be governed by MANAGE_SUPPORT.
    get_staff_support_ticket(
        staff_code=(
            staff_code
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
                    public.staff_support_tickets

                SET
                    assigned_staff_code
                        = :assigned_staff_code,

                    status = 'InProgress',

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

                "assigned_staff_code": (
                    assigned_staff_code
                ),
            },
        )

    # The person assigning it can still see the
    # ticket if they created it.
    return get_staff_support_ticket(
        staff_code=(
            staff_code
        ),

        ticket_id=(
            ticket_id
        ),
    )


# ============================================================
# UPDATE SUPPORT STATUS
# ============================================================

def update_staff_support_status(
    *,
    staff_code: str,
    ticket_id: str,
    status: str,
    resolution_notes: str | None = None,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    ticket_id = validate_uuid(
        ticket_id,
        "ticket ID",
    )

    status = clean_required_text(
        status,
        "Status",
    )

    resolution_notes = (
        clean_optional_text(
            resolution_notes
        )
    )

    current_ticket = (
        get_staff_support_ticket(
            staff_code=(
                staff_code
            ),

            ticket_id=(
                ticket_id
            ),
        )
    )

    valid_statuses = {
        "Open",
        "InProgress",
        "AwaitingStaff",
        "Resolved",
        "Closed",
    }

    if (
        status
        not in valid_statuses
    ):

        raise ValueError(
            "Invalid support ticket status."
        )

    resolved_at = None
    resolved_by = None
    closed_at = None

    if (
        status
        == "Resolved"
    ):

        resolved_at = datetime.now(
            timezone.utc
        )

        resolved_by = (
            staff_code
        )

    elif (
        status
        == "Closed"
    ):

        closed_at = datetime.now(
            timezone.utc
        )

        if (
            current_ticket[
                "resolved_at"
            ]
            is None
        ):

            resolved_at = datetime.now(
                timezone.utc
            )

            resolved_by = (
                staff_code
            )

        else:

            resolved_at = (
                current_ticket[
                    "resolved_at"
                ]
            )

            resolved_by = (
                current_ticket[
                    "resolved_by"
                ]
            )

    else:

        resolved_at = (
            current_ticket[
                "resolved_at"
            ]
        )

        resolved_by = (
            current_ticket[
                "resolved_by"
            ]
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.staff_support_tickets

                SET
                    status = :status,

                    resolved_at
                        = :resolved_at,

                    resolved_by
                        = :resolved_by,

                    resolution_notes
                        = :resolution_notes,

                    closed_at
                        = :closed_at,

                    updated_at
                        = now()

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

                "status": (
                    status
                ),

                "resolved_at": (
                    resolved_at
                ),

                "resolved_by": (
                    resolved_by
                ),

                "resolution_notes": (
                    resolution_notes
                ),

                "closed_at": (
                    closed_at
                ),
            },
        )

    return get_staff_support_ticket(
        staff_code=(
            staff_code
        ),

        ticket_id=(
            ticket_id
        ),
    )