from __future__ import annotations

from uuid import uuid4

from sqlalchemy import text

from app.database import engine
from app.services.staff_auth_service import (
    hash_secret,
)
from app.services.staff_audit_service import (
    create_staff_audit_log,
)


SUPPORT_PRIORITIES = {
    "Low",
    "Normal",
    "High",
    "Urgent",
}

SUPPORT_STATUSES = {
    "Open",
    "In Progress",
    "Waiting",
    "Resolved",
    "Closed",
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


def _clean_optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    value = str(
        value
    ).strip()

    return value or None


def _table_exists(
    connection,
    table_name: str,
) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                )
                """
            ),
            {
                "table_name": table_name
            },
        ).scalar_one()
    )


def _table_columns(
    connection,
    table_name: str,
) -> set[str]:
    return set(
        connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                """
            ),
            {
                "table_name": table_name
            },
        ).scalars().all()
    )


def _write_audit(
    *,
    actor_staff_code: str,
    action_code: str,
    entity_type: str,
    entity_id: str,
    description: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
    metadata: dict | None = None,
) -> None:
    try:
        create_staff_audit_log(
            actor_staff_code=(
                actor_staff_code
            ),
            action_code=action_code,
            module_code="PRINCIPAL",
            entity_type=entity_type,
            entity_id=str(
                entity_id
            ),
            description=description,
            before_data=before_data,
            after_data=after_data,
            metadata=(
                metadata
                or {}
            ),
        )
    except Exception as error:
        print(
            "WARNING: Principal action "
            "succeeded but audit logging "
            f"failed: {error}"
        )


def ensure_principal_support_schema() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS
                public.staff_support_tickets (
                    id uuid PRIMARY KEY
                        DEFAULT gen_random_uuid(),
                    ticket_number text
                        NOT NULL UNIQUE,
                    created_by_staff_code text
                        NOT NULL,
                    assigned_to_staff_code text,
                    category text NOT NULL,
                    subject text NOT NULL,
                    description text NOT NULL,
                    priority text NOT NULL
                        DEFAULT 'Normal',
                    status text NOT NULL
                        DEFAULT 'Open',
                    resolution text,
                    created_at timestamptz
                        NOT NULL DEFAULT NOW(),
                    updated_at timestamptz
                        NOT NULL DEFAULT NOW(),
                    resolved_at timestamptz
                )
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                staff_support_tickets_creator_idx
                ON public.staff_support_tickets (
                    created_by_staff_code
                )
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                staff_support_tickets_status_idx
                ON public.staff_support_tickets (
                    status
                )
                """
            )
        )


def get_principal_overview() -> dict:
    candidate_tables = [
        "applications",
        "registrations",
        "student_accounts",
        "courses",
        "classes",
        "timetable_sessions",
        "staff_accounts",
        "staff_notifications",
        "staff_message_threads",
        "student_message_threads",
        "assessment_appeals",
        "workplace_placements",
        "eisa_sittings",
        "qa_corrective_actions",
        "staff_support_tickets",
    ]

    table_counts = {}

    with engine.connect() as connection:
        for table_name in candidate_tables:
            if not _table_exists(
                connection,
                table_name,
            ):
                continue

            count = int(
                connection.execute(
                    text(
                        f'SELECT COUNT(*) '
                        f'FROM public."{table_name}"'
                    )
                ).scalar_one()
            )

            table_counts[
                table_name
            ] = count

        role_counts = [
            dict(
                row
            )
            for row in connection.execute(
                text(
                    """
                    SELECT
                        role_code,
                        COUNT(*) AS account_count,
                        COUNT(*) FILTER (
                            WHERE is_active = TRUE
                        ) AS active_count
                    FROM public.staff_accounts
                    GROUP BY role_code
                    ORDER BY role_code
                    """
                )
            ).mappings().all()
        ]

    return {
        "table_counts": table_counts,
        "staff_role_counts": role_counts,
    }


def list_principal_staff() -> list[dict]:
    with engine.connect() as connection:
        employee_columns = (
            _table_columns(
                connection,
                "employees",
            )
        )

        contact_exprs = []

        contact_candidates = {
            "email": [
                "email",
                "work_email",
            ],
            "cell_number": [
                "cell_number",
                "mobile_number",
                "cellphone",
            ],
            "phone_number": [
                "phone_number",
                "telephone",
                "work_phone",
            ],
        }

        for alias, candidates in (
            contact_candidates.items()
        ):
            chosen = next(
                (
                    column
                    for column in candidates
                    if column
                    in employee_columns
                ),
                None,
            )

            if chosen:
                contact_exprs.append(
                    f'e."{chosen}" AS '
                    f'"{alias}"'
                )
            else:
                contact_exprs.append(
                    f'NULL::text AS "{alias}"'
                )

        contact_sql = ",\n                    ".join(
            contact_exprs
        )

        rows = connection.execute(
            text(
                f"""
                SELECT
                    sa.staff_code,
                    sa.role_code,
                    sa.is_active,
                    sa.must_change_password,
                    sa.must_change_pin,
                    sa.failed_login_attempts,
                    sa.locked_until,
                    sa.last_login_at,
                    e.employee_number,
                    e.first_name,
                    e.middle_name,
                    e.last_name,
                    e.job_title,
                    e.department,
                    {contact_sql}
                FROM public.staff_accounts sa
                JOIN public.employees e
                    ON e.id = sa.employee_id
                ORDER BY
                    e.last_name,
                    e.first_name,
                    sa.staff_code
                """
            )
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def update_staff_contact(
    *,
    actor_staff_code: str,
    staff_code: str,
    email: str | None,
    cell_number: str | None,
    phone_number: str | None,
) -> dict:
    actor_staff_code = (
        _clean_staff_code(
            actor_staff_code
        )
    )
    staff_code = _clean_staff_code(
        staff_code
    )

    values = {
        "email": (
            _clean_optional_text(
                email
            )
        ),
        "cell_number": (
            _clean_optional_text(
                cell_number
            )
        ),
        "phone_number": (
            _clean_optional_text(
                phone_number
            )
        ),
    }

    if all(
        value is None
        for value in values.values()
    ):
        raise ValueError(
            "At least one contact field "
            "must be supplied."
        )

    with engine.begin() as connection:
        employee_columns = (
            _table_columns(
                connection,
                "employees",
            )
        )

        account = connection.execute(
            text(
                """
                SELECT
                    sa.staff_code,
                    sa.role_code,
                    sa.employee_id
                FROM public.staff_accounts sa
                WHERE sa.staff_code = :staff_code
                LIMIT 1
                """
            ),
            {
                "staff_code": staff_code
            },
        ).mappings().first()

        if not account:
            raise ValueError(
                "Staff account not found."
            )

        contact_candidates = {
            "email": [
                "email",
                "work_email",
            ],
            "cell_number": [
                "cell_number",
                "mobile_number",
                "cellphone",
            ],
            "phone_number": [
                "phone_number",
                "telephone",
                "work_phone",
            ],
        }

        assignments = []
        params = {
            "employee_id": (
                account[
                    "employee_id"
                ]
            )
        }

        applied = {}

        for logical_name, value in (
            values.items()
        ):
            if value is None:
                continue

            column = next(
                (
                    candidate
                    for candidate
                    in contact_candidates[
                        logical_name
                    ]
                    if candidate
                    in employee_columns
                ),
                None,
            )

            if not column:
                continue

            assignments.append(
                f'"{column}" = '
                f':{logical_name}'
            )
            params[
                logical_name
            ] = value
            applied[
                logical_name
            ] = value

        if not assignments:
            raise ValueError(
                "The current employees table "
                "does not contain a supported "
                "contact field."
            )

        if "updated_at" in employee_columns:
            assignments.append(
                '"updated_at" = NOW()'
            )

        before = connection.execute(
            text(
                """
                SELECT *
                FROM public.employees
                WHERE id = CAST(
                    :employee_id AS uuid
                )
                LIMIT 1
                """
            ),
            {
                "employee_id": (
                    account[
                        "employee_id"
                    ]
                )
            },
        ).mappings().first()

        connection.execute(
            text(
                f"""
                UPDATE public.employees
                SET {", ".join(assignments)}
                WHERE id = CAST(
                    :employee_id AS uuid
                )
                """
            ),
            params,
        )

        after = connection.execute(
            text(
                """
                SELECT *
                FROM public.employees
                WHERE id = CAST(
                    :employee_id AS uuid
                )
                LIMIT 1
                """
            ),
            {
                "employee_id": (
                    account[
                        "employee_id"
                    ]
                )
            },
        ).mappings().first()

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "PRINCIPAL_STAFF_CONTACT_UPDATED"
        ),
        entity_type="STAFF_ACCOUNT",
        entity_id=staff_code,
        description=(
            "Principal updated staff "
            "contact information."
        ),
        before_data=(
            dict(
                before
            )
            if before
            else None
        ),
        after_data=(
            dict(
                after
            )
            if after
            else None
        ),
        metadata={
            "staff_code": staff_code,
            "fields": sorted(
                applied.keys()
            ),
        },
    )

    return {
        "staff_code": staff_code,
        "updated_fields": applied,
    }


def reset_staff_credentials(
    *,
    actor_staff_code: str,
    staff_code: str,
    temporary_password: str,
    temporary_pin: str,
) -> dict:
    actor_staff_code = (
        _clean_staff_code(
            actor_staff_code
        )
    )
    staff_code = _clean_staff_code(
        staff_code
    )

    if (
        actor_staff_code
        == staff_code
    ):
        raise ValueError(
            "Use your own profile security "
            "settings to change your own "
            "credentials."
        )

    temporary_password = str(
        temporary_password
    )

    temporary_pin = str(
        temporary_pin
    ).strip()

    if len(
        temporary_password
    ) < 8:
        raise ValueError(
            "Temporary password must be "
            "at least 8 characters."
        )

    if (
        len(
            temporary_pin
        ) != 5
        or not temporary_pin.isdigit()
    ):
        raise ValueError(
            "Temporary PIN must contain "
            "exactly 5 digits."
        )

    with engine.begin() as connection:
        account = connection.execute(
            text(
                """
                SELECT
                    staff_code,
                    role_code,
                    is_active
                FROM public.staff_accounts
                WHERE staff_code = :staff_code
                LIMIT 1
                """
            ),
            {
                "staff_code": staff_code
            },
        ).mappings().first()

        if not account:
            raise ValueError(
                "Staff account not found."
            )

        if str(
            account[
                "role_code"
            ]
            or ""
        ).upper() in {
            "ADMIN",
            "PRINCIPAL",
        }:
            raise ValueError(
                "Principal cannot reset "
                "Admin or Principal credentials "
                "through this endpoint."
            )

        password_hash = (
            hash_secret(
                temporary_password
            )
        )
        pin_hash = hash_secret(
            temporary_pin
        )

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts
                SET
                    password_hash =
                        :password_hash,
                    pin_hash =
                        :pin_hash,
                    must_change_password =
                        TRUE,
                    must_change_pin =
                        TRUE,
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    credentials_issued_at =
                        NOW()
                WHERE staff_code =
                    :staff_code
                """
            ),
            {
                "staff_code": staff_code,
                "password_hash": (
                    password_hash
                ),
                "pin_hash": pin_hash,
            },
        )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "PRINCIPAL_STAFF_CREDENTIALS_RESET"
        ),
        entity_type="STAFF_ACCOUNT",
        entity_id=staff_code,
        description=(
            "Principal issued temporary "
            "staff credentials."
        ),
        metadata={
            "staff_code": staff_code,
            "target_role": (
                account[
                    "role_code"
                ]
            ),
        },
    )

    return {
        "staff_code": staff_code,
        "role_code": (
            account[
                "role_code"
            ]
        ),
        "must_change_password": True,
        "must_change_pin": True,
    }


def create_staff_support_ticket(
    *,
    staff_code: str,
    subject: str,
    category: str,
    description: str,
    priority: str,
) -> dict:
    staff_code = _clean_staff_code(
        staff_code
    )

    subject = str(
        subject
        or ""
    ).strip()
    category = str(
        category
        or ""
    ).strip()
    description = str(
        description
        or ""
    ).strip()

    priority = str(
        priority
        or "Normal"
    ).strip().title()

    if priority not in SUPPORT_PRIORITIES:
        raise ValueError(
            "Invalid support priority."
        )

    if not (
        subject
        and category
        and description
    ):
        raise ValueError(
            "Subject, category and "
            "description are required."
        )

    ticket_number = (
        "SST-"
        + uuid4().hex[
            :12
        ].upper()
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO
                public.staff_support_tickets (
                    ticket_number,
                    created_by_staff_code,
                    category,
                    subject,
                    description,
                    priority,
                    status
                )
                VALUES (
                    :ticket_number,
                    :staff_code,
                    :category,
                    :subject,
                    :description,
                    :priority,
                    'Open'
                )
                RETURNING *
                """
            ),
            {
                "ticket_number": (
                    ticket_number
                ),
                "staff_code": staff_code,
                "category": category,
                "subject": subject,
                "description": (
                    description
                ),
                "priority": priority,
            },
        ).mappings().first()

    return dict(
        row
    )


def list_my_staff_support_tickets(
    *,
    staff_code: str,
) -> list[dict]:
    staff_code = _clean_staff_code(
        staff_code
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.staff_support_tickets
                WHERE created_by_staff_code =
                    :staff_code
                ORDER BY created_at DESC
                """
            ),
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


def list_staff_support_tickets(
    *,
    status: str | None = None,
    priority: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict]:
    status = _clean_optional_text(
        status
    )
    priority = _clean_optional_text(
        priority
    )
    search = _clean_optional_text(
        search
    )

    conditions = []
    params = {
        "limit": int(
            limit
        )
    }

    if status:
        conditions.append(
            "sst.status = :status"
        )
        params[
            "status"
        ] = status

    if priority:
        conditions.append(
            "sst.priority = :priority"
        )
        params[
            "priority"
        ] = priority

    if search:
        conditions.append(
            """
            (
                sst.ticket_number
                    ILIKE :search
                OR sst.subject
                    ILIKE :search
                OR sst.description
                    ILIKE :search
                OR sst.created_by_staff_code
                    ILIKE :search
            )
            """
        )
        params[
            "search"
        ] = (
            "%"
            + search
            + "%"
        )

    where_sql = (
        "WHERE "
        + " AND ".join(
            conditions
        )
        if conditions
        else ""
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT
                    sst.*
                FROM public.staff_support_tickets sst
                {where_sql}
                ORDER BY
                    sst.created_at DESC
                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def update_staff_support_ticket(
    *,
    actor_staff_code: str,
    ticket_id: str,
    status: str | None,
    priority: str | None,
    assigned_to_staff_code: str | None,
    resolution: str | None,
) -> dict:
    actor_staff_code = (
        _clean_staff_code(
            actor_staff_code
        )
    )

    status = _clean_optional_text(
        status
    )

    priority = _clean_optional_text(
        priority
    )

    assigned_to_staff_code = (
        _clean_optional_text(
            assigned_to_staff_code
        )
    )

    resolution = _clean_optional_text(
        resolution
    )

    if status:
        status = status.title()

        if status not in (
            SUPPORT_STATUSES
        ):
            raise ValueError(
                "Invalid support status."
            )

    if priority:
        priority = priority.title()

        if priority not in (
            SUPPORT_PRIORITIES
        ):
            raise ValueError(
                "Invalid support priority."
            )

    with engine.begin() as connection:
        before = connection.execute(
            text(
                """
                SELECT *
                FROM public.staff_support_tickets
                WHERE id = CAST(
                    :ticket_id AS uuid
                )
                LIMIT 1
                """
            ),
            {
                "ticket_id": ticket_id
            },
        ).mappings().first()

        if not before:
            raise ValueError(
                "Support ticket not found."
            )

        if assigned_to_staff_code:
            staff_exists = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM public.staff_accounts
                    WHERE staff_code =
                        :staff_code
                      AND is_active = TRUE
                    LIMIT 1
                    """
                ),
                {
                    "staff_code": (
                        assigned_to_staff_code
                    )
                },
            ).first()

            if not staff_exists:
                raise ValueError(
                    "Assigned staff account "
                    "was not found or inactive."
                )

        row = connection.execute(
            text(
                """
                UPDATE public.staff_support_tickets
                SET
                    status =
                        COALESCE(
                            :status,
                            status
                        ),
                    priority =
                        COALESCE(
                            :priority,
                            priority
                        ),
                    assigned_to_staff_code =
                        COALESCE(
                            :assigned_to_staff_code,
                            assigned_to_staff_code
                        ),
                    resolution =
                        COALESCE(
                            :resolution,
                            resolution
                        ),
                    resolved_at =
                        CASE
                            WHEN :status IN (
                                'Resolved',
                                'Closed'
                            )
                            THEN COALESCE(
                                resolved_at,
                                NOW()
                            )
                            WHEN :status IS NOT NULL
                            THEN NULL
                            ELSE resolved_at
                        END,
                    updated_at = NOW()
                WHERE id = CAST(
                    :ticket_id AS uuid
                )
                RETURNING *
                """
            ),
            {
                "ticket_id": (
                    ticket_id
                ),
                "status": status,
                "priority": priority,
                "assigned_to_staff_code": (
                    assigned_to_staff_code
                ),
                "resolution": resolution,
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code=(
            "PRINCIPAL_SUPPORT_TICKET_UPDATED"
        ),
        entity_type="STAFF_SUPPORT_TICKET",
        entity_id=record[
            "id"
        ],
        description=(
            "Principal updated a staff "
            "support ticket."
        ),
        before_data=dict(
            before
        ),
        after_data=record,
    )

    return record
