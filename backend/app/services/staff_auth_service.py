import html
import secrets
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
from app.services.security_service import (
    hash_secret,
    validate_password,
    validate_pin,
    verify_secret,
)
from app.services.staff_jwt_service import (
    create_staff_access_token,
    create_staff_challenge_token,
    decode_staff_challenge_token,
)

# ============================================================
# SETTINGS
# ============================================================

MAX_FAILED_LOGIN_ATTEMPTS = 5

LOCK_MINUTES = 15

OTP_EXPIRE_MINUTES = 10

OTP_MAX_ATTEMPTS = 5


# ============================================================
# HELPERS
# ============================================================

def _now_utc() -> datetime:

    return datetime.now(
        timezone.utc
    )


def _normalise_staff_code(
    staff_code: str,
) -> str:

    return str(
        staff_code
        or ""
    ).strip().upper()


def _full_name(
    account: dict,
) -> str:

    return " ".join(
        str(value).strip()
        for value in [
            account.get(
                "first_name"
            ),
            account.get(
                "middle_name"
            ),
            account.get(
                "last_name"
            ),
        ]
        if value
        and str(value).strip()
    )


def _masked_email(
    email_address: str,
) -> str:

    email_address = str(
        email_address
        or ""
    ).strip()

    if (
        not email_address
        or "@"
        not in email_address
    ):

        return ""

    local_part, domain = (
        email_address.split(
            "@",
            1,
        )
    )

    if len(local_part) <= 2:

        masked_local = (
            local_part[:1]
            + "*"
        )

    else:

        masked_local = (
            local_part[0]
            + "*"
            * (
                len(local_part)
                - 2
            )
            + local_part[-1]
        )

    return (
        f"{masked_local}"
        f"@{domain}"
    )


# ============================================================
# GET STAFF ACCOUNT
# ============================================================

def get_staff_account(
    staff_code: str,
) -> dict | None:

    query = text(
        """
        SELECT
            sa.id AS staff_account_id,
            sa.employee_id,
            sa.staff_code,
            sa.role_code,
            sa.password_hash,
            sa.pin_hash,
            sa.must_change_password,
            sa.must_change_pin,
            sa.failed_login_attempts,
            sa.locked_until,
            sa.is_active AS account_is_active,
            sa.credentials_issued_at,
            sa.password_changed_at,
            sa.pin_changed_at,
            sa.last_login_at,

            e.employee_number,
            e.first_name,
            e.middle_name,
            e.last_name,
            e.email,
            e.phone_number,
            e.job_title,
            e.department,
            e.employment_status,
            e.requires_system_access,

            sr.role_name,
            sr.is_active AS role_is_active

        FROM public.staff_accounts sa

        JOIN public.employees e
            ON e.id = sa.employee_id

        JOIN public.staff_roles sr
            ON sr.role_code = sa.role_code

        WHERE
            upper(
                sa.staff_code
            )
            = :staff_code

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "staff_code": (
                    _normalise_staff_code(
                        staff_code
                    )
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row
        else None
    )


def get_staff_account_by_id(
    staff_account_id: str,
) -> dict | None:

    query = text(
        """
        SELECT
            sa.id AS staff_account_id,
            sa.employee_id,
            sa.staff_code,
            sa.role_code,
            sa.password_hash,
            sa.pin_hash,
            sa.must_change_password,
            sa.must_change_pin,
            sa.failed_login_attempts,
            sa.locked_until,
            sa.is_active AS account_is_active,
            sa.credentials_issued_at,
            sa.password_changed_at,
            sa.pin_changed_at,
            sa.last_login_at,

            e.employee_number,
            e.first_name,
            e.middle_name,
            e.last_name,
            e.email,
            e.phone_number,
            e.job_title,
            e.department,
            e.employment_status,
            e.requires_system_access,

            sr.role_name,
            sr.is_active AS role_is_active

        FROM public.staff_accounts sa

        JOIN public.employees e
            ON e.id = sa.employee_id

        JOIN public.staff_roles sr
            ON sr.role_code = sa.role_code

        WHERE
            sa.id = CAST(
                :staff_account_id
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        ).mappings().first()

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# ACCOUNT ACCESS
# ============================================================

def check_staff_account_access(
    account: dict,
) -> None:

    if not account.get(
        "account_is_active"
    ):

        raise ValueError(
            "Staff account is disabled."
        )

    if not account.get(
        "role_is_active"
    ):

        raise ValueError(
            "Staff role is disabled."
        )

    if not account.get(
        "requires_system_access"
    ):

        raise ValueError(
            "This employee does not have "
            "system access."
        )

    if (
        account.get(
            "employment_status"
        )
        != "Active"
    ):

        raise ValueError(
            "Employee record is not active."
        )

    locked_until = (
        account.get(
            "locked_until"
        )
    )

    if not locked_until:

        return

    if (
        locked_until.tzinfo
        is None
    ):

        locked_until = (
            locked_until.replace(
                tzinfo=timezone.utc
            )
        )

    if locked_until > _now_utc():

        raise ValueError(
            "Staff account is temporarily "
            "locked."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts

                SET
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    updated_at = now()

                WHERE id = CAST(
                    :staff_account_id
                    AS uuid
                )
                """
            ),
            {
                "staff_account_id": (
                    str(
                        account[
                            "staff_account_id"
                        ]
                    )
                ),
            },
        )


# ============================================================
# FAILED / SUCCESSFUL LOGIN
# ============================================================

def record_failed_staff_login(
    staff_account_id: str,
) -> None:

    with engine.begin() as connection:

        row = connection.execute(
            text(
                """
                SELECT
                    failed_login_attempts

                FROM public.staff_accounts

                WHERE id = CAST(
                    :staff_account_id
                    AS uuid
                )

                FOR UPDATE
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        ).mappings().first()

        if not row:

            return

        failed_attempts = (
            int(
                row.get(
                    "failed_login_attempts"
                )
                or 0
            )
            + 1
        )

        if (
            failed_attempts
            >= MAX_FAILED_LOGIN_ATTEMPTS
        ):

            locked_until = (
                _now_utc()
                + timedelta(
                    minutes=(
                        LOCK_MINUTES
                    )
                )
            )

            connection.execute(
                text(
                    """
                    UPDATE public.staff_accounts

                    SET
                        failed_login_attempts =
                            :failed_login_attempts,

                        locked_until =
                            :locked_until,

                        updated_at = now()

                    WHERE id = CAST(
                        :staff_account_id
                        AS uuid
                    )
                    """
                ),
                {
                    "staff_account_id": (
                        staff_account_id
                    ),

                    "failed_login_attempts": (
                        failed_attempts
                    ),

                    "locked_until": (
                        locked_until
                    ),
                },
            )

        else:

            connection.execute(
                text(
                    """
                    UPDATE public.staff_accounts

                    SET
                        failed_login_attempts =
                            :failed_login_attempts,

                        updated_at = now()

                    WHERE id = CAST(
                        :staff_account_id
                        AS uuid
                    )
                    """
                ),
                {
                    "staff_account_id": (
                        staff_account_id
                    ),

                    "failed_login_attempts": (
                        failed_attempts
                    ),
                },
            )


def clear_staff_login_failures(
    staff_account_id: str,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts

                SET
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    updated_at = now()

                WHERE id = CAST(
                    :staff_account_id
                    AS uuid
                )
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        )


# ============================================================
# OTP EMAIL
# ============================================================

def _build_staff_otp_email(
    *,
    account: dict,
    otp: str,
) -> tuple[str, str]:

    name = (
        _full_name(
            account
        )
        or account.get(
            "staff_code"
        )
        or "Staff Member"
    )

    safe_name = html.escape(
        name
    )

    safe_otp = html.escape(
        otp
    )

    text_body = (
        f"Dear {name},\n\n"
        "Your Glen Moniques Staff Portal "
        "verification code is:\n\n"
        f"{otp}\n\n"
        f"This code expires in "
        f"{OTP_EXPIRE_MINUTES} minutes.\n\n"
        "If you did not attempt to sign in, "
        "please contact the system "
        "administrator.\n\n"
        "Regards,\n"
        "Glen Moniques (Pty) Ltd"
    )

    html_body = (
        "<html><body>"
        f"<p>Dear {safe_name},</p>"
        "<p>Your Glen Moniques Staff Portal "
        "verification code is:</p>"
        f"<p style='font-size:28px;"
        f"font-weight:bold;letter-spacing:4px;'>"
        f"{safe_otp}</p>"
        f"<p>This code expires in "
        f"{OTP_EXPIRE_MINUTES} minutes.</p>"
        "<p>If you did not attempt to sign in, "
        "please contact the system "
        "administrator.</p>"
        "<p>Regards,<br>"
        "Glen Moniques (Pty) Ltd</p>"
        "</body></html>"
    )

    return (
        html_body,
        text_body,
    )


def _send_staff_otp_email(
    *,
    account: dict,
    otp: str,
) -> None:

    recipient_email = str(
        account.get(
            "email"
        )
        or ""
    ).strip()

    if not recipient_email:

        raise ValueError(
            "Staff email address is "
            "not available."
        )

    html_body, text_body = (
        _build_staff_otp_email(
            account=account,
            otp=otp,
        )
    )

    send_email(
        recipient_email=(
            recipient_email
        ),
        subject=(
            "Glen Moniques - "
            "Staff Login Verification Code"
        ),
        html_body=(
            html_body
        ),
        text_body=(
            text_body
        ),
    )


# ============================================================
# OTP STORAGE
# ============================================================

def _generate_otp() -> str:

    return (
        f"{secrets.randbelow(1_000_000):06d}"
    )


def _consume_active_staff_otps(
    staff_account_id: str,
) -> None:

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.staff_otp_challenges

                SET
                    consumed_at = now()

                WHERE
                    staff_account_id
                    = CAST(
                        :staff_account_id
                        AS uuid
                    )

                    AND purpose = 'LOGIN'

                    AND consumed_at IS NULL
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        )


def _create_staff_otp(
    account: dict,
) -> str:

    staff_account_id = str(
        account[
            "staff_account_id"
        ]
    )

    _consume_active_staff_otps(
        staff_account_id
    )

    otp = _generate_otp()

    otp_hash = hash_secret(
        otp
    )

    expires_at = (
        _now_utc()
        + timedelta(
            minutes=(
                OTP_EXPIRE_MINUTES
            )
        )
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                INSERT INTO
                    public.staff_otp_challenges
                (
                    staff_account_id,
                    otp_hash,
                    purpose,
                    expires_at,
                    attempts,
                    max_attempts
                )

                VALUES
                (
                    CAST(
                        :staff_account_id
                        AS uuid
                    ),
                    :otp_hash,
                    'LOGIN',
                    :expires_at,
                    0,
                    :max_attempts
                )
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),

                "otp_hash": (
                    otp_hash
                ),

                "expires_at": (
                    expires_at
                ),

                "max_attempts": (
                    OTP_MAX_ATTEMPTS
                ),
            },
        )

    return otp


def start_staff_otp_challenge(
    account: dict,
) -> dict:

    otp = _create_staff_otp(
        account
    )

    try:

        _send_staff_otp_email(
            account=account,
            otp=otp,
        )

    except Exception:

        _consume_active_staff_otps(
            str(
                account[
                    "staff_account_id"
                ]
            )
        )

        raise

    challenge_token = (
        create_staff_challenge_token(
            staff_code=(
                account[
                    "staff_code"
                ]
            ),

            staff_account_id=str(
                account[
                    "staff_account_id"
                ]
            ),

            role_code=(
                account[
                    "role_code"
                ]
            ),

            stage="OTP",
        )
    )

    return {
        "authenticated": False,

        "status": (
            "OTP_REQUIRED"
        ),

        "challenge_token": (
            challenge_token
        ),

        "staff_code": (
            account[
                "staff_code"
            ]
        ),

        "role_code": (
            account[
                "role_code"
            ]
        ),

        "role_name": (
            account[
                "role_name"
            ]
        ),

        "otp_sent_to": (
            _masked_email(
                account.get(
                    "email"
                )
                or ""
            )
        ),

        "otp_expires_in_minutes": (
            OTP_EXPIRE_MINUTES
        ),
    }


# ============================================================
# STAFF LOGIN
# ============================================================

def login_staff(
    *,
    staff_code: str,
    password: str,
    pin: str,
) -> dict:

    account = get_staff_account(
        staff_code
    )

    if not account:

        raise ValueError(
            "Staff code, password or PIN "
            "is incorrect."
        )

    check_staff_account_access(
        account
    )

    password_valid = verify_secret(
        password,
        account[
            "password_hash"
        ],
    )

    pin_valid = verify_secret(
        pin,
        account[
            "pin_hash"
        ],
    )

    if (
        not password_valid
        or not pin_valid
    ):

        record_failed_staff_login(
            str(
                account[
                    "staff_account_id"
                ]
            )
        )

        raise ValueError(
            "Staff code, password or PIN "
            "is incorrect."
        )

    clear_staff_login_failures(
        str(
            account[
                "staff_account_id"
            ]
        )
    )

    if (
        account.get(
            "must_change_password"
        )
        or account.get(
            "must_change_pin"
        )
    ):

        challenge_token = (
            create_staff_challenge_token(
                staff_code=(
                    account[
                        "staff_code"
                    ]
                ),

                staff_account_id=str(
                    account[
                        "staff_account_id"
                    ]
                ),

                role_code=(
                    account[
                        "role_code"
                    ]
                ),

                stage=(
                    "CREDENTIAL_CHANGE"
                ),
            )
        )

        return {
            "authenticated": False,

            "status": (
                "CREDENTIAL_CHANGE_REQUIRED"
            ),

            "challenge_token": (
                challenge_token
            ),

            "staff_code": (
                account[
                    "staff_code"
                ]
            ),

            "role_code": (
                account[
                    "role_code"
                ]
            ),

            "role_name": (
                account[
                    "role_name"
                ]
            ),
        }

    return start_staff_otp_challenge(
        account
    )


# ============================================================
# CHANGE TEMPORARY CREDENTIALS
# ============================================================

def change_temporary_staff_credentials(
    *,
    challenge_token: str,
    new_password: str,
    confirm_password: str,
    new_pin: str,
    confirm_pin: str,
) -> dict:

    if (
        new_password
        != confirm_password
    ):

        raise ValueError(
            "Passwords do not match."
        )

    if (
        new_pin
        != confirm_pin
    ):

        raise ValueError(
            "PINs do not match."
        )

    validate_password(
        new_password
    )

    validate_pin(
        new_pin
    )

    payload = (
        decode_staff_challenge_token(
            challenge_token,
            required_stage=(
                "CREDENTIAL_CHANGE"
            ),
        )
    )

    staff_account_id = str(
        payload[
            "staff_account_id"
        ]
    )

    account = (
        get_staff_account_by_id(
            staff_account_id
        )
    )

    if not account:

        raise ValueError(
            "Staff account not found."
        )

    check_staff_account_access(
        account
    )

    if not (
        account.get(
            "must_change_password"
        )
        or account.get(
            "must_change_pin"
        )
    ):

        raise ValueError(
            "Temporary credentials have "
            "already been changed."
        )

    if verify_secret(
        new_password,
        account[
            "password_hash"
        ],
    ):

        raise ValueError(
            "New password must be different "
            "from the temporary password."
        )

    if verify_secret(
        new_pin,
        account[
            "pin_hash"
        ],
    ):

        raise ValueError(
            "New PIN must be different "
            "from the temporary PIN."
        )

    password_hash = hash_secret(
        new_password
    )

    pin_hash = hash_secret(
        new_pin
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts

                SET
                    password_hash =
                        :password_hash,

                    pin_hash =
                        :pin_hash,

                    must_change_password =
                        FALSE,

                    must_change_pin =
                        FALSE,

                    password_changed_at =
                        now(),

                    pin_changed_at =
                        now(),

                    failed_login_attempts =
                        0,

                    locked_until =
                        NULL,

                    updated_at =
                        now()

                WHERE id = CAST(
                    :staff_account_id
                    AS uuid
                )
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),

                "password_hash": (
                    password_hash
                ),

                "pin_hash": (
                    pin_hash
                ),
            },
        )

    refreshed_account = (
        get_staff_account_by_id(
            staff_account_id
        )
    )

    if not refreshed_account:

        raise ValueError(
            "Staff account could not be "
            "reloaded."
        )

    return start_staff_otp_challenge(
        refreshed_account
    )


# ============================================================
# RESEND OTP
# ============================================================

def resend_staff_otp(
    challenge_token: str,
) -> dict:

    payload = (
        decode_staff_challenge_token(
            challenge_token,
            required_stage="OTP",
        )
    )

    account = (
        get_staff_account_by_id(
            str(
                payload[
                    "staff_account_id"
                ]
            )
        )
    )

    if not account:

        raise ValueError(
            "Staff account not found."
        )

    check_staff_account_access(
        account
    )

    return start_staff_otp_challenge(
        account
    )


# ============================================================
# VERIFY OTP
# ============================================================

def verify_staff_otp(
    *,
    challenge_token: str,
    otp: str,
) -> dict:

    payload = (
        decode_staff_challenge_token(
            challenge_token,
            required_stage="OTP",
        )
    )

    staff_account_id = str(
        payload[
            "staff_account_id"
        ]
    )

    account = (
        get_staff_account_by_id(
            staff_account_id
        )
    )

    if not account:

        raise ValueError(
            "Staff account not found."
        )

    check_staff_account_access(
        account
    )

    with engine.connect() as connection:

        row = connection.execute(
            text(
                """
                SELECT
                    id,
                    otp_hash,
                    expires_at,
                    attempts,
                    max_attempts

                FROM public.staff_otp_challenges

                WHERE
                    staff_account_id
                    = CAST(
                        :staff_account_id
                        AS uuid
                    )

                    AND purpose = 'LOGIN'

                    AND consumed_at IS NULL

                ORDER BY
                    created_at DESC

                LIMIT 1
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        ).mappings().first()

    if not row:

        raise ValueError(
            "No active OTP was found. "
            "Request a new OTP."
        )

    expires_at = (
        row[
            "expires_at"
        ]
    )

    if (
        expires_at.tzinfo
        is None
    ):

        expires_at = (
            expires_at.replace(
                tzinfo=timezone.utc
            )
        )

    otp_id = str(
        row[
            "id"
        ]
    )

    if expires_at <= _now_utc():

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    UPDATE public.staff_otp_challenges

                    SET
                        consumed_at = now()

                    WHERE id = CAST(
                        :otp_id
                        AS uuid
                    )
                    """
                ),
                {
                    "otp_id": (
                        otp_id
                    ),
                },
            )

        raise ValueError(
            "OTP has expired. "
            "Request a new OTP."
        )

    attempts = int(
        row.get(
            "attempts"
        )
        or 0
    )

    max_attempts = int(
        row.get(
            "max_attempts"
        )
        or OTP_MAX_ATTEMPTS
    )

    if attempts >= max_attempts:

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    UPDATE public.staff_otp_challenges

                    SET
                        consumed_at = now()

                    WHERE id = CAST(
                        :otp_id
                        AS uuid
                    )
                    """
                ),
                {
                    "otp_id": (
                        otp_id
                    ),
                },
            )

        raise ValueError(
            "OTP attempt limit reached. "
            "Request a new OTP."
        )

    if not verify_secret(
        otp,
        row[
            "otp_hash"
        ],
    ):

        new_attempts = (
            attempts + 1
        )

        with engine.begin() as connection:

            connection.execute(
                text(
                    """
                    UPDATE public.staff_otp_challenges

                    SET
                        attempts =
                            :attempts,

                        consumed_at =
                            CASE
                                WHEN :attempts
                                >= max_attempts
                                THEN now()
                                ELSE consumed_at
                            END

                    WHERE id = CAST(
                        :otp_id
                        AS uuid
                    )
                    """
                ),
                {
                    "otp_id": (
                        otp_id
                    ),

                    "attempts": (
                        new_attempts
                    ),
                },
            )

        raise ValueError(
            "OTP is incorrect."
        )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE public.staff_otp_challenges

                SET
                    consumed_at = now()

                WHERE id = CAST(
                    :otp_id
                    AS uuid
                )
                """
            ),
            {
                "otp_id": (
                    otp_id
                ),
            },
        )

        connection.execute(
            text(
                """
                UPDATE public.staff_accounts

                SET
                    failed_login_attempts = 0,
                    locked_until = NULL,
                    last_login_at = now(),
                    updated_at = now()

                WHERE id = CAST(
                    :staff_account_id
                    AS uuid
                )
                """
            ),
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        )

    access_token = (
        create_staff_access_token(
            staff_code=(
                account[
                    "staff_code"
                ]
            ),

            staff_account_id=(
                staff_account_id
            ),

            employee_id=str(
                account[
                    "employee_id"
                ]
            ),

            role_code=(
                account[
                    "role_code"
                ]
            ),
        )
    )

    return {
        "authenticated": True,

        "status": (
            "AUTHENTICATED"
        ),

        "access_token": (
            access_token
        ),

        "token_type": (
            "bearer"
        ),

        "staff": {
            "staff_code": (
                account[
                    "staff_code"
                ]
            ),

            "employee_number": (
                account.get(
                    "employee_number"
                )
            ),

            "full_name": (
                _full_name(
                    account
                )
            ),

            "email": (
                account.get(
                    "email"
                )
            ),

            "job_title": (
                account.get(
                    "job_title"
                )
            ),

            "department": (
                account.get(
                    "department"
                )
            ),

            "role_code": (
                account[
                    "role_code"
                ]
            ),

            "role_name": (
                account[
                    "role_name"
                ]
            ),
        },
    }


# ============================================================
# CURRENT STAFF PROFILE
# ============================================================

def get_staff_profile(
    staff_account_id: str,
) -> dict:

    account = (
        get_staff_account_by_id(
            staff_account_id
        )
    )

    if not account:

        raise ValueError(
            "Staff account not found."
        )

    check_staff_account_access(
        account
    )

    return {
        "staff_code": (
            account[
                "staff_code"
            ]
        ),

        "employee_number": (
            account.get(
                "employee_number"
            )
        ),

        "full_name": (
            _full_name(
                account
            )
        ),

        "first_name": (
            account.get(
                "first_name"
            )
        ),

        "middle_name": (
            account.get(
                "middle_name"
            )
        ),

        "last_name": (
            account.get(
                "last_name"
            )
        ),

        "email": (
            account.get(
                "email"
            )
        ),

        "phone_number": (
            account.get(
                "phone_number"
            )
        ),

        "job_title": (
            account.get(
                "job_title"
            )
        ),

        "department": (
            account.get(
                "department"
            )
        ),

        "role_code": (
            account[
                "role_code"
            ]
        ),

        "role_name": (
            account[
                "role_name"
            ]
        ),

        "last_login_at": (
            account.get(
                "last_login_at"
            )
        ),
    }