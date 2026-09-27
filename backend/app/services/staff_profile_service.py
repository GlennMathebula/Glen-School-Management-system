from sqlalchemy import text
from passlib.context import CryptContext

from app.database import engine


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


# ============================================================
# HELPERS
# ============================================================

def clean_required_text(
    value: str,
    field_name: str,
) -> str:

    value = (
        value
        or ""
    ).strip()

    if not value:

        raise ValueError(
            f"{field_name} is required."
        )

    return value


def clean_optional_text(
    value: str | None,
) -> str | None:

    if value is None:
        return None

    value = value.strip()

    return value or None


# ============================================================
# GET STAFF PROFILE
# ============================================================

def get_staff_profile(
    *,
    staff_code: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        sa.staff_code,
                        sa.role_code,
                        sa.is_active,
                        sa.must_change_password,
                        sa.must_change_pin,
                        sa.failed_login_attempts,
                        sa.locked_until,
                        sa.credentials_issued_at,
                        sa.password_changed_at,
                        sa.pin_changed_at,
                        sa.last_login_at,
                        sa.created_at AS account_created_at,

                        sr.role_name,
                        sr.description AS role_description,

                        e.id AS employee_id,
                        e.employee_number,
                        e.first_name,
                        e.middle_name,
                        e.last_name,
                        e.email,
                        e.phone_number,
                        e.job_title,
                        e.department,
                        e.employment_type,
                        e.employment_status,
                        e.start_date,
                        e.end_date,
                        e.requires_system_access

                    FROM public.staff_accounts sa

                    JOIN public.employees e
                        ON e.id = sa.employee_id

                    LEFT JOIN public.staff_roles sr
                        ON sr.role_code = sa.role_code

                    WHERE
                        sa.staff_code = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "staff_code": staff_code,
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Staff profile not found."
        )

    row = dict(
        row
    )

    full_name_parts = [
        row.get(
            "first_name"
        ),
        row.get(
            "middle_name"
        ),
        row.get(
            "last_name"
        ),
    ]

    full_name = " ".join(
        part
        for part in full_name_parts
        if part
    )

    return {
        "staff_code": row[
            "staff_code"
        ],

        "role": {
            "role_code": row[
                "role_code"
            ],
            "role_name": row[
                "role_name"
            ],
            "description": row[
                "role_description"
            ],
        },

        "employee": {
            "employee_id": str(
                row[
                    "employee_id"
                ]
            ),

            "employee_number": row[
                "employee_number"
            ],

            "first_name": row[
                "first_name"
            ],

            "middle_name": row[
                "middle_name"
            ],

            "last_name": row[
                "last_name"
            ],

            "full_name": full_name,

            "email": row[
                "email"
            ],

            "phone_number": row[
                "phone_number"
            ],

            "job_title": row[
                "job_title"
            ],

            "department": row[
                "department"
            ],

            "employment_type": row[
                "employment_type"
            ],

            "employment_status": row[
                "employment_status"
            ],

            "start_date": row[
                "start_date"
            ],

            "end_date": row[
                "end_date"
            ],

            "requires_system_access": row[
                "requires_system_access"
            ],
        },

        "account": {
            "is_active": row[
                "is_active"
            ],

            "must_change_password": row[
                "must_change_password"
            ],

            "must_change_pin": row[
                "must_change_pin"
            ],

            "failed_login_attempts": row[
                "failed_login_attempts"
            ],

            "locked_until": row[
                "locked_until"
            ],

            "credentials_issued_at": row[
                "credentials_issued_at"
            ],

            "password_changed_at": row[
                "password_changed_at"
            ],

            "pin_changed_at": row[
                "pin_changed_at"
            ],

            "last_login_at": row[
                "last_login_at"
            ],

            "account_created_at": row[
                "account_created_at"
            ],
        },
    }


# ============================================================
# UPDATE CONTACT DETAILS
# ============================================================

def update_staff_contact_details(
    *,
    staff_code: str,
    email: str | None = None,
    phone_number: str | None = None,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    email = clean_optional_text(
        email
    )

    phone_number = clean_optional_text(
        phone_number
    )

    with engine.begin() as connection:

        employee_row = (
            connection.execute(
                text(
                    """
                    SELECT
                        employee_id

                    FROM public.staff_accounts

                    WHERE
                        staff_code = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "staff_code": staff_code,
                },
            )
            .mappings()
            .first()
        )

        if not employee_row:

            raise ValueError(
                "Staff account not found."
            )

        connection.execute(
            text(
                """
                UPDATE public.employees

                SET
                    email = COALESCE(
                        :email,
                        email
                    ),

                    phone_number = COALESCE(
                        :phone_number,
                        phone_number
                    ),

                    updated_at = now()

                WHERE
                    id = :employee_id
                """
            ),
            {
                "email": email,
                "phone_number": (
                    phone_number
                ),
                "employee_id": (
                    employee_row[
                        "employee_id"
                    ]
                ),
            },
        )

    return get_staff_profile(
        staff_code=staff_code
    )


# ============================================================
# CHANGE PASSWORD
# ============================================================

def change_staff_password(
    *,
    staff_code: str,
    current_password: str,
    new_password: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    current_password = (
        clean_required_text(
            current_password,
            "Current password",
        )
    )

    new_password = (
        clean_required_text(
            new_password,
            "New password",
        )
    )

    if len(
        new_password
    ) < 8:

        raise ValueError(
            "New password must be at least "
            "8 characters."
        )

    with engine.begin() as connection:

        account = (
            connection.execute(
                text(
                    """
                    SELECT
                        password_hash

                    FROM public.staff_accounts

                    WHERE
                        staff_code = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "staff_code": staff_code,
                },
            )
            .mappings()
            .first()
        )

        if not account:

            raise ValueError(
                "Staff account not found."
            )

        if not pwd_context.verify(
            current_password,
            account[
                "password_hash"
            ],
        ):

            raise ValueError(
                "Current password is incorrect."
            )

        if pwd_context.verify(
            new_password,
            account[
                "password_hash"
            ],
        ):

            raise ValueError(
                "New password must be different "
                "from the current password."
            )

        new_password_hash = (
            pwd_context.hash(
                new_password
            )
        )

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts

                SET
                    password_hash
                        = :password_hash,

                    must_change_password
                        = FALSE,

                    password_changed_at
                        = now(),

                    updated_at
                        = now()

                WHERE
                    staff_code = :staff_code
                """
            ),
            {
                "password_hash": (
                    new_password_hash
                ),
                "staff_code": (
                    staff_code
                ),
            },
        )

    return {
        "staff_code": staff_code,
        "password_changed": True,
    }


# ============================================================
# CHANGE PIN
# ============================================================

def change_staff_pin(
    *,
    staff_code: str,
    current_pin: str,
    new_pin: str,
) -> dict:

    staff_code = clean_required_text(
        staff_code,
        "Staff code",
    )

    current_pin = clean_required_text(
        current_pin,
        "Current PIN",
    )

    new_pin = clean_required_text(
        new_pin,
        "New PIN",
    )

    if (
        len(
            current_pin
        )
        != 5

        or not current_pin.isdigit()
    ):

        raise ValueError(
            "Current PIN must contain "
            "exactly 5 digits."
        )

    if (
        len(
            new_pin
        )
        != 5

        or not new_pin.isdigit()
    ):

        raise ValueError(
            "New PIN must contain exactly "
            "5 digits."
        )

    with engine.begin() as connection:

        account = (
            connection.execute(
                text(
                    """
                    SELECT
                        pin_hash

                    FROM public.staff_accounts

                    WHERE
                        staff_code = :staff_code

                    LIMIT 1
                    """
                ),
                {
                    "staff_code": staff_code,
                },
            )
            .mappings()
            .first()
        )

        if not account:

            raise ValueError(
                "Staff account not found."
            )

        if not pwd_context.verify(
            current_pin,
            account[
                "pin_hash"
            ],
        ):

            raise ValueError(
                "Current PIN is incorrect."
            )

        if pwd_context.verify(
            new_pin,
            account[
                "pin_hash"
            ],
        ):

            raise ValueError(
                "New PIN must be different "
                "from the current PIN."
            )

        new_pin_hash = (
            pwd_context.hash(
                new_pin
            )
        )

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts

                SET
                    pin_hash = :pin_hash,

                    must_change_pin = FALSE,

                    pin_changed_at = now(),

                    updated_at = now()

                WHERE
                    staff_code = :staff_code
                """
            ),
            {
                "pin_hash": (
                    new_pin_hash
                ),
                "staff_code": (
                    staff_code
                ),
            },
        )

    return {
        "staff_code": staff_code,
        "pin_changed": True,
    }