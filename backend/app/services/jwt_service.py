import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt

from app.config import settings

# ============================================================
# JWT SETTINGS
# ============================================================

JWT_ALGORITHM = "HS256"


# ============================================================
# VALIDATE JWT CONFIGURATION
# ============================================================

def validate_jwt_configuration() -> None:

    if not settings.jwt_secret_key:

        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    if len(
        settings.jwt_secret_key
    ) < 32:

        raise RuntimeError(
            "JWT_SECRET_KEY must contain at least "
            "32 characters."
        )

    if (
        settings.jwt_access_token_expire_minutes
        <= 0
    ):

        raise RuntimeError(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES "
            "must be greater than zero."
        )


# ============================================================
# CREATE STUDENT ACCESS TOKEN
# ============================================================

def create_student_access_token(
    student_number: str,
    login_method: str,
    must_change_password: bool,
    pin_created: bool,
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
        "sub": student_number,

        "type": (
            "student_access"
        ),

        "login_method": (
            login_method
        ),

        "must_change_password": (
            must_change_password
        ),

        "pin_created": (
            pin_created
        ),

        "iat": now,

        "exp": (
            expires_at
        ),

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
# DECODE STUDENT ACCESS TOKEN
# ============================================================

def decode_student_access_token(
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
            "Access token has expired."
        ) from error

    except jwt.InvalidTokenError as error:

        raise ValueError(
            "Invalid access token."
        ) from error

    if (
        payload.get(
            "type"
        )
        != "student_access"
    ):

        raise ValueError(
            "Invalid access token type."
        )

    student_number = (
        payload.get(
            "sub"
        )
    )

    if not student_number:

        raise ValueError(
            "Access token does not contain "
            "a student number."
        )

    return payload