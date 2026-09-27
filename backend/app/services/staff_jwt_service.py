import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt

from app.config import settings
from app.services.jwt_service import (
    JWT_ALGORITHM,
    validate_jwt_configuration,
)

# ============================================================
# STAFF JWT SETTINGS
# ============================================================

STAFF_CHALLENGE_EXPIRE_MINUTES = 15


# ============================================================
# CREATE STAFF CHALLENGE TOKEN
# ============================================================

def create_staff_challenge_token(
    *,
    staff_code: str,
    staff_account_id: str,
    role_code: str,
    stage: str,
) -> str:

    validate_jwt_configuration()

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=(
                STAFF_CHALLENGE_EXPIRE_MINUTES
            )
        )
    )

    payload = {
        "sub": staff_code,

        "type": (
            "staff_challenge"
        ),

        "staff_account_id": (
            staff_account_id
        ),

        "role_code": (
            role_code
        ),

        "stage": (
            stage
        ),

        "iat": now,

        "exp": expires_at,

        "jti": (
            secrets.token_urlsafe(
                16
            )
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=(
            JWT_ALGORITHM
        ),
    )


# ============================================================
# DECODE STAFF CHALLENGE TOKEN
# ============================================================

def decode_staff_challenge_token(
    token: str,
    required_stage: str | None = None,
) -> dict:

    validate_jwt_configuration()

    try:

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

    except jwt.ExpiredSignatureError as error:

        raise ValueError(
            "Staff authentication session "
            "has expired."
        ) from error

    except jwt.InvalidTokenError as error:

        raise ValueError(
            "Invalid staff authentication "
            "session."
        ) from error

    if (
        payload.get(
            "type"
        )
        != "staff_challenge"
    ):

        raise ValueError(
            "Invalid staff authentication "
            "token type."
        )

    if (
        required_stage
        and payload.get(
            "stage"
        )
        != required_stage
    ):

        raise ValueError(
            "Invalid staff authentication "
            "stage."
        )

    if not payload.get(
        "staff_account_id"
    ):

        raise ValueError(
            "Staff authentication session "
            "does not contain an account."
        )

    return payload


# ============================================================
# CREATE STAFF ACCESS TOKEN
# ============================================================

def create_staff_access_token(
    *,
    staff_code: str,
    staff_account_id: str,
    employee_id: str,
    role_code: str,
) -> str:

    validate_jwt_configuration()

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=(
                settings
                .jwt_access_token_expire_minutes
            )
        )
    )

    payload = {
        "sub": staff_code,

        "type": (
            "staff_access"
        ),

        "staff_account_id": (
            staff_account_id
        ),

        "employee_id": (
            employee_id
        ),

        "role_code": (
            role_code
        ),

        "iat": now,

        "exp": expires_at,

        "jti": (
            secrets.token_urlsafe(
                16
            )
        ),
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=(
            JWT_ALGORITHM
        ),
    )


# ============================================================
# DECODE STAFF ACCESS TOKEN
# ============================================================

def decode_staff_access_token(
    token: str,
) -> dict:

    validate_jwt_configuration()

    try:

        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

    except jwt.ExpiredSignatureError as error:

        raise ValueError(
            "Staff access token has expired."
        ) from error

    except jwt.InvalidTokenError as error:

        raise ValueError(
            "Invalid staff access token."
        ) from error

    if (
        payload.get(
            "type"
        )
        != "staff_access"
    ):

        raise ValueError(
            "Invalid staff access token type."
        )

    if not payload.get(
        "sub"
    ):

        raise ValueError(
            "Staff access token does not contain "
            "a staff code."
        )

    if not payload.get(
        "staff_account_id"
    ):

        raise ValueError(
            "Staff access token does not contain "
            "an account."
        )

    return payload