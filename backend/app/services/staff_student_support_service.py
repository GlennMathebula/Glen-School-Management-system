from __future__ import annotations

from uuid import UUID

from sqlalchemy import text

from app.database import engine


def _uuid(value: str, label: str) -> str:
    value = str(value or "").strip()

    try:
        UUID(value)
    except ValueError as error:
        raise ValueError(f"Invalid {label}.") from error

    return value


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


def list_student_support_tickets(
    *,
    status: str | None = None,
) -> list[dict]:
    params = {}
    where = ""

    if status:
        where = "WHERE status = :status"
        params["status"] = str(status).strip()

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT *
                FROM public.support_tickets
                {where}
                ORDER BY
                    COALESCE(updated_at, created_at) DESC
                """
            ),
            params,
        ).mappings().all()

    return [dict(row) for row in rows]


def get_student_support_ticket(ticket_id: str) -> dict:
    ticket_id = _uuid(ticket_id, "ticket ID")

    with engine.connect() as connection:
        ticket = connection.execute(
            text(
                """
                SELECT *
                FROM public.support_tickets
                WHERE id = CAST(:ticket_id AS uuid)
                LIMIT 1
                """
            ),
            {"ticket_id": ticket_id},
        ).mappings().first()

        if not ticket:
            raise ValueError("Student support ticket was not found.")

        messages = connection.execute(
            text(
                """
                SELECT *
                FROM public.support_ticket_messages
                WHERE ticket_id = CAST(:ticket_id AS uuid)
                ORDER BY created_at, id
                """
            ),
            {"ticket_id": ticket_id},
        ).mappings().all()

    return {
        "ticket": dict(ticket),
        "messages": [dict(row) for row in messages],
    }


def reply_student_support_ticket(
    *,
    staff_code: str,
    ticket_id: str,
    message_body: str,
) -> dict:
    ticket_id = _uuid(ticket_id, "ticket ID")
    message_body = str(message_body or "").strip()

    if not message_body:
        raise ValueError("Message is required.")

    with engine.begin() as connection:
        ticket = connection.execute(
            text(
                """
                SELECT *
                FROM public.support_tickets
                WHERE id = CAST(:ticket_id AS uuid)
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"ticket_id": ticket_id},
        ).mappings().first()

        if not ticket:
            raise ValueError("Student support ticket was not found.")

        if str(ticket.get("status") or "").strip().lower() in {
            "closed",
            "resolved",
        }:
            raise ValueError("This support ticket is closed.")

        cols = _columns(connection, "support_ticket_messages")

        ticket_col = next(
            (c for c in ("ticket_id", "support_ticket_id") if c in cols),
            None,
        )
        message_col = next(
            (c for c in ("message_body", "message", "body") if c in cols),
            None,
        )
        sender_type_col = next(
            (c for c in ("sender_type", "sender_role") if c in cols),
            None,
        )
        sender_code_col = next(
            (
                c
                for c in (
                    "sender_code",
                    "sender_staff_code",
                    "staff_code",
                    "sender_reference",
                )
                if c in cols
            ),
            None,
        )

        if not ticket_col or not message_col:
            raise ValueError(
                "Support message table schema is not compatible with staff replies."
            )

        insert_cols = [ticket_col, message_col]
        values = ["CAST(:ticket_id AS uuid)", ":message_body"]
        params = {
            "ticket_id": ticket_id,
            "message_body": message_body,
            "staff_code": staff_code,
        }

        if sender_type_col:
            insert_cols.append(sender_type_col)
            values.append(":sender_type")
            params["sender_type"] = "Staff"

        if sender_code_col:
            insert_cols.append(sender_code_col)
            values.append(":staff_code")

        sql_cols = ", ".join(f'"{col}"' for col in insert_cols)

        row = connection.execute(
            text(
                f"""
                INSERT INTO public.support_ticket_messages (
                    {sql_cols}
                )
                VALUES (
                    {", ".join(values)}
                )
                RETURNING *
                """
            ),
            params,
        ).mappings().first()

        ticket_cols = _columns(connection, "support_tickets")
        sets = []

        if "assigned_staff_code" in ticket_cols:
            sets.append(
                "assigned_staff_code = COALESCE(assigned_staff_code, :staff_code)"
            )

        if "status" in ticket_cols:
            sets.append("status = 'AwaitingStudent'")

        if "updated_at" in ticket_cols:
            sets.append("updated_at = NOW()")

        if sets:
            connection.execute(
                text(
                    f"""
                    UPDATE public.support_tickets
                    SET {", ".join(sets)}
                    WHERE id = CAST(:ticket_id AS uuid)
                    """
                ),
                {
                    "ticket_id": ticket_id,
                    "staff_code": staff_code,
                },
            )

    return dict(row)


def update_student_support_status(
    *,
    staff_code: str,
    ticket_id: str,
    status: str,
) -> dict:
    ticket_id = _uuid(ticket_id, "ticket ID")
    status = str(status or "").strip()

    with engine.begin() as connection:
        cols = _columns(connection, "support_tickets")

        if "status" not in cols:
            raise ValueError("Support ticket table has no status column.")

        sets = ["status = :status"]

        if "assigned_staff_code" in cols:
            sets.append(
                "assigned_staff_code = COALESCE(assigned_staff_code, :staff_code)"
            )

        if "updated_at" in cols:
            sets.append("updated_at = NOW()")

        if "closed_at" in cols:
            sets.append(
                """
                closed_at = CASE
                    WHEN :status IN ('Closed', 'Resolved')
                    THEN COALESCE(closed_at, NOW())
                    ELSE NULL
                END
                """
            )

        row = connection.execute(
            text(
                f"""
                UPDATE public.support_tickets
                SET {", ".join(sets)}
                WHERE id = CAST(:ticket_id AS uuid)
                RETURNING *
                """
            ),
            {
                "ticket_id": ticket_id,
                "status": status,
                "staff_code": staff_code,
            },
        ).mappings().first()

    if not row:
        raise ValueError("Student support ticket was not found.")

    return dict(row)
