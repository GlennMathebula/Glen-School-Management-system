from datetime import date

from sqlalchemy import text

from app.database import engine
from app.services.registration_service import (
    register_student,
)

# ============================================================
# PUBLIC ERROR MESSAGE
# ============================================================

IDENTITY_VERIFICATION_ERROR = (
    "The information provided could not be verified "
    "against an accepted application."
)


# ============================================================
# NORMALISE TEXT
# ============================================================

def normalise_text(
    value: str | None,
) -> str:

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .casefold()
        .split()
    )


# ============================================================
# GET APPLICATION FOR PUBLIC REGISTRATION
# ============================================================

def get_public_registration_application(
    student_number: str,
) -> dict | None:

    query = text(
        """
        SELECT
            id,
            student_number,
            qualification_id,

            national_id,
            alternate_id,
            alt_id_type,

            first_name,
            middle_name,
            last_name,
            birth_date,

            app_status,
            application_cycle,

            sponsor_name,
            email

        FROM public.applications

        WHERE student_number = :student_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),
            },
        ).mappings().first()

    return dict(row) if row else None


# ============================================================
# CHECK EXISTING REGISTRATION
# ============================================================

def public_registration_exists(
    student_number: str,
) -> bool:

    query = text(
        """
        SELECT 1

        FROM public.registrations

        WHERE student_number = :student_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),
            },
        ).first()

    return row is not None


# ============================================================
# VERIFY ID / PASSPORT
# ============================================================

def identity_number_matches(
    application: dict,
    id_or_passport: str,
) -> bool:

    supplied_identity = (
        normalise_text(
            id_or_passport
        )
    )

    national_id = (
        normalise_text(
            application.get(
                "national_id"
            )
        )
    )

    alternate_id = (
        normalise_text(
            application.get(
                "alternate_id"
            )
        )
    )

    if not supplied_identity:
        return False

    return supplied_identity in {
        national_id,
        alternate_id,
    }


# ============================================================
# VERIFY APPLICATION IDENTITY
# ============================================================

def verify_registration_identity(
    application: dict,
    id_or_passport: str,
    first_name: str,
    second_name: str | None,
    last_name: str,
    birth_date: date,
) -> bool:

    if application.get(
        "app_status"
    ) != "Accepted":

        return False

    if not identity_number_matches(
        application=application,
        id_or_passport=id_or_passport,
    ):

        return False

    if (
        normalise_text(
            application.get(
                "first_name"
            )
        )
        != normalise_text(
            first_name
        )
    ):

        return False

    application_middle_name = (
        normalise_text(
            application.get(
                "middle_name"
            )
        )
    )

    supplied_second_name = (
        normalise_text(
            second_name
        )
    )

    if (
        supplied_second_name
        and application_middle_name
        != supplied_second_name
    ):

        return False

    if (
        normalise_text(
            application.get(
                "last_name"
            )
        )
        != normalise_text(
            last_name
        )
    ):

        return False

    application_birth_date = (
        application.get(
            "birth_date"
        )
    )

    if (
        application_birth_date
        != birth_date
    ):

        return False

    return True


# ============================================================
# GET CYCLE BY APPLICATION CYCLE
# ============================================================

def get_cycle_by_application_cycle(
    application_cycle: str,
    course_code: str,
) -> dict | None:

    query = text(
        """
        SELECT
            c.id,
            c.cycle_code,
            c.cycle_name,

            c.registration_start_date,
            c.registration_end_date,

            c.program_start_date,
            c.expected_completion_date,

            c.status

        FROM public.cycles c

        JOIN public.cycle_courses cc
            ON cc.cycle_id = c.id

        WHERE
            (
                LOWER(TRIM(c.cycle_code))
                    = LOWER(TRIM(:application_cycle))

                OR

                LOWER(TRIM(c.cycle_name))
                    = LOWER(TRIM(:application_cycle))
            )

            AND cc.course_code = :course_code

            AND cc.is_active = true

            AND c.status = 'Active'

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "application_cycle": (
                    application_cycle
                ),
                "course_code": (
                    course_code
                ),
            },
        ).mappings().first()

    return dict(row) if row else None


# ============================================================
# FIND SINGLE ACTIVE CYCLE
# ============================================================

def get_single_active_cycle_for_course(
    course_code: str,
) -> dict | None:

    query = text(
        """
        SELECT
            c.id,
            c.cycle_code,
            c.cycle_name,

            c.registration_start_date,
            c.registration_end_date,

            c.program_start_date,
            c.expected_completion_date,

            c.status

        FROM public.cycles c

        JOIN public.cycle_courses cc
            ON cc.cycle_id = c.id

        WHERE
            cc.course_code = :course_code

            AND cc.is_active = true

            AND c.status = 'Active'

        ORDER BY
            c.registration_start_date NULLS FIRST,
            c.created_at

        LIMIT 2
        """
    )

    with engine.connect() as connection:

        rows = connection.execute(
            query,
            {
                "course_code": (
                    course_code
                ),
            },
        ).mappings().all()

    if len(rows) != 1:
        return None

    return dict(
        rows[0]
    )


# ============================================================
# RESOLVE REGISTRATION CYCLE
# ============================================================

def resolve_registration_cycle(
    application: dict,
) -> dict:

    course_code = (
        application.get(
            "qualification_id"
        )
    )

    if not course_code:

        raise ValueError(
            "The qualification for this application "
            "has not been configured."
        )

    application_cycle = (
        application.get(
            "application_cycle"
        )
    )

    cycle = None

    if application_cycle:

        cycle = (
            get_cycle_by_application_cycle(
                application_cycle=(
                    str(
                        application_cycle
                    )
                ),
                course_code=(
                    course_code
                ),
            )
        )

    else:

        cycle = (
            get_single_active_cycle_for_course(
                course_code
            )
        )

    if not cycle:

        raise ValueError(
            "A valid registration cycle could not "
            "be determined for this application."
        )

    return cycle


# ============================================================
# CHECK REGISTRATION WINDOW
# ============================================================

def validate_registration_window(
    cycle: dict,
) -> None:

    today = date.today()

    registration_start_date = (
        cycle.get(
            "registration_start_date"
        )
    )

    registration_end_date = (
        cycle.get(
            "registration_end_date"
        )
    )

    if (
        registration_start_date
        and today
        < registration_start_date
    ):

        raise ValueError(
            "Registration for this intake "
            "has not opened yet."
        )

    if (
        registration_end_date
        and today
        > registration_end_date
    ):

        raise ValueError(
            "Registration for this intake "
            "has already closed."
        )


# ============================================================
# PUBLIC STUDENT REGISTRATION
# ============================================================

def register_student_publicly(
    student_number: str,
    id_or_passport: str,
    first_name: str,
    second_name: str | None,
    last_name: str,
    birth_date: date,
) -> dict:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # APPLICATION LOOKUP
    # --------------------------------------------------------

    application = (
        get_public_registration_application(
            student_number
        )
    )

    if not application:

        raise ValueError(
            IDENTITY_VERIFICATION_ERROR
        )

    # --------------------------------------------------------
    # VERIFY ALL IDENTITY DETAILS
    # --------------------------------------------------------

    verified = (
        verify_registration_identity(
            application=application,
            id_or_passport=id_or_passport,
            first_name=first_name,
            second_name=second_name,
            last_name=last_name,
            birth_date=birth_date,
        )
    )

    if not verified:

        raise ValueError(
            IDENTITY_VERIFICATION_ERROR
        )

    # --------------------------------------------------------
    # DUPLICATE REGISTRATION
    # --------------------------------------------------------

    if public_registration_exists(
        student_number
    ):

        raise ValueError(
            "This student has already been registered."
        )

    # --------------------------------------------------------
    # RESOLVE CYCLE
    # --------------------------------------------------------

    cycle = (
        resolve_registration_cycle(
            application
        )
    )

    # --------------------------------------------------------
    # REGISTRATION WINDOW
    # --------------------------------------------------------

    validate_registration_window(
        cycle
    )

    # --------------------------------------------------------
    # PROGRAMME DATES
    # --------------------------------------------------------

    program_start_date = (
        cycle.get(
            "program_start_date"
        )
    )

    expected_completion_date = (
        cycle.get(
            "expected_completion_date"
        )
    )

    if not program_start_date:

        raise ValueError(
            "The programme start date "
            "has not been configured."
        )

    # --------------------------------------------------------
    # CALL EXISTING REGISTRATION PIPELINE
    #
    # This existing service handles:
    #
    # - accepted application validation
    # - course validation
    # - module registration
    # - registration creation
    # - POPIA registration date
    # - student account creation
    # - temporary password
    # - Proof of Registration
    # - registration email
    # --------------------------------------------------------

    result = (
        register_student(
            student_number=(
                student_number
            ),
            funding_type=None,
            cycle=(
                cycle[
                    "cycle_code"
                ]
            ),
            program_start_date=(
                program_start_date
            ),
            expected_completion_date=(
                expected_completion_date
            ),
        )
    )

    # --------------------------------------------------------
    # PUBLIC RESPONSE
    # --------------------------------------------------------

    return {
        "student_number": (
            student_number
        ),

        "registration_status": (
            "Registered"
        ),

        "cycle": (
            cycle.get(
                "cycle_code"
            )
        ),

        "cycle_name": (
            cycle.get(
                "cycle_name"
            )
        ),

        "program_start_date": (
            program_start_date
        ),

        "expected_completion_date": (
            expected_completion_date
        ),

        "registration": (
            result
        ),
    }