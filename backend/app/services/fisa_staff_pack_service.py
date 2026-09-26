from pathlib import Path

from sqlalchemy import text

from app.database import engine
from app.pdfs.assessment.fisa_attendance_register_pdf import (
    generate_fisa_attendance_register_pdf,
)
from app.pdfs.assessment.fisa_seating_order_pdf import (
    generate_fisa_seating_order_pdf,
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


def get_fisa_sitting_data(
    sitting_reference: str,
) -> dict:
    sitting_query = text(
        """
        SELECT
            fs.id,
            fs.sitting_reference,
            fs.course_code,
            fs.cycle_code,
            fs.assessment_date,
            fs.reporting_time,
            fs.start_time,
            fs.end_time,
            fs.venue,
            fs.assessment_centre,
            fs.instructions,
            fs.status,

            c.course_name

        FROM public.fisa_sittings fs

        JOIN public.courses c
            ON c.course_code = fs.course_code

        WHERE
            fs.sitting_reference
            = :sitting_reference

        LIMIT 1
        """
    )

    candidate_query = text(
        """
        SELECT
            fsc.seat_number,
            fsc.admission_status,
            fsc.attendance_status,

            r.student_number,

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

        JOIN public.applications a
            ON a.id = r.application_id

        WHERE
            fs.sitting_reference
            = :sitting_reference

            AND fsc.admission_status
            = 'Admitted'

        ORDER BY
            fsc.seat_number,
            r.student_number
        """
    )

    with engine.connect() as connection:
        sitting = (
            connection.execute(
                sitting_query,
                {
                    "sitting_reference": (
                        sitting_reference
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not sitting:
            raise ValueError(
                "FISA sitting not found."
            )

        candidates = (
            connection.execute(
                candidate_query,
                {
                    "sitting_reference": (
                        sitting_reference
                    ),
                },
            )
            .mappings()
            .all()
        )

    data = dict(
        sitting
    )

    if data.get("status") not in {
        "Published",
        "Completed",
    }:
        raise ValueError(
            "The FISA sitting is not available for staff documents."
        )

    candidate_list = []

    for row in candidates:
        item = dict(
            row
        )

        student_name = " ".join(
            value
            for value in [
                item.get(
                    "first_name"
                ),
                item.get(
                    "middle_name"
                ),
                item.get(
                    "last_name"
                ),
            ]
            if value
        )

        candidate_list.append(
            {
                "seat_number": (
                    item.get(
                        "seat_number"
                    )
                ),
                "student_number": (
                    item.get(
                        "student_number"
                    )
                ),
                "identity_number": (
                    item.get(
                        "national_id"
                    )
                    or item.get(
                        "alternate_id"
                    )
                    or ""
                ),
                "student_name": (
                    student_name
                ),
                "attendance_status": (
                    item.get(
                        "attendance_status"
                    )
                ),
            }
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

    data["candidates"] = (
        candidate_list
    )

    return data


def get_output_directory() -> Path:
    path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "assessment"
        / "fisa"
        / "staff"
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def generate_fisa_seating_order(
    sitting_reference: str,
) -> dict:
    data = get_fisa_sitting_data(
        sitting_reference
    )

    output_path = (
        get_output_directory()
        / (
            f"FISA-SEATING-ORDER-"
            f"{sitting_reference}.pdf"
        )
    )

    generate_fisa_seating_order_pdf(
        output_path,
        data,
    )

    return {
        "sitting_reference": (
            sitting_reference
        ),
        "document": (
            "FISA Seating Order"
        ),
        "candidates": (
            len(
                data["candidates"]
            )
        ),
        "pdf_path": (
            str(output_path)
        ),
    }


def generate_fisa_attendance_register(
    sitting_reference: str,
) -> dict:
    data = get_fisa_sitting_data(
        sitting_reference
    )

    output_path = (
        get_output_directory()
        / (
            f"FISA-ATTENDANCE-REGISTER-"
            f"{sitting_reference}.pdf"
        )
    )

    generate_fisa_attendance_register_pdf(
        output_path,
        data,
    )

    return {
        "sitting_reference": (
            sitting_reference
        ),
        "document": (
            "FISA Attendance Register"
        ),
        "candidates": (
            len(
                data["candidates"]
            )
        ),
        "pdf_path": (
            str(output_path)
        ),
    }