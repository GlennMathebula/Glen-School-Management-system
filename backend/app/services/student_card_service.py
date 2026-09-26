import os
from datetime import date
from uuid import UUID
from zipfile import Path

from sqlalchemy import text

from app.database import engine

# ============================================================
# CONFIG
# ============================================================

PUBLIC_BASE_URL = (
    os.getenv(
        "PUBLIC_BASE_URL",
        "http://127.0.0.1:8000",
    )
    .strip()
    .rstrip("/")
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(
    value,
    default: str = "",
) -> str:

    if value is None:
        return default

    value = str(
        value
    ).strip()

    if not value:
        return default

    return value


def build_full_name(
    first_name,
    middle_name,
    last_name,
) -> str:

    return " ".join(
        value
        for value in [
            clean_text(first_name),
            clean_text(middle_name),
            clean_text(last_name),
        ]
        if value
    )


def get_identity_value(
    national_id,
    alternate_id,
) -> str:

    national_id = clean_text(
        national_id
    )

    if national_id:
        return national_id

    return clean_text(
        alternate_id
    )


def validate_verification_token(
    token: str,
) -> str:

    try:

        return str(
            UUID(
                token
            )
        )

    except ValueError as error:

        raise ValueError(
            "Invalid student card verification token."
        ) from error


# ============================================================
# GET STUDENT REGISTRATION
# ============================================================

def get_student_card_registration(
    student_number: str,
) -> dict | None:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.registration_date,
            r.registration_status,
            r.cycle,
            r.expected_completion_date,
            r.program_start_date,

            a.first_name,
            a.middle_name,
            a.last_name,

            a.national_id,
            a.alternate_id,
            a.alt_id_type,

            c.course_name,
            c.qualification_type,
            c.nqf_level,
            c.credits

        FROM public.registrations r

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        WHERE
            r.student_number = :student_number

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
                },
            )
            .mappings()
            .first()
        )

    return (
        dict(
            row
        )
        if row
        else None
    )


# ============================================================
# GET EXISTING CARD
# ============================================================

def get_existing_student_card(
    registration_id: str,
) -> dict | None:

    query = text(
        """
        SELECT
            id,
            registration_id,
            student_number,
            verification_token,

            avatar_bucket,
            avatar_path,
            avatar_mime_type,
            avatar_updated_at,

            issued_date,
            expiry_date,
            card_status,

            created_at,
            updated_at

        FROM public.student_cards

        WHERE
            registration_id = CAST(
                :registration_id
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "registration_id": (
                        registration_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    return (
        dict(
            row
        )
        if row
        else None
    )


# ============================================================
# DETERMINE CARD STATUS
# ============================================================

def calculate_card_status(
    card_status: str,
    expiry_date: date,
) -> str:

    # Manually suspended/revoked cards stay that way.
    if card_status in {
        "Suspended",
        "Revoked",
    }:

        return card_status

    if expiry_date < date.today():

        return "Expired"

    return "Active"


# ============================================================
# ENSURE STUDENT CARD
# ============================================================

def ensure_student_card(
    student_number: str,
) -> dict:

    registration = (
        get_student_card_registration(
            student_number
        )
    )

    if not registration:

        raise ValueError(
            "Student registration not found."
        )

    if registration[
        "registration_status"
    ] not in {
        "Registered",
        "In Progress",
        "Completed",
    }:

        raise ValueError(
            
                "Student card is not available "
                "for this registration status."
            
        )

    expiry_date = (
        registration.get(
            "expected_completion_date"
        )
    )

    if not expiry_date:

        raise ValueError(
            
                "Student card cannot be issued because "
                "the registration has no expected "
                "completion date."
            
        )

    registration_id = str(
        registration[
            "registration_id"
        ]
    )

    existing_card = (
        get_existing_student_card(
            registration_id
        )
    )

    if existing_card:

        calculated_status = (
            calculate_card_status(
                existing_card[
                    "card_status"
                ],
                existing_card[
                    "expiry_date"
                ],
            )
        )

        if (
            calculated_status
            != existing_card[
                "card_status"
            ]
        ):

            with engine.begin() as connection:

                connection.execute(
                    text(
                        """
                        UPDATE public.student_cards

                        SET
                            card_status = :card_status,
                            updated_at = now()

                        WHERE
                            id = CAST(
                                :card_id
                                AS uuid
                            )
                        """
                    ),
                    {
                        "card_status": (
                            calculated_status
                        ),

                        "card_id": str(
                            existing_card[
                                "id"
                            ]
                        ),
                    },
                )

            existing_card[
                "card_status"
            ] = calculated_status

        return existing_card

    issued_date = (
        registration.get(
            "program_start_date"
        )
        or registration.get(
            "registration_date"
        )
        or date.today()
    )

    if issued_date > date.today():

        issued_date = (
            registration.get(
                "registration_date"
            )
            or date.today()
        )

    with engine.begin() as connection:

        created_card = (
            connection.execute(
                text(
                    """
                    INSERT INTO public.student_cards
                    (
                        registration_id,
                        student_number,
                        issued_date,
                        expiry_date,
                        card_status
                    )

                    VALUES
                    (
                        CAST(
                            :registration_id
                            AS uuid
                        ),
                        :student_number,
                        :issued_date,
                        :expiry_date,
                        'Active'
                    )

                    RETURNING
                        *
                    """
                ),
                {
                    "registration_id": (
                        registration_id
                    ),

                    "student_number": (
                        registration[
                            "student_number"
                        ]
                    ),

                    "issued_date": (
                        issued_date
                    ),

                    "expiry_date": (
                        expiry_date
                    ),
                },
            )
            .mappings()
            .one()
        )

    return dict(
        created_card
    )


# ============================================================
# BUILD STUDENT CARD DATA
# ============================================================

def get_student_card_data(
    student_number: str,
) -> dict:

    registration = (
        get_student_card_registration(
            student_number
        )
    )

    if not registration:

        raise ValueError(
            "Student registration not found."
        )

    card = ensure_student_card(
        student_number
    )

    full_name = build_full_name(
        registration[
            "first_name"
        ],
        registration[
            "middle_name"
        ],
        registration[
            "last_name"
        ],
    )

    identity_value = (
        get_identity_value(
            registration[
                "national_id"
            ],
            registration[
                "alternate_id"
            ],
        )
    )

    verification_token = str(
        card[
            "verification_token"
        ]
    )

    verification_url = (
        f"{PUBLIC_BASE_URL}"
        f"/api/public/student-card/verify/"
        f"{verification_token}"
    )

    return {
        "card_id": str(
            card[
                "id"
            ]
        ),

        "student_number": (
            registration[
                "student_number"
            ]
        ),

        "full_name": (
            full_name
        ),

        # Used internally to generate the barcode.
        # We do not have to display this as normal text
        # on the card.
        "identity_barcode_value": (
            identity_value
        ),

        "identity_type": (
            "National ID"
            if registration[
                "national_id"
            ]
            else clean_text(
                registration[
                    "alt_id_type"
                ],
                "Passport / Alternate ID",
            )
        ),

        "course": {
            "course_code": (
                registration[
                    "course_code"
                ]
            ),

            "course_name": (
                registration[
                    "course_name"
                ]
            ),

            "qualification_type": (
                registration[
                    "qualification_type"
                ]
            ),

            "nqf_level": (
                registration[
                    "nqf_level"
                ]
            ),

            "credits": (
                registration[
                    "credits"
                ]
            ),
        },

        "registration": {
            "cycle": (
                registration[
                    "cycle"
                ]
            ),

            "registration_status": (
                registration[
                    "registration_status"
                ]
            ),

            "registration_date": (
                registration[
                    "registration_date"
                ]
            ),
        },

        "card": {
            "issued_date": (
                card[
                    "issued_date"
                ]
            ),

            "expiry_date": (
                card[
                    "expiry_date"
                ]
            ),

            "card_status": (
                card[
                    "card_status"
                ]
            ),
        },

        "avatar": {
            "available": bool(
                card[
                    "avatar_path"
                ]
            ),

            "bucket": (
                card[
                    "avatar_bucket"
                ]
            ),

            "path": (
                card[
                    "avatar_path"
                ]
            ),

            "mime_type": (
                card[
                    "avatar_mime_type"
                ]
            ),

            "updated_at": (
                card[
                    "avatar_updated_at"
                ]
            ),
        },

        "verification": {
            "token": (
                verification_token
            ),

            "url": (
                verification_url
            ),
        },
    }


# ============================================================
# PUBLIC CARD VERIFICATION
# ============================================================

def verify_student_card(
    token: str,
) -> dict:

    token = (
        validate_verification_token(
            token
        )
    )

    query = text(
        """
        SELECT
            sc.id AS card_id,
            sc.student_number,
            sc.issued_date,
            sc.expiry_date,
            sc.card_status,

            r.registration_status,
            r.course_code,
            r.cycle,

            a.first_name,
            a.middle_name,
            a.last_name,

            c.course_name,
            c.nqf_level

        FROM public.student_cards sc

        JOIN public.registrations r
            ON r.id = sc.registration_id

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        WHERE
            sc.verification_token
            = CAST(
                :token
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "token": (
                        token
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return {
            "valid": False,
            "reason": (
                "Student card not found."
            ),
        }

    card = dict(
        row
    )

    status = calculate_card_status(
        card[
            "card_status"
        ],
        card[
            "expiry_date"
        ],
    )

    valid = (
        status == "Active"
        and card[
            "registration_status"
        ] in {
            "Registered",
            "In Progress",
        }
    )

    return {
        "valid": (
            valid
        ),

        "card_status": (
            status
        ),

        "student_number": (
            card[
                "student_number"
            ]
        ),

        "student_name": (
            build_full_name(
                card[
                    "first_name"
                ],
                card[
                    "middle_name"
                ],
                card[
                    "last_name"
                ],
            )
        ),

        "course_code": (
            card[
                "course_code"
            ]
        ),

        "course_name": (
            card[
                "course_name"
            ]
        ),

        "nqf_level": (
            card[
                "nqf_level"
            ]
        ),

        "cycle": (
            card[
                "cycle"
            ]
        ),

        "issued_date": (
            card[
                "issued_date"
            ]
        ),

        "expiry_date": (
            card[
                "expiry_date"
            ]
        ),
    }

# ============================================================
# GENERATE STUDENT CARD PDF
# ============================================================

def generate_student_card_document(
    student_number: str,
    ) -> Path:

    from pathlib import Path

    from app.pdfs.student_card_pdf import (
        generate_student_card_pdf,
    )

    data = get_student_card_data(
        student_number
    )

    output_directory = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "student_cards"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        output_directory
        / (
            f"Student_Card_"
            f"{student_number}.pdf"
        )
    )

    return (
        generate_student_card_pdf(
            output_path,
            data,
        )
    )
