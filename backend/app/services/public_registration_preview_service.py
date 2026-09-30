from __future__ import annotations

from sqlalchemy import text

from app.database import engine
from app.services.public_registration_service import (
    IDENTITY_VERIFICATION_ERROR,
    get_public_registration_application,
    identity_number_matches,
    public_registration_exists,
    resolve_registration_cycle,
    validate_registration_window,
)
from app.services.registration_service import (
    get_course_modules,
)


def _mask_email(
    email: str | None,
) -> str | None:
    if not email or "@" not in email:
        return None

    local, domain = email.split("@", 1)

    if len(local) <= 1:
        local_masked = "*"
    elif len(local) == 2:
        local_masked = f"{local[0]}*"
    else:
        local_masked = (
            local[0]
            + ("*" * min(len(local) - 2, 8))
            + local[-1]
        )

    return f"{local_masked}@{domain}"


def get_public_registration_preview(
    student_number: str,
    id_or_passport: str,
) -> dict:
    student_number = (
        student_number
        .strip()
        .upper()
    )

    id_or_passport = (
        id_or_passport
        .strip()
    )

    application = (
        get_public_registration_application(
            student_number
        )
    )

    if (
        not application
        or application.get("app_status")
        != "Accepted"
        or not identity_number_matches(
            application=application,
            id_or_passport=id_or_passport,
        )
    ):
        raise ValueError(
            IDENTITY_VERIFICATION_ERROR
        )

    if public_registration_exists(
        student_number
    ):
        raise ValueError(
            "This student has already been registered."
        )

    cycle = resolve_registration_cycle(
        application
    )

    validate_registration_window(
        cycle
    )

    course_code = (
        application.get(
            "qualification_id"
        )
    )

    with engine.connect() as connection:
        course = connection.execute(
            text(
                """
                SELECT
                    course_code,
                    course_name,
                    qualification_type,
                    nqf_level,
                    credits,
                    completion_months,
                    entry_requirements
                FROM public.courses
                WHERE course_code = :course_code
                LIMIT 1
                """
            ),
            {
                "course_code": course_code,
            },
        ).mappings().first()

    course = (
        dict(course)
        if course
        else {
            "course_code": course_code,
            "course_name": course_code,
        }
    )

    # IMPORTANT:
    # This is the same function used by register_student(),
    # so the preview matches the actual modules registered.
    modules = get_course_modules(
        course_code
    )

    if not modules:
        raise ValueError(
            "No active modules were found "
            f"for course {course_code}."
        )

    public_modules = []
    total_module_credits = 0

    for module in modules:
        credits = module.get("credits") or 0

        total_module_credits += credits

        public_modules.append(
            {
                "module_code": module.get(
                    "module_code"
                ),
                "module_name": module.get(
                    "module_name"
                ),
                "module_type": module.get(
                    "module_type"
                ),
                "nqf_level": module.get(
                    "nqf_level"
                ),
                "credits": credits,
            }
        )

    return {
        "verified": True,
        "student_number": student_number,
        "course": course,
        "cycle": {
            "cycle_code": cycle.get(
                "cycle_code"
            ),
            "cycle_name": cycle.get(
                "cycle_name"
            ),
            "registration_start_date": cycle.get(
                "registration_start_date"
            ),
            "registration_end_date": cycle.get(
                "registration_end_date"
            ),
            "program_start_date": cycle.get(
                "program_start_date"
            ),
            "expected_completion_date": cycle.get(
                "expected_completion_date"
            ),
        },
        "second_name_required": False,
        "email_masked": _mask_email(
            application.get("email")
        ),
        "modules": public_modules,
        "module_count": len(
            public_modules
        ),
        "module_credits": total_module_credits,
    }
