import json

from sqlalchemy import text

from app.database import engine
from app.services.staff_permission_service import (
    get_staff_roles,
)


# ============================================================
# HELPERS
# ============================================================

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
# CREATE AUDIT LOG
# ============================================================

def create_staff_audit_log(
    *,
    actor_staff_code: str | None,
    action_code: str,
    module_code: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    description: str | None = None,
    before_data: dict | None = None,
    after_data: dict | None = None,
    metadata: dict | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict:

    action_code = clean_required_text(
        action_code,
        "Action code",
    )

    module_code = clean_required_text(
        module_code,
        "Module code",
    )

    actor_roles = []

    if actor_staff_code:

        actor_roles = get_staff_roles(
            staff_code=(
                actor_staff_code
            ),
        )

    actor_roles_json = json.dumps(
        actor_roles
    )

    before_data_json = (
        json.dumps(
            before_data
        )
        if before_data is not None
        else None
    )

    after_data_json = (
        json.dumps(
            after_data
        )
        if after_data is not None
        else None
    )

    metadata_json = json.dumps(
        metadata
        or {}
    )

    with engine.begin() as connection:

        row = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.staff_audit_logs
                    (
                        actor_staff_code,
                        actor_roles,
                        action_code,
                        module_code,
                        entity_type,
                        entity_id,
                        description,
                        before_data,
                        after_data,
                        metadata,
                        request_id,
                        ip_address,
                        user_agent
                    )

                    VALUES
                    (
                        :actor_staff_code,
                        CAST(
                            :actor_roles
                            AS jsonb
                        ),
                        :action_code,
                        :module_code,
                        :entity_type,
                        :entity_id,
                        :description,
                        CAST(
                            :before_data
                            AS jsonb
                        ),
                        CAST(
                            :after_data
                            AS jsonb
                        ),
                        CAST(
                            :metadata
                            AS jsonb
                        ),
                        :request_id,
                        :ip_address,
                        :user_agent
                    )

                    RETURNING
                        id,
                        created_at
                    """
                ),
                {
                    "actor_staff_code": (
                        actor_staff_code
                    ),

                    "actor_roles": (
                        actor_roles_json
                    ),

                    "action_code": (
                        action_code
                    ),

                    "module_code": (
                        module_code
                    ),

                    "entity_type": (
                        entity_type
                    ),

                    "entity_id": (
                        entity_id
                    ),

                    "description": (
                        description
                    ),

                    "before_data": (
                        before_data_json
                    ),

                    "after_data": (
                        after_data_json
                    ),

                    "metadata": (
                        metadata_json
                    ),

                    "request_id": (
                        request_id
                    ),

                    "ip_address": (
                        ip_address
                    ),

                    "user_agent": (
                        user_agent
                    ),
                },
            )
            .mappings()
            .first()
        )

    return {
        "audit_id": str(
            row[
                "id"
            ]
        ),

        "created_at": (
            row[
                "created_at"
            ]
        ),
    }


# ============================================================
# GET AUDIT LOGS
# ============================================================

def get_staff_audit_logs(
    *,
    actor_staff_code: str | None = None,
    module_code: str | None = None,
    action_code: str | None = None,
    limit: int = 100,
) -> list[dict]:

    limit = max(
        1,
        min(
            int(
                limit
            ),
            500,
        ),
    )

    filters = []

    params = {
        "limit": (
            limit
        ),
    }

    if actor_staff_code:

        actor_staff_code = (
            actor_staff_code
            .strip()
        )

        if actor_staff_code:

            filters.append(
                """
                actor_staff_code
                    = :actor_staff_code
                """
            )

            params[
                "actor_staff_code"
            ] = actor_staff_code

    if module_code:

        module_code = (
            module_code
            .strip()
        )

        if module_code:

            filters.append(
                """
                module_code
                    = :module_code
                """
            )

            params[
                "module_code"
            ] = module_code

    if action_code:

        action_code = (
            action_code
            .strip()
        )

        if action_code:

            filters.append(
                """
                action_code
                    = :action_code
                """
            )

            params[
                "action_code"
            ] = action_code

    where_sql = ""

    if filters:

        where_sql = (
            "WHERE "
            + " AND ".join(
                filters
            )
        )

    query = text(
        f"""
        SELECT
            id,
            actor_staff_code,
            actor_roles,
            action_code,
            module_code,
            entity_type,
            entity_id,
            description,
            before_data,
            after_data,
            metadata,
            request_id,
            ip_address,
            user_agent,
            created_at

        FROM
            public.staff_audit_logs

        {where_sql}

        ORDER BY
            created_at DESC

        LIMIT :limit
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                params,
            )
            .mappings()
            .all()
        )

    return [
        {
            "audit_id": str(
                row[
                    "id"
                ]
            ),

            "actor_staff_code": (
                row[
                    "actor_staff_code"
                ]
            ),

            "actor_roles": (
                row[
                    "actor_roles"
                ]
                or []
            ),

            "action_code": (
                row[
                    "action_code"
                ]
            ),

            "module_code": (
                row[
                    "module_code"
                ]
            ),

            "entity_type": (
                row[
                    "entity_type"
                ]
            ),

            "entity_id": (
                row[
                    "entity_id"
                ]
            ),

            "description": (
                row[
                    "description"
                ]
            ),

            "before_data": (
                row[
                    "before_data"
                ]
            ),

            "after_data": (
                row[
                    "after_data"
                ]
            ),

            "metadata": (
                row[
                    "metadata"
                ]
                or {}
            ),

            "request_id": (
                row[
                    "request_id"
                ]
            ),

            "ip_address": (
                row[
                    "ip_address"
                ]
            ),

            "user_agent": (
                row[
                    "user_agent"
                ]
            ),

            "created_at": (
                row[
                    "created_at"
                ]
            ),
        }
        for row in rows
    ]


# ============================================================
# GET ONE AUDIT LOG
# ============================================================

def get_staff_audit_log(
    *,
    audit_id: str,
) -> dict:

    audit_id = clean_required_text(
        audit_id,
        "Audit ID",
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        actor_staff_code,
                        actor_roles,
                        action_code,
                        module_code,
                        entity_type,
                        entity_id,
                        description,
                        before_data,
                        after_data,
                        metadata,
                        request_id,
                        ip_address,
                        user_agent,
                        created_at

                    FROM
                        public.staff_audit_logs

                    WHERE
                        id = CAST(
                            :audit_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "audit_id": (
                        audit_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Audit log not found."
        )

    return {
        "audit_id": str(
            row[
                "id"
            ]
        ),

        "actor_staff_code": (
            row[
                "actor_staff_code"
            ]
        ),

        "actor_roles": (
            row[
                "actor_roles"
            ]
            or []
        ),

        "action_code": (
            row[
                "action_code"
            ]
        ),

        "module_code": (
            row[
                "module_code"
            ]
        ),

        "entity_type": (
            row[
                "entity_type"
            ]
        ),

        "entity_id": (
            row[
                "entity_id"
            ]
        ),

        "description": (
            row[
                "description"
            ]
        ),

        "before_data": (
            row[
                "before_data"
            ]
        ),

        "after_data": (
            row[
                "after_data"
            ]
        ),

        "metadata": (
            row[
                "metadata"
            ]
            or {}
        ),

        "request_id": (
            row[
                "request_id"
            ]
        ),

        "ip_address": (
            row[
                "ip_address"
            ]
        ),

        "user_agent": (
            row[
                "user_agent"
            ]
        ),

        "created_at": (
            row[
                "created_at"
            ]
        ),
    }