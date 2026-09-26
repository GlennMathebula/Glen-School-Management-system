from pathlib import Path

from sqlalchemy import text

from app.database import engine
from app.pdfs.assessment.fisa_admission_letter_pdf import (
    generate_fisa_admission_letter_pdf,
)


def format_date(value) -> str:
    if value is None:
        return ""

    try:
        return value.strftime(
            "%d %B %Y"
        )
    except AttributeError:
        return str(value)


def format_time(value) -> str:
    if value is None:
        return ""

    try:
        return value.strftime(
            "%H:%M"
        )
    except AttributeError:
        return str(value)


def get_admission_data(
    student_number: str,
    sitting_reference: str,
) -> dict:
    query = text(
        """
        SELECT
            fs.id AS sitting_id,
            fs.sitting_reference,
            fs.assessment_date,
            fs.reporting_time,
            fs.start_time,
            fs.end_time,
            fs.venue,
            fs.assessment_centre,
            fs.instructions,
            fs.status AS sitting_status,

            fsc.seat_number,
            fsc.admission_status,

            r.student_number,
            r.course_code,

            c.course_name,

            a.first_name,
            a.middle_name,
            a.last_name,
            a.national_id,
            a.alternate_id

        FROM public.fisa_sitting_candidates fsc

        JOIN public.fisa_sittings fs
            ON fs.id = fsc.sitting_id

        JOIN public.registrations r
            ON r.id = fsc.registration_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        JOIN public.applications a
            ON a.id = r.application_id

        WHERE
            r.student_number = :student_number
            AND fs.sitting_reference = :sitting_reference

        LIMIT 1
        """
    )

    with engine.connect() as connection:
        row = (
            connection.execute(
                query,
                {
                    "student_number": (
                        student_number
                    ),
                    "sitting_reference": (
                        sitting_reference
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:
        raise ValueError(
            "FISA sitting admission record not found."
        )

    data = dict(row)

    if (
        data.get("sitting_status")
        != "Published"
    ):
        raise ValueError(
            "The FISA sitting has not yet been published."
        )

    if (
        data.get("admission_status")
        != "Admitted"
    ):
        raise ValueError(
            "The learner has not been admitted to this FISA sitting."
        )

    student_name = " ".join(
        value
        for value in [
            data.get("first_name"),
            data.get("middle_name"),
            data.get("last_name"),
        ]
        if value
    )

    data["student_name"] = (
        student_name
    )

    data["identity_number"] = (
        data.get("national_id")
        or data.get("alternate_id")
        or ""
    )

    data["assessment_date"] = (
        format_date(
            data.get(
                "assessment_date"
            )
        )
    )

    data["reporting_time"] = (
        format_time(
            data.get(
                "reporting_time"
            )
        )
    )

    data["start_time"] = (
        format_time(
            data.get(
                "start_time"
            )
        )
    )

    data["end_time"] = (
        format_time(
            data.get(
                "end_time"
            )
        )
    )

    return data


def generate_student_fisa_admission_letter(
    student_number: str,
    sitting_reference: str,
) -> dict:
    data = get_admission_data(
        student_number,
        sitting_reference,
    )

    output_dir = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "assessment"
        / "fisa"
        / "admission_letters"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_dir
        / (
            f"FISA-ADMISSION-"
            f"{student_number}-"
            f"{sitting_reference}.pdf"
        )
    )

    generate_fisa_admission_letter_pdf(
        output_path,
        data,
    )

    return {
        "student_number": (
            student_number
        ),
        "sitting_reference": (
            sitting_reference
        ),
        "status": (
            "Generated"
        ),
        "pdf_path": (
            str(output_path)
        ),
    }