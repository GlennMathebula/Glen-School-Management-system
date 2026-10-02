from __future__ import annotations

from uuid import UUID

from sqlalchemy import text

from app.database import engine
from app.services.staff_auth_service import hash_secret
from app.services.staff_audit_service import create_staff_audit_log


ADMIN_SAFETY_PERMISSIONS = {
    "MANAGE_ROLES_PERMISSIONS",
    "MANAGE_STAFF_ACCOUNTS",
    "MANAGE_SYSTEM_SETTINGS",
}


def _columns(connection, table_name: str) -> set[str]:
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
            {"table_name": table_name},
        ).scalars().all()
    )


def list_system_settings() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("SELECT * FROM public.sms_system_settings ORDER BY 1")
        ).mappings().all()

    return [dict(row) for row in rows]


def update_system_setting(
    *,
    actor_staff_code: str,
    setting_key: str,
    value: str,
) -> dict:
    setting_key = str(setting_key or "").strip()

    with engine.begin() as connection:
        cols = _columns(connection, "sms_system_settings")

        key_col = next(
            (c for c in ("setting_key", "key", "name", "code") if c in cols),
            None,
        )
        value_col = next(
            (c for c in ("setting_value", "value", "value_text") if c in cols),
            None,
        )

        if not key_col or not value_col:
            raise ValueError(
                "sms_system_settings does not expose a recognised key/value schema."
            )

        existing = connection.execute(
            text(
                f"""
                SELECT *
                FROM public.sms_system_settings
                WHERE "{key_col}" = :setting_key
                LIMIT 1
                """
            ),
            {"setting_key": setting_key},
        ).mappings().first()

        if existing:
            sets = [f'"{value_col}" = :value']

            if "updated_at" in cols:
                sets.append("updated_at = NOW()")

            row = connection.execute(
                text(
                    f"""
                    UPDATE public.sms_system_settings
                    SET {", ".join(sets)}
                    WHERE "{key_col}" = :setting_key
                    RETURNING *
                    """
                ),
                {
                    "setting_key": setting_key,
                    "value": value,
                },
            ).mappings().first()
        else:
            insert_cols = [key_col, value_col]
            sql_cols = [f'"{key_col}"', f'"{value_col}"']
            sql_values = [":setting_key", ":value"]

            if "created_at" in cols:
                insert_cols.append("created_at")
                sql_cols.append('"created_at"')
                sql_values.append("NOW()")

            row = connection.execute(
                text(
                    f"""
                    INSERT INTO public.sms_system_settings (
                        {", ".join(sql_cols)}
                    )
                    VALUES (
                        {", ".join(sql_values)}
                    )
                    RETURNING *
                    """
                ),
                {
                    "setting_key": setting_key,
                    "value": value,
                },
            ).mappings().first()

    record = dict(row)

    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code="ADMIN_SYSTEM_SETTING_UPDATED",
            module_code="ADMIN_SYSTEM",
            entity_type="SYSTEM_SETTING",
            entity_id=setting_key,
            description="Admin updated a system setting.",
            before_data=dict(existing) if existing else None,
            after_data=record,
            metadata={},
        )
    except Exception as error:
        print(f"WARNING: system setting audit failed: {error}")

    return record


def list_staff_accounts() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    sa.id,
                    sa.employee_id,
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
                    e.last_name,
                    e.email,
                    e.job_title
                FROM public.staff_accounts sa
                LEFT JOIN public.employees e
                    ON e.id = sa.employee_id
                ORDER BY sa.staff_code
                """
            )
        ).mappings().all()

    return [dict(row) for row in rows]


def create_staff_account(
    *,
    actor_staff_code: str,
    employee_id: str,
    staff_code: str,
    role_code: str,
    temporary_password: str,
    temporary_pin: str,
) -> dict:
    staff_code = str(staff_code or "").strip().upper()
    role_code = str(role_code or "").strip().upper()

    try:
        UUID(str(employee_id))
    except ValueError as error:
        raise ValueError("Invalid employee ID.") from error

    with engine.begin() as connection:
        employee = connection.execute(
            text(
                """
                SELECT id
                FROM public.employees
                WHERE id = CAST(:employee_id AS uuid)
                LIMIT 1
                """
            ),
            {"employee_id": employee_id},
        ).first()

        if not employee:
            raise ValueError("Employee was not found.")

        role = connection.execute(
            text(
                """
                SELECT role_code
                FROM public.staff_roles
                WHERE role_code = :role_code
                LIMIT 1
                """
            ),
            {"role_code": role_code},
        ).first()

        if not role:
            raise ValueError("Staff role was not found.")

        if role_code == "CEO":
            raise ValueError("CEO is not an intended Glen Moniques SMS role.")

        duplicate = connection.execute(
            text(
                """
                SELECT 1
                FROM public.staff_accounts
                WHERE upper(staff_code) = :staff_code
                   OR employee_id = CAST(:employee_id AS uuid)
                LIMIT 1
                """
            ),
            {
                "staff_code": staff_code,
                "employee_id": employee_id,
            },
        ).first()

        if duplicate:
            raise ValueError(
                "A staff account already exists for this staff code or employee."
            )

        row = connection.execute(
            text(
                """
                INSERT INTO public.staff_accounts (
                    employee_id,
                    staff_code,
                    role_code,
                    password_hash,
                    pin_hash,
                    must_change_password,
                    must_change_pin,
                    failed_login_attempts,
                    is_active,
                    credentials_issued_at
                )
                VALUES (
                    CAST(:employee_id AS uuid),
                    :staff_code,
                    :role_code,
                    :password_hash,
                    :pin_hash,
                    TRUE,
                    TRUE,
                    0,
                    TRUE,
                    NOW()
                )
                RETURNING
                    id,
                    employee_id,
                    staff_code,
                    role_code,
                    is_active,
                    must_change_password,
                    must_change_pin,
                    credentials_issued_at
                """
            ),
            {
                "employee_id": employee_id,
                "staff_code": staff_code,
                "role_code": role_code,
                "password_hash": hash_secret(temporary_password),
                "pin_hash": hash_secret(temporary_pin),
            },
        ).mappings().first()

    return dict(row)


def set_staff_account_status(
    *,
    actor_staff_code: str,
    staff_code: str,
    is_active: bool,
) -> dict:
    staff_code = str(staff_code or "").strip().upper()

    if staff_code == str(actor_staff_code or "").strip().upper() and not is_active:
        raise ValueError("You cannot deactivate your own staff account.")

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.staff_accounts
                SET
                    is_active = :is_active,
                    locked_until = CASE
                        WHEN :is_active THEN NULL
                        ELSE locked_until
                    END
                WHERE upper(staff_code) = :staff_code
                RETURNING
                    id,
                    employee_id,
                    staff_code,
                    role_code,
                    is_active
                """
            ),
            {
                "staff_code": staff_code,
                "is_active": bool(is_active),
            },
        ).mappings().first()

    if not row:
        raise ValueError("Staff account was not found.")

    return dict(row)


def list_roles_permissions() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    sr.role_code,
                    sr.role_name,
                    COALESCE(
                        array_agg(
                            srp.permission_code
                            ORDER BY srp.permission_code
                        ) FILTER (
                            WHERE srp.permission_code IS NOT NULL
                        ),
                        ARRAY[]::text[]
                    ) AS permissions
                FROM public.staff_roles sr
                LEFT JOIN public.staff_role_permissions srp
                    ON srp.role_code = sr.role_code
                GROUP BY sr.role_code, sr.role_name
                ORDER BY sr.role_code
                """
            )
        ).mappings().all()

    return [dict(row) for row in rows]


def replace_role_permissions(
    *,
    actor_staff_code: str,
    role_code: str,
    permission_codes: list[str],
) -> dict:
    role_code = str(role_code or "").strip().upper()

    if role_code == "CEO":
        raise ValueError("CEO is a legacy role and cannot be configured.")

    clean = sorted(
        {
            str(code or "").strip().upper()
            for code in permission_codes
            if str(code or "").strip()
        }
    )

    if role_code == "ADMIN":
        clean = sorted(set(clean) | ADMIN_SAFETY_PERMISSIONS)

    with engine.begin() as connection:
        role = connection.execute(
            text(
                """
                SELECT role_code
                FROM public.staff_roles
                WHERE role_code = :role_code
                LIMIT 1
                """
            ),
            {"role_code": role_code},
        ).first()

        if not role:
            raise ValueError("Role was not found.")

        valid = set(
            connection.execute(
                text(
                    """
                    SELECT permission_code
                    FROM public.staff_permissions
                    WHERE permission_code = ANY(:permissions)
                    """
                ),
                {"permissions": clean},
            ).scalars().all()
        ) if clean else set()

        invalid = sorted(set(clean) - valid)

        if invalid:
            raise ValueError(
                "Unknown permission codes: " + ", ".join(invalid)
            )

        connection.execute(
            text(
                """
                DELETE FROM public.staff_role_permissions
                WHERE role_code = :role_code
                """
            ),
            {"role_code": role_code},
        )

        for permission_code in clean:
            connection.execute(
                text(
                    """
                    INSERT INTO public.staff_role_permissions (
                        role_code,
                        permission_code
                    )
                    VALUES (
                        :role_code,
                        :permission_code
                    )
                    ON CONFLICT DO NOTHING
                    """
                ),
                {
                    "role_code": role_code,
                    "permission_code": permission_code,
                },
            )

    return {
        "role_code": role_code,
        "permissions": clean,
    }



# ============================================================
# ADMIN STAFF ACCOUNT OPTIONS
# ============================================================

def list_staff_employee_options() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT
                    e.id AS employee_id,
                    e.employee_number,
                    e.first_name,
                    e.middle_name,
                    e.last_name,
                    e.email,
                    e.job_title,
                    e.department,
                    e.employment_status,
                    e.requires_system_access,
                    sa.staff_code
                FROM public.employees e
                LEFT JOIN public.staff_accounts sa
                    ON sa.employee_id = e.id
                WHERE e.employment_status = 'Active'
                  AND e.requires_system_access = TRUE
                ORDER BY e.last_name, e.first_name
            """)
        ).mappings().all()
    return [dict(row) for row in rows]

def list_staff_permission_catalog() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text("""
                SELECT *
                FROM public.staff_permissions
                ORDER BY permission_code
            """)
        ).mappings().all()
    return [dict(row) for row in rows]
