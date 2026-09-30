import json
from uuid import UUID

from sqlalchemy import text

from app.database import engine


ALLOWED_PRIORITIES = {
    "Normal",
    "Important",
    "Urgent",
}


def _clean_staff_code(
    staff_code: str,
) -> str:
    value = str(
        staff_code
        or ""
    ).strip().upper()

    if not value:
        raise ValueError(
            "Staff code is required."
        )

    return value


def _clean_notification_id(
    notification_id: str,
) -> str:
    value = str(
        notification_id
        or ""
    ).strip()

    try:
        UUID(value)
    except (
        TypeError,
        ValueError,
        AttributeError,
    ) as error:
        raise ValueError(
            "Invalid notification ID."
        ) from error

    return value


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
    expires_at=None,
    created_by_staff_code: str | None = None,
) -> dict:
    recipient_staff_code = (
        _clean_staff_code(
            recipient_staff_code
        )
    )

    notification_type = str(
        notification_type
        or ""
    ).strip()

    title = str(
        title
        or ""
    ).strip()

    message = str(
        message
        or ""
    ).strip()

    priority = str(
        priority
        or "Normal"
    ).strip().title()

    if not notification_type:
        raise ValueError(
            "Notification type is required."
        )

    if not title:
        raise ValueError(
            "Notification title is required."
        )

    if not message:
        raise ValueError(
            "Notification message is required."
        )

    if priority not in ALLOWED_PRIORITIES:
        raise ValueError(
            "Priority must be Normal, "
            "Important or Urgent."
        )

    if created_by_staff_code:
        created_by_staff_code = (
            _clean_staff_code(
                created_by_staff_code
            )
        )

    with engine.begin() as connection:
        staff_exists = connection.execute(
            text("""
                SELECT 1
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

        if not staff_exists:
            raise ValueError(
                "Notification recipient is "
                "not an active staff account."
            )

        result = connection.execute(
            text("""
                INSERT INTO public.staff_notifications (
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
                VALUES (
                    :recipient_staff_code,
                    :notification_type,
                    :title,
                    :message,
                    :priority,
                    :action_url,
                    CAST(:metadata AS jsonb),
                    :show_desktop_popup,
                    :expires_at,
                    :created_by_staff_code
                )
                RETURNING *
            """),
            {
                "recipient_staff_code": (
                    recipient_staff_code
                ),
                "notification_type": (
                    notification_type
                ),
                "title": title,
                "message": message,
                "priority": priority,
                "action_url": action_url,
                "metadata": json.dumps(
                    metadata
                    or {}
                ),
                "show_desktop_popup": (
                    bool(
                        show_desktop_popup
                    )
                ),
                "expires_at": expires_at,
                "created_by_staff_code": (
                    created_by_staff_code
                ),
            },
        )

        row = (
            result
            .mappings()
            .first()
        )

    return dict(
        row
    )


def get_staff_notifications(
    *,
    staff_code: str,
    unread_only: bool = False,
    limit: int = 50,
) -> list[dict]:
    staff_code = (
        _clean_staff_code(
            staff_code
        )
    )

    try:
        limit = int(
            limit
        )
    except (
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "Limit must be a number."
        ) from error

    limit = max(
        1,
        min(
            limit,
            100,
        ),
    )

    unread_clause = ""

    if unread_only:
        unread_clause = (
            "AND read_at IS NULL"
        )

    with engine.connect() as connection:
        result = connection.execute(
            text(f"""
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
                FROM public.staff_notifications
                WHERE recipient_staff_code = :staff_code
                  AND (
                        expires_at IS NULL
                        OR expires_at > NOW()
                  )
                  {unread_clause}
                ORDER BY
                    created_at DESC
                LIMIT :limit
            """),
            {
                "staff_code": staff_code,
                "limit": limit,
            },
        )

        rows = (
            result
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_staff_unread_notification_count(
    *,
    staff_code: str,
) -> int:
    staff_code = (
        _clean_staff_code(
            staff_code
        )
    )

    with engine.connect() as connection:
        count = connection.execute(
            text("""
                SELECT COUNT(*)
                FROM public.staff_notifications
                WHERE recipient_staff_code = :staff_code
                  AND read_at IS NULL
                  AND (
                        expires_at IS NULL
                        OR expires_at > NOW()
                  )
            """),
            {
                "staff_code": staff_code
            },
        ).scalar_one()

    return int(
        count
        or 0
    )


def mark_staff_notification_read(
    *,
    staff_code: str,
    notification_id: str,
) -> dict | None:
    staff_code = (
        _clean_staff_code(
            staff_code
        )
    )

    notification_id = (
        _clean_notification_id(
            notification_id
        )
    )

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE public.staff_notifications
                SET
                    read_at = COALESCE(
                        read_at,
                        NOW()
                    ),
                    updated_at = NOW()
                WHERE id = CAST(
                    :notification_id
                    AS uuid
                )
                  AND recipient_staff_code = :staff_code
                RETURNING *
            """),
            {
                "notification_id": (
                    notification_id
                ),
                "staff_code": (
                    staff_code
                ),
            },
        )

        row = (
            result
            .mappings()
            .first()
        )

    if not row:
        return None

    return dict(
        row
    )


def mark_all_staff_notifications_read(
    *,
    staff_code: str,
) -> int:
    staff_code = (
        _clean_staff_code(
            staff_code
        )
    )

    with engine.begin() as connection:
        result = connection.execute(
            text("""
                UPDATE public.staff_notifications
                SET
                    read_at = NOW(),
                    updated_at = NOW()
                WHERE recipient_staff_code = :staff_code
                  AND read_at IS NULL
                  AND (
                        expires_at IS NULL
                        OR expires_at > NOW()
                  )
            """),
            {
                "staff_code": staff_code
            },
        )

        updated_count = (
            result.rowcount
            or 0
        )

    return int(
        updated_count
    )

