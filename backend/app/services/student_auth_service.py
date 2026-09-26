from datetime import (
    datetime,
    timedelta,
    timezone,
)

from sqlalchemy import text

from app.database import engine
from app.services.email_service import (
    send_email,
)
from app.services.jwt_service import (
    create_student_access_token,
)
from app.services.security_service import (
    generate_temporary_password,
    hash_secret,
    validate_password,
    validate_pin,
    verify_secret,
)

# ============================================================
# SETTINGS
# ============================================================

MAX_FAILED_LOGIN_ATTEMPTS = 5

LOCK_MINUTES = 15


# ============================================================
# GET STUDENT ACCOUNT
# ============================================================

def get_student_account(
    student_number: str,
) -> dict | None:

    query = text(
        """
        SELECT
            id,
            student_number,
            password_hash,
            pin_hash,
            must_change_password,
            pin_created,
            account_status,
            failed_login_attempts,
            locked_until,
            last_login_at,
            password_changed_at,
            pin_changed_at,
            created_at,
            updated_at

        FROM public.student_accounts

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

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# GET STUDENT CONTACT
# ============================================================

def get_student_contact(
    student_number: str,
) -> dict | None:

    query = text(
        """
        SELECT
            student_number,
            first_name,
            middle_name,
            last_name,
            email,
            cell_number

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

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# CHECK STUDENT REGISTRATION
# ============================================================

def student_is_registered(
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
# BUILD STUDENT ACCOUNT EMAIL
# ============================================================

def build_student_account_email(
    student_number: str,
    first_name: str,
    temporary_password: str,
) -> str:

    return (
        f"Dear {first_name or 'Student'},\n\n"

        "Your Glen Moniques student account "
        "has been created successfully.\n\n"

        "Login Details:\n"
        f"Student Number: {student_number}\n"
        f"Temporary Password: "
        f"{temporary_password}\n\n"

        "You must change your temporary password "
        "after your first login.\n\n"

        "Your new password must:\n"
        "- Contain at least 8 characters\n"
        "- Include at least one uppercase letter\n"
        "- Include at least one number\n"
        "- Include at least one special character\n\n"

        "You must also create your own "
        "5-digit PIN.\n\n"

        "Your PIN:\n"
        "- Must contain exactly 5 digits\n"
        "- Must not start with zero\n"
        "- Must not contain identical consecutive "
        "digits such as 22, 33 or 44\n"
        "- Must not be an easy sequence "
        "such as 12345\n\n"

        "Do not share your password or PIN "
        "with anyone.\n\n"

        "Regards,\n"
        "Glen Moniques (Pty) Ltd"
    )


# ============================================================
# CREATE STUDENT ACCOUNT
# ============================================================

def create_student_account(
    student_number: str,
    send_credentials_email: bool = True,
) -> dict:

    if not student_is_registered(
        student_number
    ):

        raise ValueError(
            "The student must be registered "
            "before an account can be created."
        )

    existing_account = (
        get_student_account(
            student_number
        )
    )

    if existing_account:

        raise ValueError(
            "A student account already exists "
            "for this student number."
        )

    student = get_student_contact(
        student_number
    )

    if not student:

        raise ValueError(
            "Student record not found."
        )

    temporary_password = (
        generate_temporary_password()
    )

    password_hash = (
        hash_secret(
            temporary_password
        )
    )

    query = text(
        """
        INSERT INTO public.student_accounts (
            student_number,
            password_hash,
            pin_hash,
            must_change_password,
            pin_created,
            account_status,
            failed_login_attempts
        )
        VALUES (
            :student_number,
            :password_hash,
            NULL,
            TRUE,
            FALSE,
            'Active',
            0
        )

        RETURNING
            id,
            student_number,
            must_change_password,
            pin_created,
            account_status,
            created_at
        """
    )

    with engine.begin() as connection:

        row = connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),
                "password_hash": (
                    password_hash
                ),
            },
        ).mappings().first()

    student_email = (
        student.get(
            "email"
        )
    )

    email_sent = False
    email_error = None

    if (
        send_credentials_email
        and student_email
    ):

        try:

            send_email(
                to_email=(
                    student_email
                ),
                subject=(
                    "Glen Moniques - "
                    "Student Account"
                ),
                body=(
                    build_student_account_email(
                        student_number=(
                            student_number
                        ),
                        first_name=(
                            student.get(
                                "first_name"
                            )
                            or "Student"
                        ),
                        temporary_password=(
                            temporary_password
                        ),
                    )
                ),
            )

            email_sent = True

        except Exception as error:

            email_error = (
                str(error)
            )

            print(
                "WARNING: Student account "
                "email failed: "
                f"{error}"
            )

    elif not student_email:

        email_error = (
            "Student email address "
            "is not available."
        )

    return {
        "account": (
            dict(row)
        ),

        "credentials": {
            "temporary_password": (
                temporary_password
            ),

            "must_change_password": True,

            "pin_created": False,
        },

        "email": {
            "sent": (
                email_sent
            ),

            "recipient": (
                student_email
            ),

            "error": (
                email_error
            ),
        },
    }


# ============================================================
# REISSUE TEMPORARY PASSWORD
# ============================================================

def reissue_temporary_password(
    student_number: str,
) -> dict:

    account = get_student_account(
        student_number
    )

    if not account:

        raise ValueError(
            "Student account not found."
        )

    student = get_student_contact(
        student_number
    )

    if not student:

        raise ValueError(
            "Student record not found."
        )

    temporary_password = (
        generate_temporary_password()
    )

    password_hash = (
        hash_secret(
            temporary_password
        )
    )

    query = text(
        """
        UPDATE public.student_accounts

        SET
            password_hash = :password_hash,
            must_change_password = TRUE,
            failed_login_attempts = 0,
            locked_until = NULL,
            account_status = 'Active',
            password_changed_at = NULL,
            updated_at = now()

        WHERE student_number = :student_number
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),
                "password_hash": (
                    password_hash
                ),
            },
        )

    student_email = (
        student.get(
            "email"
        )
    )

    email_sent = False
    email_error = None

    if student_email:

        try:

            send_email(
                to_email=(
                    student_email
                ),
                subject=(
                    "Glen Moniques - "
                    "New Temporary Password"
                ),
                body=(
                    build_student_account_email(
                        student_number=(
                            student_number
                        ),
                        first_name=(
                            student.get(
                                "first_name"
                            )
                            or "Student"
                        ),
                        temporary_password=(
                            temporary_password
                        ),
                    )
                ),
            )

            email_sent = True

        except Exception as error:

            email_error = (
                str(error)
            )

    return {
        "student_number": (
            student_number
        ),

        "temporary_password": (
            temporary_password
        ),

        "must_change_password": True,

        "email_sent": (
            email_sent
        ),

        "email_error": (
            email_error
        ),
    }


# ============================================================
# CHECK ACCOUNT ACCESS
# ============================================================

def check_account_access(
    account: dict,
) -> None:

    status = (
        account.get(
            "account_status"
        )
    )

    if status in {
        "Suspended",
        "Disabled",
    }:

        raise ValueError(
            f"Student account is "
            f"{status.lower()}."
        )

    locked_until = (
        account.get(
            "locked_until"
        )
    )

    if not locked_until:

        return

    now = datetime.now(
        timezone.utc
    )

    if (
        locked_until.tzinfo
        is None
    ):

        locked_until = (
            locked_until.replace(
                tzinfo=timezone.utc
            )
        )

    if locked_until > now:

        raise ValueError(
            "Student account is "
            "temporarily locked."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.student_accounts

                SET
                    account_status = 'Active',
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    updated_at = now()

                WHERE student_number =
                    :student_number
                """
            ),
            {
                "student_number": (
                    account[
                        "student_number"
                    ]
                ),
            },
        )


# ============================================================
# RECORD FAILED LOGIN
# ============================================================

def record_failed_login(
    student_number: str,
) -> None:

    account = get_student_account(
        student_number
    )

    if not account:

        return

    failed_attempts = (
        account.get(
            "failed_login_attempts"
        )
        or 0
    ) + 1

    if (
        failed_attempts
        >= MAX_FAILED_LOGIN_ATTEMPTS
    ):

        locked_until = (
            datetime.now(
                timezone.utc
            )
            + timedelta(
                minutes=(
                    LOCK_MINUTES
                )
            )
        )

        query = text(
            """
            UPDATE public.student_accounts

            SET
                failed_login_attempts =
                    :failed_login_attempts,

                account_status = 'Locked',

                locked_until =
                    :locked_until,

                updated_at = now()

            WHERE student_number =
                :student_number
            """
        )

        parameters = {
            "student_number": (
                student_number
            ),

            "failed_login_attempts": (
                failed_attempts
            ),

            "locked_until": (
                locked_until
            ),
        }

    else:

        query = text(
            """
            UPDATE public.student_accounts

            SET
                failed_login_attempts =
                    :failed_login_attempts,

                updated_at = now()

            WHERE student_number =
                :student_number
            """
        )

        parameters = {
            "student_number": (
                student_number
            ),

            "failed_login_attempts": (
                failed_attempts
            ),
        }

    with engine.begin() as connection:

        connection.execute(
            query,
            parameters,
        )


# ============================================================
# RECORD SUCCESSFUL LOGIN
# ============================================================

def record_successful_login(
    student_number: str,
) -> None:

    query = text(
        """
        UPDATE public.student_accounts

        SET
            failed_login_attempts = 0,
            account_status = 'Active',
            locked_until = NULL,
            last_login_at = now(),
            updated_at = now()

        WHERE student_number =
            :student_number
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),
            },
        )


# ============================================================
# SETUP STUDENT PIN
# ============================================================

def setup_student_pin(
    student_number: str,
    password: str,
    pin: str,
) -> dict:

    validate_pin(
        pin
    )

    account = get_student_account(
        student_number
    )

    if not account:

        raise ValueError(
            "Student account not found."
        )

    check_account_access(
        account
    )

    if not verify_secret(
        password,
        account[
            "password_hash"
        ],
    ):

        record_failed_login(
            student_number
        )

        raise ValueError(
            "Student number or password "
            "is incorrect."
        )

    pin_hash = hash_secret(
        pin
    )

    query = text(
        """
        UPDATE public.student_accounts

        SET
            pin_hash = :pin_hash,
            pin_created = TRUE,
            pin_changed_at = now(),
            failed_login_attempts = 0,
            locked_until = NULL,
            account_status = 'Active',
            updated_at = now()

        WHERE student_number =
            :student_number
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),

                "pin_hash": (
                    pin_hash
                ),
            },
        )

    return {
        "student_number": (
            student_number
        ),

        "pin_created": True,

        "message": (
            "Student PIN created successfully."
        ),
    }


# ============================================================
# LOGIN WITH PASSWORD
# ============================================================

def login_with_password(
    student_number: str,
    password: str,
) -> dict:

    account = get_student_account(
        student_number
    )

    if not account:

        raise ValueError(
            "Student number or password "
            "is incorrect."
        )

    check_account_access(
        account
    )

    if not verify_secret(
        password,
        account[
            "password_hash"
        ],
    ):

        record_failed_login(
            student_number
        )

        raise ValueError(
            "Student number or password "
            "is incorrect."
        )

    record_successful_login(
        student_number
    )

    must_change_password = bool(
        account.get(
            "must_change_password"
        )
    )

    pin_created = bool(
        account.get(
            "pin_created"
        )
    )

    access_token = (
        create_student_access_token(
            student_number=(
                student_number
            ),

            login_method=(
                "password"
            ),

            must_change_password=(
                must_change_password
            ),

            pin_created=(
                pin_created
            ),
        )
    )

    return {
        "authenticated": True,

        "student_number": (
            student_number
        ),

        "login_method": (
            "password"
        ),

        "must_change_password": (
            must_change_password
        ),

        "pin_created": (
            pin_created
        ),

        "access_token": (
            access_token
        ),

        "token_type": (
            "bearer"
        ),
    }


# ============================================================
# LOGIN WITH PIN
# ============================================================

def login_with_pin(
    student_number: str,
    pin: str,
) -> dict:

    account = get_student_account(
        student_number
    )

    if not account:

        raise ValueError(
            "Student number or PIN "
            "is incorrect."
        )

    check_account_access(
        account
    )

    if account.get(
        "must_change_password"
    ):

        raise ValueError(
            "You must change your temporary "
            "password before using PIN login."
        )

    if not account.get(
        "pin_created"
    ):

        raise ValueError(
            "A PIN has not been created "
            "for this student account."
        )

    pin_hash = account.get(
        "pin_hash"
    )

    if (
        not pin_hash
        or not verify_secret(
            pin,
            pin_hash,
        )
    ):

        record_failed_login(
            student_number
        )

        raise ValueError(
            "Student number or PIN "
            "is incorrect."
        )

    record_successful_login(
        student_number
    )

    access_token = (
        create_student_access_token(
            student_number=(
                student_number
            ),

            login_method=(
                "pin"
            ),

            must_change_password=False,

            pin_created=True,
        )
    )

    return {
        "authenticated": True,

        "student_number": (
            student_number
        ),

        "login_method": (
            "pin"
        ),

        "must_change_password": False,

        "pin_created": True,

        "access_token": (
            access_token
        ),

        "token_type": (
            "bearer"
        ),
    }


# ============================================================
# CHANGE STUDENT PASSWORD
# ============================================================

def change_student_password(
    student_number: str,
    current_password: str,
    new_password: str,
) -> dict:

    validate_password(
        new_password
    )

    account = get_student_account(
        student_number
    )

    if not account:

        raise ValueError(
            "Student account not found."
        )

    check_account_access(
        account
    )

    if not verify_secret(
        current_password,
        account[
            "password_hash"
        ],
    ):

        record_failed_login(
            student_number
        )

        raise ValueError(
            "Current password is incorrect."
        )

    if verify_secret(
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
        hash_secret(
            new_password
        )
    )

    query = text(
        """
        UPDATE public.student_accounts

        SET
            password_hash = :password_hash,
            must_change_password = FALSE,
            password_changed_at = now(),
            failed_login_attempts = 0,
            locked_until = NULL,
            account_status = 'Active',
            updated_at = now()

        WHERE student_number =
            :student_number
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "student_number": (
                    student_number
                ),

                "password_hash": (
                    new_password_hash
                ),
            },
        )

    access_token = (
        create_student_access_token(
            student_number=(
                student_number
            ),

            login_method=(
                "password"
            ),

            must_change_password=False,

            pin_created=bool(
                account.get(
                    "pin_created"
                )
            ),
        )
    )

    return {
        "student_number": (
            student_number
        ),

        "password_changed": True,

        "must_change_password": False,

        "pin_created": bool(
            account.get(
                "pin_created"
            )
        ),

        "access_token": (
            access_token
        ),

        "token_type": (
            "bearer"
        ),
    }