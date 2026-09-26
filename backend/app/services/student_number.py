from datetime import datetime

from sqlalchemy import text

from app.database import engine


def generate_student_number() -> str:
    """
    Generate a unique student number in the format YYYYNNNN.

    Example:
        20260001
        20260002
        20260003
    """

    current_year = datetime.now().year

    with engine.begin() as connection:

        result = connection.execute(
            text("""
                INSERT INTO public.student_number_sequences (
                    enrolment_year,
                    last_number
                )
                VALUES (
                    :year,
                    1
                )
                ON CONFLICT (enrolment_year)
                DO UPDATE SET
                    last_number =
                        public.student_number_sequences.last_number + 1,
                    updated_at = now()
                RETURNING last_number;
            """),
            {
                "year": current_year
            },
        )

        sequence_number = result.scalar_one()

    if sequence_number > 9999:
        raise ValueError(
            f"Student number capacity for {current_year} has been reached."
        )

    return f"{current_year}{sequence_number:04d}"