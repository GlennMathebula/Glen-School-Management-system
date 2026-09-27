from uuid import UUID



from sqlalchemy import text



from app.database import engine
from app.services.staff_notification_service import (
    create_staff_notification,
)





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

# VALIDATE STAFF ACCOUNT

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

# FORMAT THREAD

# ============================================================



def format_thread(

    row,

    current_staff_code: str,

) -> dict:



    row = dict(

        row

    )



    sender_staff_code = (

        row[

            "sender_staff_code"

        ]

    )



    recipient_staff_code = (

        row[

            "recipient_staff_code"

        ]

    )



    other_staff_code = (

        recipient_staff_code

        if sender_staff_code

        == current_staff_code

        else sender_staff_code

    )



    return {

        "thread_id": str(

            row[

                "id"

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



        "status": (

            row[

                "status"

            ]

        ),



        "sender_staff_code": (

            sender_staff_code

        ),



        "recipient_staff_code": (

            recipient_staff_code

        ),



        "other_staff_code": (

            other_staff_code

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

# CREATE THREAD

# ============================================================



def create_staff_message_thread(

    *,

    sender_staff_code: str,

    recipient_staff_code: str,

    subject: str,

    category: str,

    message_body: str,

) -> dict:



    sender_staff_code = (

        clean_required_text(

            sender_staff_code,

            "Sender staff code",

        )

    )



    recipient_staff_code = (

        clean_required_text(

            recipient_staff_code,

            "Recipient staff code",

        )

    )



    subject = clean_required_text(

        subject,

        "Subject",

    )



    message_body = (

        clean_required_text(

            message_body,

            "Message",

        )

    )



    if (

        sender_staff_code

        == recipient_staff_code

    ):



        raise ValueError(

            "You cannot start a message "

            "thread with yourself."

        )



    validate_active_staff(

        sender_staff_code

    )



    validate_active_staff(

        recipient_staff_code

    )



    with engine.begin() as connection:



        thread_id = (

            connection.execute(

                text(

                    """

                    INSERT INTO

                        public.staff_message_threads

                    (

                        sender_staff_code,

                        recipient_staff_code,

                        subject,

                        category,

                        status

                    )



                    VALUES

                    (

                        :sender_staff_code,

                        :recipient_staff_code,

                        :subject,

                        :category,

                        'Open'

                    )



                    RETURNING id

                    """

                ),

                {

                    "sender_staff_code": (

                        sender_staff_code

                    ),



                    "recipient_staff_code": (

                        recipient_staff_code

                    ),



                    "subject": (

                        subject

                    ),



                    "category": (

                        category

                    ),

                },

            )

            .scalar_one()

        )



        connection.execute(

            text(

                """

                INSERT INTO

                    public.staff_messages

                (

                    thread_id,

                    sender_staff_code,

                    message_body

                )



                VALUES

                (

                    CAST(

                        :thread_id

                        AS uuid

                    ),



                    :sender_staff_code,

                    :message_body

                )

                """

            ),

            {

                "thread_id": str(

                    thread_id

                ),



                "sender_staff_code": (

                    sender_staff_code

                ),



                "message_body": (

                    message_body

                ),

            },

        )



    try:

        create_staff_notification(
            recipient_staff_code=(
                recipient_staff_code
            ),
            notification_type=(
                "STAFF_MESSAGE"
            ),
            title=(
                "New Staff Message"
            ),
            message=(
                f"You received a new message from "
                f"{sender_staff_code}: {subject}"
            ),
            priority=(
                "Normal"
            ),
            action_url=(
                f"/staff/communications/messages/"
                f"{thread_id}"
            ),
            metadata={
                "thread_id": str(
                    thread_id
                ),
                "sender_staff_code": (
                    sender_staff_code
                ),
                "subject": (
                    subject
                ),
            },
            show_desktop_popup=True,
            created_by_staff_code=(
                sender_staff_code
            ),
        )

    except Exception as error:

        print(
            "WARNING: Staff message was created, "
            "but its notification could not be created: "
            f"{error}"
        )

    return get_staff_message_thread(

        staff_code=(

            sender_staff_code

        ),

        thread_id=str(

            thread_id

        ),

    )





# ============================================================

# LIST STAFF THREADS

# ============================================================



def get_staff_message_threads(

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

                        t.sender_staff_code,

                        t.recipient_staff_code,

                        t.subject,

                        t.category,

                        t.status,

                        t.created_at,

                        t.updated_at,

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

                        public.staff_message_threads t



                    LEFT JOIN

                        public.staff_messages m

                    ON

                        m.thread_id = t.id



                    WHERE

                        t.sender_staff_code

                            = :staff_code



                        OR

                        t.recipient_staff_code

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

        format_thread(

            row,

            staff_code,

        )

        for row in rows

    ]





# ============================================================

# GET ONE THREAD

# ============================================================



def get_staff_message_thread(

    *,

    staff_code: str,

    thread_id: str,

) -> dict:



    staff_code = clean_required_text(

        staff_code,

        "Staff code",

    )



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

                        sender_staff_code,

                        recipient_staff_code,

                        subject,

                        category,

                        status,

                        created_at,

                        updated_at,

                        closed_at



                    FROM

                        public.staff_message_threads



                    WHERE

                        id = CAST(

                            :thread_id

                            AS uuid

                        )



                        AND

                        (

                            sender_staff_code

                                = :staff_code



                            OR



                            recipient_staff_code

                                = :staff_code

                        )



                    LIMIT 1

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

            .mappings()

            .first()

        )



        if not thread_row:



            raise ValueError(

                "Message thread not found."

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

                        public.staff_messages



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



    thread = format_thread(

        thread_row,

        staff_code,

    )



    thread[

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



    return thread





# ============================================================

# REPLY TO THREAD

# ============================================================



def reply_to_staff_message_thread(

    *,

    staff_code: str,

    thread_id: str,

    message_body: str,

) -> dict:



    staff_code = clean_required_text(

        staff_code,

        "Staff code",

    )



    thread_id = validate_uuid(

        thread_id,

        "thread ID",

    )



    message_body = (

        clean_required_text(

            message_body,

            "Message",

        )

    )



    with engine.begin() as connection:



        thread_row = (

            connection.execute(

                text(

                    """

                    SELECT

                        id,

                        sender_staff_code,

                        recipient_staff_code,

                        subject,

                        status



                    FROM

                        public.staff_message_threads



                    WHERE

                        id = CAST(

                            :thread_id

                            AS uuid

                        )



                        AND

                        (

                            sender_staff_code

                                = :staff_code



                            OR



                            recipient_staff_code

                                = :staff_code

                        )



                    LIMIT 1

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

            .mappings()

            .first()

        )



        if not thread_row:



            raise ValueError(

                "Message thread not found."

            )



        if (

            thread_row[

                "status"

            ]

            == "Closed"

        ):



            raise ValueError(

                "This message thread is closed."

            )



        connection.execute(

            text(

                """

                INSERT INTO

                    public.staff_messages

                (

                    thread_id,

                    sender_staff_code,

                    message_body

                )



                VALUES

                (

                    CAST(

                        :thread_id

                        AS uuid

                    ),



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

                UPDATE

                    public.staff_message_threads



                SET

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



    recipient_staff_code = (
        thread_row[
            "recipient_staff_code"
        ]
        if thread_row[
            "sender_staff_code"
        ]
        == staff_code
        else thread_row[
            "sender_staff_code"
        ]
    )

    try:

        create_staff_notification(
            recipient_staff_code=(
                recipient_staff_code
            ),
            notification_type=(
                "STAFF_MESSAGE_REPLY"
            ),
            title=(
                "New Message Reply"
            ),
            message=(
                f"{staff_code} replied to "
                f"'{thread_row['subject']}'."
            ),
            priority=(
                "Normal"
            ),
            action_url=(
                f"/staff/communications/messages/"
                f"{thread_id}"
            ),
            metadata={
                "thread_id": (
                    thread_id
                ),
                "sender_staff_code": (
                    staff_code
                ),
                "subject": (
                    thread_row[
                        "subject"
                    ]
                ),
            },
            show_desktop_popup=True,
            created_by_staff_code=(
                staff_code
            ),
        )

    except Exception as error:

        print(
            "WARNING: Staff message reply was sent, "
            "but its notification could not be created: "
            f"{error}"
        )

    return get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )





# ============================================================

# MARK THREAD AS READ

# ============================================================



def mark_staff_message_thread_read(

    *,

    staff_code: str,

    thread_id: str,

) -> dict:



    staff_code = clean_required_text(

        staff_code,

        "Staff code",

    )



    thread_id = validate_uuid(

        thread_id,

        "thread ID",

    )



    get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )



    with engine.begin() as connection:



        connection.execute(

            text(

                """

                UPDATE

                    public.staff_messages



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



                    AND sender_staff_code

                        <> :staff_code



                    AND read_at

                        IS NULL

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



    return get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )





# ============================================================

# CLOSE THREAD

# ============================================================



def close_staff_message_thread(

    *,

    staff_code: str,

    thread_id: str,

) -> dict:



    staff_code = clean_required_text(

        staff_code,

        "Staff code",

    )



    thread_id = validate_uuid(

        thread_id,

        "thread ID",

    )



    get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )



    with engine.begin() as connection:



        connection.execute(

            text(

                """

                UPDATE

                    public.staff_message_threads



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



    return get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )





# ============================================================

# REOPEN THREAD

# ============================================================



def reopen_staff_message_thread(

    *,

    staff_code: str,

    thread_id: str,

) -> dict:



    staff_code = clean_required_text(

        staff_code,

        "Staff code",

    )



    thread_id = validate_uuid(

        thread_id,

        "thread ID",

    )



    get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )



    with engine.begin() as connection:



        connection.execute(

            text(

                """

                UPDATE

                    public.staff_message_threads



                SET

                    status = 'Open',

                    closed_at = NULL,

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



    return get_staff_message_thread(

        staff_code=(

            staff_code

        ),

        thread_id=(

            thread_id

        ),

    )