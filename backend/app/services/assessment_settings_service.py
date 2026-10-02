from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy import text

from app.database import engine


SETTING_KEY = "assessment.default_pass_mark"
HARD_FALLBACK_PASS_MARK = Decimal("50")


def get_default_assessment_pass_mark() -> Decimal:
    with engine.connect() as connection:
        value = connection.execute(
            text(
                """
                SELECT setting_value
                FROM public.sms_system_settings
                WHERE
                    setting_key = :setting_key
                    AND is_active = TRUE
                LIMIT 1
                """
            ),
            {"setting_key": SETTING_KEY},
        ).scalar()

    if value is None:
        return HARD_FALLBACK_PASS_MARK

    raw = str(value).strip().strip('"')

    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return HARD_FALLBACK_PASS_MARK
