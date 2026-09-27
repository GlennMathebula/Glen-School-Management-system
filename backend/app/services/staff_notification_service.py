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
# FORMAT NOTIFICATION
# ============================================================

def format_notification(
    row,
) -> dict:

    row = dict(
        row
    )

    return {
        "notification_id": str(
            row[
                "id"
            ]
        ),

        "recipient_staff_code": (
            row[
                "recipient_staff_code"
            ]
        ),

        "notification_type": (
            row[
                "notification_type"
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

        "priority": (
            row[
                "priority"
            ]
        ),

        "action_url": (
            row[
                "action_url"
            ]
        ),

        "metadata": (
            row[
                "metadata"
            ]
            or {}
        ),

        "show_desktop_popup": (
            row[
                "show_desktop_popup"
            ]
        ),

        "read_at": (
            row[
                "read_at"
            ]
        ),

        "popup_delivered_at": (
            row[
                "popup_delivered_at"
            ]
        ),

        "expires_at": (
            row[
                "expires_at"
            ]
        ),

        "created_by_staff_code": (
            row[
                "created_by_staff_code"
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

        "is_read": (
            row[
                "read_at"
            ]
            is not None
        ),

        "popup_pending": (
            bool(
                row[
                    "show_desktop_popup"
                ]
            )
            and row[
                "popup_delivered_at"
            ]
            is None
        ),
    }


# ============================================================
# CREATE NOTIFICATION
# ============================================================

def create_staff_notification(
    *,
    recipient_staff_code: str,
    notification_type: str,
    title: str,
    message: str,
    priority: str = "Normal",
    action_url: str | None = None,
    metadata: dict | None = None,
    show_desktop_popup: bool = True,
    expires_at: datetime | None = None,
    created_by_staff_code: str | None = None,
) -> dict:

    recipient_staff_code = (
        clean_required_text(
            recipient_staff_code,
            "Recipient staff code",
        )
    )

    notification_type = (
        clean_required_text(
            notification_type,
            "Notification type",
        )
    )

    title = clean_required_text(
        title,
        "Title",
    )

    message = clean_required_text(
        message,
        "Message",
    )

    priority = clean_required_text(
        priority,
        "Priority",
    )

    valid_priorities = {
        "Normal",
        "Important",
        "Urgent",
    }

    if (
        priority
        not in valid_priorities
    ):

        raise ValueError(
            "Invalid notification priority."
        )

    validate_active_staff(
        recipient_staff_code
    )

    if created_by_staff_code:

        validate_active_staff(
            created_by_staff_code
        )

    action_url = (
        clean_optional_text(
            action_url
        )
    )

    if metadata is None:

        metadata = {}

    with engine.begin() as connection:

        notification_id = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.staff_notifications
                    (
                        recipient_staff_code,
                        notification_type,
                        title,
                        message,
                        priority,
                        action_url,
                        metadata,
                        show_desktop_popup,
                        expires_at,
                        created_by_staff_code
                    )

                    VALUES
                    (
                        :recipient_staff_code,
                        :notification_type,
                        :title,
                        :message,
                        :priority,
                        :action_url,
                        CAST(
                            :metadata
                            AS jsonb
                        ),
                        :show_desktop_popup,
                        :expires_at,
                        :created_by_staff_code
                    )

                    RETURNING id
                    """
                ),
                {
                    "recipient_staff_code": (
                        recipient_staff_code
                    ),

                    "notification_type": (
                        notification_type
                    ),

                    "title": (
                        title
                    ),

                    "message": (
                        message
                    ),

                    "priority": (
                        priority
                    ),

                    "action_url": (
                        action_url
                    ),

                    "metadata": (
                        __import__(
                            "json"
                        ).dumps(
                            metadata
                        )
                    ),

                    "show_desktop_popup": (
                        show_desktop_popup
                    ),

                    "expires_at": (
                        expires_at
                    ),

                    "created_by_staff_code": (
                        created_by_staff_code
                    ),
                },
            )
            .scalar_one()
        )

    return get_staff_notification(
        staff_code=(
            recipient_staff_code
        ),

        notification_id=str(
            notification_id
        ),
    )


# ============================================================
# LIST NOTIFICATIONS
# ============================================================

def get_staff_notifications(
    *,
    staff_code: str,
    unread_only: bool = False,
    limit: int = 100,
) -> list[dict]:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    limit = max(
        1,
        min(
            int(
                limit
            ),
            200,
        ),
    )

    unread_sql = (
        "AND read_at IS NULL"
        if unread_only
        else ""
    )

    query = text(
        f"""
        SELECT
            id,
            recipient_staff_code,
            notification_type,
            title,
            message,
            priority,
            action_url,
            metadata,
            show_desktop_popup,
            read_at,
            popup_delivered_at,
            expires_at,
            created_by_staff_code,
            created_at,
            updated_at

        FROM
            public.staff_notifications

        WHERE
            recipient_staff_code
                = :staff_code

            AND
            (
                expires_at IS NULL

                OR

                expires_at > now()
            )

            {unread_sql}

        ORDER BY
            created_at DESC

        LIMIT :limit
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

                    "limit": (
                        limit
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        format_notification(
            row
        )
        for row in rows
    ]


# ============================================================
# GET ONE NOTIFICATION
# ============================================================

def get_staff_notification(
    *,
    staff_code: str,
    notification_id: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    notification_id = validate_uuid(
        notification_id,
        "notification ID",
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        recipient_staff_code,
                        notification_type,
                        title,
                        message,
                        priority,
                        action_url,
                        metadata,
                        show_desktop_popup,
                        read_at,
                        popup_delivered_at,
                        expires_at,
                        created_by_staff_code,
                        created_at,
                        updated_at

                    FROM
                        public.staff_notifications

                    WHERE
                        id = CAST(
                            :notification_id
                            AS uuid
                        )

                        AND recipient_staff_code
                            = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "notification_id": (
                        notification_id
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
            "Notification not found."
        )

    return format_notification(
        row
    )


# ============================================================
# UNREAD COUNT
# ============================================================

def get_staff_unread_notification_count(
    *,
    staff_code: str,
) -> int:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    with engine.connect() as connection:

        count = (
            connection.execute(
                text(
                    """
                    SELECT
                        COUNT(*)

                    FROM
                        public.staff_notifications

                    WHERE
                        recipient_staff_code
                            = :staff_code

                        AND read_at
                            IS NULL

                        AND
                        (
                            expires_at IS NULL

                            OR

                            expires_at > now()
                        )
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
            .scalar_one()
        )

    return int(
        count
    )


# ============================================================
# PENDING DESKTOP POPUPS
# ============================================================

def get_pending_desktop_notifications(
    *,
    staff_code: str,
    limit: int = 20,
) -> list[dict]:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    limit = max(
        1,
        min(
            int(
                limit
            ),
            50,
        ),
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        recipient_staff_code,
                        notification_type,
                        title,
                        message,
                        priority,
                        action_url,
                        metadata,
                        show_desktop_popup,
                        read_at,
                        popup_delivered_at,
                        expires_at,
                        created_by_staff_code,
                        created_at,
                        updated_at

                    FROM
                        public.staff_notifications

                    WHERE
                        recipient_staff_code
                            = :staff_code

                        AND show_desktop_popup
                            = TRUE

                        AND popup_delivered_at
                            IS NULL

                        AND
                        (
                            expires_at IS NULL

                            OR

                            expires_at > now()
                        )

                    ORDER BY
                        created_at ASC

                    LIMIT :limit
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),

                    "limit": (
                        limit
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        format_notification(
            row
        )
        for row in rows
    ]


# ============================================================
# MARK ONE AS READ
# ============================================================

def mark_staff_notification_read(
    *,
    staff_code: str,
    notification_id: str,
) -> dict:

    notification_id = validate_uuid(
        notification_id,
        "notification ID",
    )

    get_staff_notification(
        staff_code=(
            staff_code
        ),

        notification_id=(
            notification_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.staff_notifications

                SET
                    read_at = COALESCE(
                        read_at,
                        now()
                    ),

                    updated_at = now()

                WHERE
                    id = CAST(
                        :notification_id
                        AS uuid
                    )

                    AND recipient_staff_code
                        = :staff_code
                """
            ),
            {
                "notification_id": (
                    notification_id
                ),

                "staff_code": (
                    staff_code
                ),
            },
        )

    return get_staff_notification(
        staff_code=(
            staff_code
        ),

        notification_id=(
            notification_id
        ),
    )


# ============================================================
# MARK ONE AS UNREAD
# ============================================================

def mark_staff_notification_unread(
    *,
    staff_code: str,
    notification_id: str,
) -> dict:

    notification_id = validate_uuid(
        notification_id,
        "notification ID",
    )

    get_staff_notification(
        staff_code=(
            staff_code
        ),

        notification_id=(
            notification_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.staff_notifications

                SET
                    read_at = NULL,
                    updated_at = now()

                WHERE
                    id = CAST(
                        :notification_id
                        AS uuid
                    )

                    AND recipient_staff_code
                        = :staff_code
                """
            ),
            {
                "notification_id": (
                    notification_id
                ),

                "staff_code": (
                    staff_code
                ),
            },
        )

    return get_staff_notification(
        staff_code=(
            staff_code
        ),

        notification_id=(
            notification_id
        ),
    )


# ============================================================
# MARK ALL AS READ
# ============================================================

def mark_all_staff_notifications_read(
    *,
    staff_code: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    with engine.begin() as connection:

        result = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.staff_notifications

                    SET
                        read_at = COALESCE(
                            read_at,
                            now()
                        ),

                        updated_at = now()

                    WHERE
                        recipient_staff_code
                            = :staff_code

                        AND read_at
                            IS NULL

                        AND
                        (
                            expires_at IS NULL

                            OR

                            expires_at > now()
                        )
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                },
            )
        )

    return {
        "staff_code": (
            staff_code
        ),

        "marked_read": (
            result.rowcount
            or 0
        ),
    }


# ============================================================
# MARK POPUP DELIVERED
# ============================================================

def mark_desktop_popup_delivered(
    *,
    staff_code: str,
    notification_id: str,
) -> dict:

    notification_id = validate_uuid(
        notification_id,
        "notification ID",
    )

    get_staff_notification(
        staff_code=(
            staff_code
        ),

        notification_id=(
            notification_id
        ),
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.staff_notifications

                SET
                    popup_delivered_at
                        = COALESCE(
                            popup_delivered_at,
                            now()
                        ),

                    updated_at = now()

                WHERE
                    id = CAST(
                        :notification_id
                        AS uuid
                    )

                    AND recipient_staff_code
                        = :staff_code
                """
            ),
            {
                "notification_id": (
                    notification_id
                ),

                "staff_code": (
                    staff_code
                ),
            },
        )

    return get_staff_notification(
        staff_code=(
            staff_code
        ),

        notification_id=(
            notification_id
        ),
    )


# ============================================================
# MARK MULTIPLE POPUPS DELIVERED
# ============================================================

def mark_desktop_popups_delivered(
    *,
    staff_code: str,
    notification_ids: list[str],
) -> dict:

    valid_ids = []

    for notification_id in notification_ids:

        valid_ids.append(
            validate_uuid(
                notification_id,
                "notification ID",
            )
        )

    if not valid_ids:

        return {
            "staff_code": (
                staff_code
            ),

            "marked_delivered": 0,
        }

    with engine.begin() as connection:

        result = (
            connection.execute(
                text(
                    """
                    UPDATE
                        public.staff_notifications

                    SET
                        popup_delivered_at
                            = COALESCE(
                                popup_delivered_at,
                                now()
                            ),

                        updated_at = now()

                    WHERE
                        recipient_staff_code
                            = :staff_code

                        AND id = ANY(
                            CAST(
                                :notification_ids
                                AS uuid[]
                            )
                        )
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),

                    "notification_ids": (
                        valid_ids
                    ),
                },
            )
        )

    return {
        "staff_code": (
            staff_code
        ),

        "marked_delivered": (
            result.rowcount
            or 0
        ),
    }