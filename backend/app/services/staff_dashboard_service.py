from sqlalchemy import text

from app.database import engine
from app.services.staff_notification_service import (
    get_staff_notifications,
    get_staff_unread_notification_count,
)
from app.services.staff_permission_service import (
    get_staff_permission_context,
)
from app.services.staff_profile_service import (
    get_staff_profile,
)


# ============================================================
# HELPERS
# ============================================================

def _count(
    connection,
    sql: str,
    params: dict,
) -> int:

    value = connection.execute(
        text(
            sql
        ),
        params,
    ).scalar_one()

    return int(
        value
        or 0
    )


# ============================================================
# COMMON COUNTS
# ============================================================

def get_staff_common_counts(
    *,
    staff_code: str,
) -> dict:

    with engine.connect() as connection:

        unread_staff_messages = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.staff_messages m

            JOIN public.staff_message_threads t
                ON t.id = m.thread_id

            WHERE
                (
                    t.sender_staff_code
                        = :staff_code

                    OR

                    t.recipient_staff_code
                        = :staff_code
                )

                AND m.sender_staff_code
                    <> :staff_code

                AND m.read_at IS NULL
            """,
            {
                "staff_code": (
                    staff_code
                ),
            },
        )

        open_support_tickets = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.staff_support_tickets

            WHERE
                (
                    created_by_staff_code
                        = :staff_code

                    OR

                    assigned_staff_code
                        = :staff_code
                )

                AND status NOT IN (
                    'Resolved',
                    'Closed'
                )
            """,
            {
                "staff_code": (
                    staff_code
                ),
            },
        )

        unread_support_messages = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM
                public.staff_support_ticket_messages m

            JOIN public.staff_support_tickets t
                ON t.id = m.ticket_id

            WHERE
                (
                    t.created_by_staff_code
                        = :staff_code

                    OR

                    t.assigned_staff_code
                        = :staff_code
                )

                AND m.sender_staff_code
                    <> :staff_code

                AND m.read_at IS NULL
            """,
            {
                "staff_code": (
                    staff_code
                ),
            },
        )

    unread_notifications = (
        get_staff_unread_notification_count(
            staff_code=(
                staff_code
            ),
        )
    )

    return {
        "unread_notifications": (
            unread_notifications
        ),

        "unread_staff_messages": (
            unread_staff_messages
        ),

        "open_support_tickets": (
            open_support_tickets
        ),

        "unread_support_messages": (
            unread_support_messages
        ),
    }


# ============================================================
# ACADEMIC DELIVERY SUMMARY
# FACILITATOR + ASSESSOR
# ============================================================

def get_academic_delivery_summary(
    *,
    staff_code: str,
    roles: list[str],
) -> dict | None:

    role_set = {
        str(
            role
        ).strip().upper()
        for role in roles
    }

    is_facilitator = (
        "FACILITATOR"
        in role_set
    )

    is_assessor = (
        "ASSESSOR"
        in role_set
    )

    if (
        not is_facilitator
        and not is_assessor
    ):

        return None

    params = {
        "staff_code": (
            staff_code
        ),

        "is_facilitator": (
            is_facilitator
        ),

        "is_assessor": (
            is_assessor
        ),
    }

    assignment_filter = """
        (
            (
                :is_facilitator = TRUE

                AND c.facilitator_code
                    = :staff_code
            )

            OR

            (
                :is_assessor = TRUE

                AND c.assessor_code
                    = :staff_code
            )
        )
    """

    with engine.connect() as connection:

        assigned_classes = _count(
            connection,
            f"""
            SELECT
                COUNT(
                    DISTINCT c.id
                )

            FROM public.classes c

            WHERE
                c.status = 'Active'

                AND {assignment_filter}
            """,
            params,
        )

        assigned_learners = _count(
            connection,
            f"""
            SELECT
                COUNT(
                    DISTINCT ce.registration_id
                )

            FROM public.classes c

            JOIN public.class_enrolments ce
                ON ce.class_id = c.id

                AND ce.status = 'Active'

            WHERE
                c.status = 'Active'

                AND {assignment_filter}
            """,
            params,
        )

    return {
        "assigned_classes": (
            assigned_classes
        ),

        "assigned_learners": (
            assigned_learners
        ),
    }


# ============================================================
# ASSESSOR SUMMARY
# ============================================================

def get_assessor_summary(
    *,
    staff_code: str,
    roles: list[str],
) -> dict | None:

    role_set = {
        str(
            role
        ).strip().upper()
        for role in roles
    }

    if (
        "ASSESSOR"
        not in role_set
    ):

        return None

    params = {
        "staff_code": (
            staff_code
        ),
    }

    with engine.connect() as connection:

        module_drafts = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.marks

            WHERE
                assessor_code
                    = :staff_code

                AND status = 'Draft'
            """,
            params,
        )

        module_returned = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.marks

            WHERE
                assessor_code
                    = :staff_code

                AND status = 'Returned'
            """,
            params,
        )

        module_submitted = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.marks

            WHERE
                assessor_code
                    = :staff_code

                AND status = 'Submitted'
            """,
            params,
        )

        summative_drafts = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.summative_assessments

            WHERE
                assessor_code
                    = :staff_code

                AND status = 'Draft'
            """,
            params,
        )

        summative_returned = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.summative_assessments

            WHERE
                assessor_code
                    = :staff_code

                AND status = 'Returned'
            """,
            params,
        )

        summative_submitted = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.summative_assessments

            WHERE
                assessor_code
                    = :staff_code

                AND status = 'Submitted'
            """,
            params,
        )

    return {
        "module_assessments": {
            "draft": (
                module_drafts
            ),

            "returned": (
                module_returned
            ),

            "submitted": (
                module_submitted
            ),
        },

        "summative_assessments": {
            "draft": (
                summative_drafts
            ),

            "returned": (
                summative_returned
            ),

            "submitted": (
                summative_submitted
            ),
        },

        "requires_attention": (
            module_returned
            + summative_returned
        ),
    }


# ============================================================
# MODERATOR SUMMARY
# ============================================================

def get_moderator_summary(
    *,
    staff_code: str,
    roles: list[str],
) -> dict | None:

    role_set = {
        str(
            role
        ).strip().upper()
        for role in roles
    }

    if (
        "MODERATOR"
        not in role_set
    ):

        return None

    params = {
        "staff_code": (
            staff_code
        ),
    }

    with engine.connect() as connection:

        module_pending = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.marks

            WHERE
                status = 'Submitted'

                AND
                (
                    assessor_code IS NULL

                    OR

                    assessor_code
                        <> :staff_code
                )
            """,
            params,
        )

        summative_pending = _count(
            connection,
            """
            SELECT COUNT(*)

            FROM public.summative_assessments

            WHERE
                status = 'Submitted'

                AND
                (
                    assessor_code IS NULL

                    OR

                    assessor_code
                        <> :staff_code
                )
            """,
            params,
        )

    return {
        "pending_module_moderation": (
            module_pending
        ),

        "pending_summative_moderation": (
            summative_pending
        ),

        "total_pending_moderation": (
            module_pending
            + summative_pending
        ),
    }


# ============================================================
# COMMON STAFF DASHBOARD
# ============================================================

def get_staff_dashboard(
    *,
    staff_code: str,
) -> dict:

    profile = (
        get_staff_profile(
            staff_code=(
                staff_code
            ),
        )
    )

    permission_context = (
        get_staff_permission_context(
            staff_code=(
                staff_code
            ),
        )
    )

    roles = (
        permission_context.get(
            "roles"
        )
        or []
    )

    common_counts = (
        get_staff_common_counts(
            staff_code=(
                staff_code
            ),
        )
    )

    recent_notifications = (
        get_staff_notifications(
            staff_code=(
                staff_code
            ),

            unread_only=False,

            limit=5,
        )
    )

    workload = {}

    academic_delivery = (
        get_academic_delivery_summary(
            staff_code=(
                staff_code
            ),

            roles=(
                roles
            ),
        )
    )

    if academic_delivery is not None:

        workload[
            "academic_delivery"
        ] = academic_delivery

    assessor = (
        get_assessor_summary(
            staff_code=(
                staff_code
            ),

            roles=(
                roles
            ),
        )
    )

    if assessor is not None:

        workload[
            "assessment"
        ] = assessor

    moderator = (
        get_moderator_summary(
            staff_code=(
                staff_code
            ),

            roles=(
                roles
            ),
        )
    )

    if moderator is not None:

        workload[
            "moderation"
        ] = moderator

    return {
        "staff": (
            profile
        ),

        "access": {
            "roles": (
                roles
            ),

            "permissions": (
                permission_context.get(
                    "permissions"
                )
                or []
            ),

            "permission_count": (
                permission_context.get(
                    "permission_count"
                )
                or 0
            ),
        },

        "counts": (
            common_counts
        ),

        "workload": (
            workload
        ),

        "recent_notifications": (
            recent_notifications
        ),
    }