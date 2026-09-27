from datetime import datetime, timezone

from fastapi import (
    Depends,
    HTTPException,
)
from sqlalchemy import text

from app.database import engine
from app.staff_auth_dependency import (
    get_current_staff,
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
# ACTIVE STAFF ROLES
# ============================================================

def get_staff_roles(
    *,
    staff_code: str,
) -> list[str]:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        role_code

                    FROM public.staff_account_roles

                    WHERE
                        staff_code = :staff_code
                        AND is_active = TRUE

                    ORDER BY
                        role_code
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

        # Backward-compatible fallback.
        if not rows:

            primary_role = (
                connection.execute(
                    text(
                        """
                        SELECT
                            role_code

                        FROM public.staff_accounts

                        WHERE
                            staff_code = :staff_code
                            AND is_active = TRUE

                        LIMIT 1
                        """
                    ),
                    {
                        "staff_code": (
                            staff_code
                        ),
                    },
                )
                .scalar_one_or_none()
            )

            if primary_role:

                return [
                    primary_role
                ]

    return [
        row[
            "role_code"
        ]
        for row in rows
    ]


# ============================================================
# EFFECTIVE PERMISSIONS
# ============================================================

def get_staff_permissions(
    *,
    staff_code: str,
) -> list[str]:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    now = datetime.now(
        timezone.utc
    )

    with engine.connect() as connection:

        role_rows = (
            connection.execute(
                text(
                    """
                    SELECT DISTINCT
                        rp.permission_code

                    FROM public.staff_role_permissions rp

                    JOIN public.staff_account_roles sar
                        ON sar.role_code = rp.role_code

                    JOIN public.staff_permissions p
                        ON p.permission_code
                            = rp.permission_code

                    WHERE
                        sar.staff_code
                            = :staff_code

                        AND sar.is_active
                            = TRUE

                        AND p.is_active
                            = TRUE
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

        permissions = {
            row[
                "permission_code"
            ]
            for row in role_rows
        }

        # Backward-compatible fallback if staff_account_roles
        # has not been populated for an older account.
        if not permissions:

            primary_rows = (
                connection.execute(
                    text(
                        """
                        SELECT DISTINCT
                            rp.permission_code

                        FROM public.staff_accounts sa

                        JOIN public.staff_role_permissions rp
                            ON rp.role_code
                                = sa.role_code

                        JOIN public.staff_permissions p
                            ON p.permission_code
                                = rp.permission_code

                        WHERE
                            sa.staff_code
                                = :staff_code

                            AND sa.is_active
                                = TRUE

                            AND p.is_active
                                = TRUE
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

            permissions = {
                row[
                    "permission_code"
                ]
                for row in primary_rows
            }

        override_rows = (
            connection.execute(
                text(
                    """
                    SELECT
                        permission_code,
                        allowed

                    FROM
                        public.staff_permission_overrides

                    WHERE
                        staff_code
                            = :staff_code

                        AND
                        (
                            effective_from IS NULL
                            OR effective_from <= :now
                        )

                        AND
                        (
                            effective_until IS NULL
                            OR effective_until > :now
                        )
                    """
                ),
                {
                    "staff_code": (
                        staff_code
                    ),
                    "now": (
                        now
                    ),
                },
            )
            .mappings()
            .all()
        )

    for row in override_rows:

        permission_code = (
            row[
                "permission_code"
            ]
        )

        if row[
            "allowed"
        ]:

            permissions.add(
                permission_code
            )

        else:

            permissions.discard(
                permission_code
            )

    return sorted(
        permissions
    )


# ============================================================
# HAS PERMISSION
# ============================================================

def staff_has_permission(
    *,
    staff_code: str,
    permission_code: str,
) -> bool:

    permission_code = (
        clean_required_text(
            permission_code,
            "Permission code",
        )
        .upper()
    )

    permissions = (
        get_staff_permissions(
            staff_code=(
                staff_code
            ),
        )
    )

    return (
        permission_code
        in permissions
    )


# ============================================================
# REQUIRE PERMISSION
# ============================================================

def require_permission(
    permission_code: str,
):

    permission_code = (
        clean_required_text(
            permission_code,
            "Permission code",
        )
        .upper()
    )

    def dependency(
        current_staff: dict = Depends(
            get_current_staff
        ),
    ) -> dict:

        staff_code = (
            current_staff[
                "staff_code"
            ]
        )

        if not staff_has_permission(
            staff_code=(
                staff_code
            ),

            permission_code=(
                permission_code
            ),
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You do not have permission "
                    f"to perform this action: "
                    f"{permission_code}."
                ),
            )

        return current_staff

    return dependency


# ============================================================
# PERMISSION CONTEXT
# ============================================================

def get_staff_permission_context(
    *,
    staff_code: str,
) -> dict:

    roles = get_staff_roles(
        staff_code=(
            staff_code
        )
    )

    permissions = (
        get_staff_permissions(
            staff_code=(
                staff_code
            )
        )
    )

    return {
        "staff_code": (
            staff_code
        ),

        "roles": (
            roles
        ),

        "permissions": (
            permissions
        ),

        "permission_count": len(
            permissions
        ),
    }