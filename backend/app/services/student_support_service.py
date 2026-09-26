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
                str(value)
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
# REGISTRATION
# ============================================================

def get_student_support_registration(
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
                    "student_number": student_number,
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "No student registration was found."
        )

    return dict(row)


def ensure_support_available(
    registration: dict,
) -> None:

    completion_date = registration.get(
        "expected_completion_date"
    )

    if (
        completion_date
        and completion_date < date.today()
    ):

        raise ValueError(
            
                "Student support is no longer available "
                "because this programme has ended."
            
        )


# ============================================================
# LIST SUPPORT TICKETS
# ============================================================

def get_student_support_tickets(
    student_number: str,
) -> list[dict]:

    registration = (
        get_student_support_registration(
            student_number
        )
    )

    completion_date = registration.get(
        "expected_completion_date"
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
                        st.id,
                        st.ticket_number,
                        st.category,
                        st.subject,
                        st.description,
                        st.priority,
                        st.status,
                        st.assigned_staff_code,
                        st.created_at,
                        st.updated_at,
                        st.resolved_at,
                        st.resolved_by,
                        st.resolution_notes,
                        st.closed_at,

                        (
                            SELECT
                                stm.message_body

                            FROM
                                public.support_ticket_messages stm

                            WHERE
                                stm.ticket_id = st.id

                            ORDER BY
                                stm.sent_at DESC

                            LIMIT 1
                        ) AS last_message,

                        (
                            SELECT
                                stm.sent_at

                            FROM
                                public.support_ticket_messages stm

                            WHERE
                                stm.ticket_id = st.id

                            ORDER BY
                                stm.sent_at DESC

                            LIMIT 1
                        ) AS last_message_at,

                        (
                            SELECT
                                COUNT(*)

                            FROM
                                public.support_ticket_messages stm

                            WHERE
                                stm.ticket_id = st.id

                                AND stm.sender_type <> 'Student'

                                AND stm.read_at IS NULL
                        ) AS unread_count

                    FROM
                        public.support_tickets st

                    WHERE
                        st.student_number = :student_number

                        AND st.registration_id =
                            CAST(
                                :registration_id
                                AS uuid
                            )

                    ORDER BY
                        CASE st.status
                            WHEN 'Open'
                                THEN 1
                            WHEN 'InProgress'
                                THEN 2
                            WHEN 'AwaitingStudent'
                                THEN 3
                            WHEN 'Resolved'
                                THEN 4
                            WHEN 'Closed'
                                THEN 5
                            ELSE 6
                        END,

                        st.updated_at DESC
                    """
                ),
                {
                    "student_number": student_number,
                    "registration_id": str(
                        registration["id"]
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# GET ONE SUPPORT TICKET
# ============================================================

def get_student_support_ticket(
    student_number: str,
    ticket_id: str,
    mark_staff_messages_read: bool = True,
) -> dict:

    ticket_id = validate_uuid(
        ticket_id,
        "support ticket ID",
    )

    registration = (
        get_student_support_registration(
            student_number
        )
    )

    ensure_support_available(
        registration
    )

    with engine.begin() as connection:

        ticket = (
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

                    FROM
                        public.support_tickets

                    WHERE
                        id = CAST(
                            :ticket_id
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
                    "ticket_id": ticket_id,
                    "student_number": student_number,
                    "registration_id": str(
                        registration["id"]
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not ticket:

            raise ValueError(
                "Support ticket was not found."
            )

        messages = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        ticket_id,
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
                    "ticket_id": ticket_id,
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
                        public.support_ticket_messages

                    SET
                        read_at = now()

                    WHERE
                        ticket_id = CAST(
                            :ticket_id
                            AS uuid
                        )

                        AND sender_type <> 'Student'

                        AND read_at IS NULL
                    """
                ),
                {
                    "ticket_id": ticket_id,
                },
            )

    return {
        "ticket": dict(ticket),
        "messages": [
            dict(message)
            for message in messages
        ],
    }


# ============================================================
# CREATE SUPPORT TICKET
# ============================================================

def create_student_support_ticket(
    student_number: str,
    category: str,
    subject: str,
    description: str,
    priority: str = "Normal",
) -> dict:

    subject = clean_required_text(
        subject,
        "Subject",
    )

    description = clean_required_text(
        description,
        "Description",
    )

    registration = (
        get_student_support_registration(
            student_number
        )
    )

    ensure_support_available(
        registration
    )

    with engine.begin() as connection:

        ticket = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.support_tickets (
                            registration_id,
                            student_number,
                            category,
                            subject,
                            description,
                            priority,
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
                        :category,
                        :subject,
                        :description,
                        :priority,
                        'Open',
                        now(),
                        now()
                    )

                    RETURNING
                        id,
                        ticket_number,
                        registration_id,
                        student_number,
                        category,
                        subject,
                        description,
                        priority,
                        status,
                        created_at,
                        updated_at
                    """
                ),
                {
                    "registration_id": str(
                        registration["id"]
                    ),
                    "student_number": student_number,
                    "category": category,
                    "subject": subject,
                    "description": description,
                    "priority": priority,
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
                        public.support_ticket_messages (
                            ticket_id,
                            sender_type,
                            sender_code,
                            message_body,
                            sent_at
                        )

                    VALUES (
                        CAST(
                            :ticket_id
                            AS uuid
                        ),
                        'Student',
                        :student_number,
                        :message_body,
                        now()
                    )

                    RETURNING
                        id,
                        ticket_id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at
                    """
                ),
                {
                    "ticket_id": str(
                        ticket["id"]
                    ),
                    "student_number": student_number,
                    "message_body": description,
                },
            )
            .mappings()
            .first()
        )

    return {
        "ticket": dict(ticket),
        "message": dict(first_message),
    }


# ============================================================
# REPLY TO SUPPORT TICKET
# ============================================================

def reply_to_student_support_ticket(
    student_number: str,
    ticket_id: str,
    message: str,
) -> dict:

    ticket_id = validate_uuid(
        ticket_id,
        "support ticket ID",
    )

    message = clean_required_text(
        message,
        "Message",
    )

    registration = (
        get_student_support_registration(
            student_number
        )
    )

    ensure_support_available(
        registration
    )

    with engine.begin() as connection:

        ticket = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        ticket_number,
                        status

                    FROM
                        public.support_tickets

                    WHERE
                        id = CAST(
                            :ticket_id
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
                    "ticket_id": ticket_id,
                    "student_number": student_number,
                    "registration_id": str(
                        registration["id"]
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not ticket:

            raise ValueError(
                "Support ticket was not found."
            )

        if ticket["status"] == "Closed":

            raise ValueError(
                
                    "This support ticket is closed. "
                    "Please create a new support ticket "
                    "if you still need assistance."
                
            )

        new_message = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.support_ticket_messages (
                            ticket_id,
                            sender_type,
                            sender_code,
                            message_body,
                            sent_at
                        )

                    VALUES (
                        CAST(
                            :ticket_id
                            AS uuid
                        ),
                        'Student',
                        :student_number,
                        :message_body,
                        now()
                    )

                    RETURNING
                        id,
                        ticket_id,
                        sender_type,
                        sender_code,
                        message_body,
                        sent_at,
                        read_at
                    """
                ),
                {
                    "ticket_id": ticket_id,
                    "student_number": student_number,
                    "message_body": message,
                },
            )
            .mappings()
            .first()
        )

        connection.execute(
            text(
                """
                UPDATE
                    public.support_tickets

                SET
                    status = 'Open',
                    updated_at = now(),
                    resolved_at = null,
                    resolved_by = null,
                    resolution_notes = null,
                    closed_at = null

                WHERE
                    id = CAST(
                        :ticket_id
                        AS uuid
                    )
                """
            ),
            {
                "ticket_id": ticket_id,
            },
        )

    return {
        "ticket_number": ticket["ticket_number"],
        "reply": dict(new_message),
    }