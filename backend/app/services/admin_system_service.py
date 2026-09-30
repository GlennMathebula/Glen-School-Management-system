from __future__ import annotations

from sqlalchemy import text

from app.database import engine


CORE_TABLES = [
    "applications",
    "registrations",
    "student_accounts",
    "courses",
    "classes",
    "timetable_sessions",
    "module_registrations",
    "marks",
    "summative_assessments",
    "staff_accounts",
    "staff_roles",
    "staff_permissions",
    "staff_role_permissions",
]


def get_admin_system_summary() -> dict:
    with engine.connect() as connection:
        existing_tables = set(
            connection.execute(
                text(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    """
                )
            ).scalars().all()
        )

        table_status = {
            name: name in existing_tables
            for name in CORE_TABLES
        }

        roles = []
        permissions = []
        role_permission_count = 0

        if "staff_roles" in existing_tables:
            roles = [
                dict(row)
                for row in connection.execute(
                    text(
                        """
                        SELECT *
                        FROM public.staff_roles
                        ORDER BY role_code
                        """
                    )
                ).mappings().all()
            ]

        if "staff_permissions" in existing_tables:
            permissions = [
                dict(row)
                for row in connection.execute(
                    text(
                        """
                        SELECT *
                        FROM public.staff_permissions
                        ORDER BY permission_code
                        """
                    )
                ).mappings().all()
            ]

        if "staff_role_permissions" in existing_tables:
            role_permission_count = int(
                connection.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM public.staff_role_permissions
                        """
                    )
                ).scalar_one()
            )

        counts = {}

        for table_name in CORE_TABLES:
            if table_name not in existing_tables:
                continue

            quoted = (
                '"'
                + table_name.replace('"', '""')
                + '"'
            )

            counts[table_name] = int(
                connection.execute(
                    text(
                        f"""
                        SELECT COUNT(*)
                        FROM public.{quoted}
                        """
                    )
                ).scalar_one()
            )

    return {
        "database": "Supabase PostgreSQL",
        "core_table_status": table_status,
        "core_table_counts": counts,
        "roles": roles,
        "permissions": permissions,
        "role_permission_count": role_permission_count,
    }

