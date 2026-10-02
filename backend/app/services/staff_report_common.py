from __future__ import annotations

from datetime import date

from sqlalchemy import text

from app.database import engine
from app.services.staff_report_catalog import get_definition


def clean_filters(
    *,
    cycle_code: str | None,
    course_code: str | None,
    class_code: str | None,
    date_from: date | None,
    date_to: date | None,
) -> dict:
    if date_from and date_to and date_to < date_from:
        raise ValueError("date_to cannot be before date_from.")

    def clean(value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    return {
        "cycle_code": clean(cycle_code),
        "course_code": clean(course_code),
        "class_code": clean(class_code),
        "date_from": date_from,
        "date_to": date_to,
    }


def fetch_rows(sql: str, params: dict) -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(sql),
            params,
        ).mappings().all()
    return [dict(row) for row in rows]


def make_report(
    code: str,
    *,
    columns: list[tuple[str, str]],
    rows: list[dict],
    filters: dict,
    summary: dict | None = None,
) -> dict:
    definition = get_definition(code)
    if not definition:
        raise ValueError("Unknown report code.")

    return {
        "code": code,
        "category": definition["category"],
        "title": definition["title"],
        "description": definition["description"],
        "filters": filters,
        "columns": [
            {"key": key, "label": label}
            for key, label in columns
        ],
        "rows": rows,
        "summary": summary or {"record_count": len(rows)},
    }


def active_class_lateral() -> str:
    return """
        LEFT JOIN LATERAL (
            SELECT
                c2.class_code,
                c2.class_name,
                c2.class_group,
                c2.cycle_code
            FROM public.class_enrolments ce2
            JOIN public.classes c2
                ON c2.id = ce2.class_id
            WHERE
                ce2.registration_id = r.id
                AND ce2.status = 'Active'
            ORDER BY ce2.enrolled_at DESC
            LIMIT 1
        ) cl ON TRUE
    """


# ============================================================
# V3.6 REPORT FILTER TYPE FIX
# ============================================================

from sqlalchemy import (
    Date as _V36SADate,
    String as _V36SAString,
    bindparam as _v36_bindparam,
)
from sqlalchemy.exc import (
    OperationalError as _V36ReportOperationalError,
)


def fetch_rows(
    sql: str,
    params: dict,
) -> list[dict]:
    statement = text(sql)

    bind_types = {
        "cycle_code": _V36SAString(),
        "course_code": _V36SAString(),
        "class_code": _V36SAString(),
        "date_from": _V36SADate(),
        "date_to": _V36SADate(),
    }

    typed_binds = []

    for name, type_ in bind_types.items():
        if f":{name}" in sql:
            typed_binds.append(
                _v36_bindparam(
                    name,
                    type_=type_,
                )
            )

    if typed_binds:
        statement = statement.bindparams(
            *typed_binds
        )

    def _load():
        with engine.connect() as connection:
            rows = connection.execute(
                statement,
                params,
            ).mappings().all()

        return [
            dict(row)
            for row in rows
        ]

    try:
        return _load()
    except _V36ReportOperationalError:
        engine.dispose()
        return _load()


# ============================================================
# V4.6 REPORT PARAMETER TYPE FIX
# Includes module_type used by curriculum reports.
# ============================================================

from sqlalchemy import (
    Date as _V46SADate,
    String as _V46SAString,
    bindparam as _v46_bindparam,
    text as _v46_text,
)
from sqlalchemy.exc import (
    OperationalError as _V46OperationalError,
)


def fetch_rows(
    sql: str,
    params: dict,
) -> list[dict]:
    statement = _v46_text(
        sql
    )

    bind_types = {
        "cycle_code": _V46SAString(),
        "course_code": _V46SAString(),
        "class_code": _V46SAString(),
        "module_type": _V46SAString(),
        "date_from": _V46SADate(),
        "date_to": _V46SADate(),
    }

    typed_binds = []

    for name, type_ in bind_types.items():
        if (
            f":{name}" in sql
            and name in params
        ):
            typed_binds.append(
                _v46_bindparam(
                    name,
                    type_=type_,
                )
            )

    if typed_binds:
        statement = statement.bindparams(
            *typed_binds
        )

    def _load():
        with engine.connect() as connection:
            rows = connection.execute(
                statement,
                params,
            ).mappings().all()

        return [
            dict(
                row
            )
            for row in rows
        ]

    try:
        return _load()
    except _V46OperationalError:
        engine.dispose()
        return _load()
