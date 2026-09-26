from datetime import date

from sqlalchemy import text

from app.database import engine

# ============================================================
# GET CALENDAR DAY
# ============================================================

def get_calendar_day(
    calendar_date: date,
) -> dict | None:

    query = text(
        """
        SELECT
            id,
            calendar_date,
            calendar_year,
            day_type,
            description,
            is_training_day,
            source,
            source_reference,
            is_manual_override

        FROM public.academic_calendar_dates

        WHERE calendar_date = :calendar_date

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "calendar_date": calendar_date,
            },
        ).mappings().first()

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# ENSURE YEAR EXISTS
# ============================================================

def ensure_calendar_year(
    target_year: int,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                SELECT
                    public.ensure_academic_calendar_year(
                        :target_year
                    )
                """
            ),
            {
                "target_year": target_year,
            },
        )


# ============================================================
# CHECK TRAINING DAY
# ============================================================

def is_training_day(
    calendar_date: date,
) -> bool:

    ensure_calendar_year(
        calendar_date.year
    )

    calendar_day = get_calendar_day(
        calendar_date
    )

    if not calendar_day:

        return False

    return bool(
        calendar_day[
            "is_training_day"
        ]
    )


# ============================================================
# REQUIRE TRAINING DAY
# ============================================================

def require_training_day(
    calendar_date: date,
) -> dict:

    ensure_calendar_year(
        calendar_date.year
    )

    calendar_day = get_calendar_day(
        calendar_date
    )

    if not calendar_day:

        raise ValueError(
            "The academic calendar does not "
            "contain this date."
        )

    if not calendar_day[
        "is_training_day"
    ]:

        description = (
            calendar_day.get(
                "description"
            )
            or calendar_day.get(
                "day_type"
            )
            or "Non-training day"
        )

        raise ValueError(
            f"Classes cannot be scheduled on "
            f"{calendar_date}. "
            f"{description}."
        )

    return calendar_day