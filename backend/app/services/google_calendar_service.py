import secrets
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt
from cryptography.fernet import Fernet
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.services.jwt_service import (
    JWT_ALGORITHM,
)


# ============================================================
# GOOGLE OAUTH SETTINGS
# ============================================================

GOOGLE_AUTH_URI = (
    "https://accounts.google.com/o/oauth2/auth"
)

GOOGLE_TOKEN_URI = (
    "https://oauth2.googleapis.com/token"
)

GOOGLE_CALENDAR_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/calendar.events",
]

OAUTH_STATE_EXPIRE_MINUTES = 10


# ============================================================
# VALIDATE GOOGLE CONFIGURATION
# ============================================================

def validate_google_calendar_configuration():
    if not settings.google_calendar_client_id:
        raise RuntimeError(
            "Google Calendar client ID "
            "is not configured."
        )

    if not settings.google_calendar_client_secret:
        raise RuntimeError(
            "Google Calendar client secret "
            "is not configured."
        )

    if not settings.google_token_encryption_key:
        raise RuntimeError(
            "Google token encryption key "
            "is not configured."
        )


# ============================================================
# TOKEN ENCRYPTION
# ============================================================

def get_token_cipher() -> Fernet:
    validate_google_calendar_configuration()

    try:
        return Fernet(
            settings.google_token_encryption_key.encode(
                "utf-8"
            )
        )

    except Exception as error:
        raise RuntimeError(
            "Google token encryption key "
            "is invalid."
        ) from error


def encrypt_token(
    token: str | None,
) -> str | None:
    if not token:
        return None

    cipher = get_token_cipher()

    return cipher.encrypt(
        token.encode(
            "utf-8"
        )
    ).decode(
        "utf-8"
    )


def decrypt_token(
    token: str | None,
) -> str | None:
    if not token:
        return None

    cipher = get_token_cipher()

    return cipher.decrypt(
        token.encode(
            "utf-8"
        )
    ).decode(
        "utf-8"
    )


# ============================================================
# GOOGLE CLIENT CONFIG
# ============================================================

def get_google_client_config() -> dict:
    validate_google_calendar_configuration()

    return {
        "web": {
            "client_id": (
                settings.google_calendar_client_id
            ),
            "client_secret": (
                settings.google_calendar_client_secret
            ),
            "auth_uri": (
                GOOGLE_AUTH_URI
            ),
            "token_uri": (
                GOOGLE_TOKEN_URI
            ),
            "redirect_uris": [
                settings.google_calendar_redirect_uri
            ],
        }
    }


# ============================================================
# CREATE PKCE CODE VERIFIER
# ============================================================

def create_code_verifier() -> str:
    return secrets.token_urlsafe(
        64
    )


# ============================================================
# CREATE OAUTH STATE TOKEN
# ============================================================

def create_google_oauth_state(
    *,
    staff_account_id: str,
    staff_code: str,
    code_verifier: str,
) -> str:

    now = datetime.now(
        timezone.utc
    )

    expires_at = (
        now
        + timedelta(
            minutes=(
                OAUTH_STATE_EXPIRE_MINUTES
            )
        )
    )

    payload = {
        "type": (
            "google_calendar_oauth_state"
        ),
        "staff_account_id": (
            staff_account_id
        ),
        "staff_code": (
            staff_code
        ),
        "code_verifier": (
            code_verifier
        ),
        "iat": now,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=(
            JWT_ALGORITHM
        ),
    )


# ============================================================
# DECODE OAUTH STATE TOKEN
# ============================================================

def decode_google_oauth_state(
    state: str,
) -> dict:

    try:
        payload = jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=[
                JWT_ALGORITHM
            ],
        )

    except jwt.ExpiredSignatureError as error:
        raise ValueError(
            "Google Calendar connection "
            "request has expired."
        ) from error

    except jwt.InvalidTokenError as error:
        raise ValueError(
            "Invalid Google Calendar "
            "connection request."
        ) from error

    if (
        payload.get(
            "type"
        )
        != "google_calendar_oauth_state"
    ):
        raise ValueError(
            "Invalid Google Calendar "
            "OAuth state."
        )

    if not payload.get(
        "staff_account_id"
    ):
        raise ValueError(
            "Google Calendar connection "
            "does not contain a staff account."
        )

    if not payload.get(
        "code_verifier"
    ):
        raise ValueError(
            "Google Calendar connection "
            "does not contain a PKCE verifier."
        )

    return payload


# ============================================================
# CREATE GOOGLE AUTHORIZATION URL
# ============================================================

def create_google_calendar_authorization_url(
    *,
    staff_account_id: str,
    staff_code: str,
) -> str:

    validate_google_calendar_configuration()

    code_verifier = (
        create_code_verifier()
    )

    state = create_google_oauth_state(
        staff_account_id=(
            staff_account_id
        ),
        staff_code=(
            staff_code
        ),
        code_verifier=(
            code_verifier
        ),
    )

    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=(
            GOOGLE_CALENDAR_SCOPES
        ),
        state=(
            state
        ),
        code_verifier=(
            code_verifier
        ),
    )

    flow.redirect_uri = (
        settings.google_calendar_redirect_uri
    )

    authorization_url, _ = (
        flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )
    )

    return authorization_url


# ============================================================
# SAVE GOOGLE CONNECTION
# ============================================================

def save_google_calendar_connection(
    *,
    staff_account_id: str,
    credentials: Credentials,
) -> dict:

    access_token = encrypt_token(
        credentials.token
    )

    refresh_token = encrypt_token(
        credentials.refresh_token
    )

    expiry = (
        credentials.expiry
        if credentials.expiry
        else None
    )

    scopes = list(
        credentials.scopes
        or GOOGLE_CALENDAR_SCOPES
    )

    query = text(
        """
        INSERT INTO
            public.google_calendar_connections
        (
            staff_account_id,
            google_calendar_id,
            access_token_encrypted,
            refresh_token_encrypted,
            token_expiry,
            scopes,
            is_active,
            connected_at,
            updated_at
        )

        VALUES
        (
            CAST(
                :staff_account_id
                AS uuid
            ),
            'primary',
            :access_token_encrypted,
            :refresh_token_encrypted,
            :token_expiry,
            :scopes,
            true,
            now(),
            now()
        )

        ON CONFLICT
        (
            staff_account_id
        )

        DO UPDATE SET
            google_calendar_id =
                EXCLUDED.google_calendar_id,

            access_token_encrypted =
                EXCLUDED.access_token_encrypted,

            refresh_token_encrypted =
                COALESCE(
                    EXCLUDED.refresh_token_encrypted,
                    public.google_calendar_connections
                        .refresh_token_encrypted
                ),

            token_expiry =
                EXCLUDED.token_expiry,

            scopes =
                EXCLUDED.scopes,

            is_active =
                true,

            connected_at =
                now(),

            updated_at =
                now()

        RETURNING
            id,
            staff_account_id,
            google_calendar_id,
            token_expiry,
            scopes,
            is_active,
            connected_at,
            last_synced_at,
            created_at,
            updated_at
        """
    )

    with engine.begin() as connection:
        row = connection.execute(
            query,
            {
                "staff_account_id": (
                    staff_account_id
                ),
                "access_token_encrypted": (
                    access_token
                ),
                "refresh_token_encrypted": (
                    refresh_token
                ),
                "token_expiry": (
                    expiry
                ),
                "scopes": (
                    scopes
                ),
            },
        ).mappings().one()

    return dict(
        row
    )


# ============================================================
# HANDLE GOOGLE CALLBACK
# ============================================================

def complete_google_calendar_connection(
    *,
    code: str,
    state: str,
) -> dict:

    state_payload = (
        decode_google_oauth_state(
            state
        )
    )

    staff_account_id = str(
        state_payload[
            "staff_account_id"
        ]
    )

    code_verifier = str(
        state_payload[
            "code_verifier"
        ]
    )

    flow = Flow.from_client_config(
        get_google_client_config(),
        scopes=(
            GOOGLE_CALENDAR_SCOPES
        ),
        state=(
            state
        ),
        code_verifier=(
            code_verifier
        ),
    )

    flow.redirect_uri = (
        settings.google_calendar_redirect_uri
    )

    flow.fetch_token(
        code=(
            code
        )
    )

    credentials = (
        flow.credentials
    )

    if not credentials.token:
        raise RuntimeError(
            "Google did not return "
            "an access token."
        )

    return (
        save_google_calendar_connection(
            staff_account_id=(
                staff_account_id
            ),
            credentials=(
                credentials
            ),
        )
    )


# ============================================================
# GET GOOGLE CONNECTION
# ============================================================

def get_google_calendar_connection(
    staff_account_id: str,
) -> dict | None:

    query = text(
        """
        SELECT
            id,
            staff_account_id,
            google_email,
            google_calendar_id,
            token_expiry,
            scopes,
            is_active,
            connected_at,
            last_synced_at,
            created_at,
            updated_at

        FROM
            public.google_calendar_connections

        WHERE
            staff_account_id = CAST(
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
        dict(
            row
        )
        if row
        else None
    )


# ============================================================
# GET GOOGLE CREDENTIALS
# ============================================================

def get_google_calendar_credentials(
    staff_account_id: str,
) -> Credentials:

    query = text(
        """
        SELECT
            access_token_encrypted,
            refresh_token_encrypted,
            token_expiry,
            scopes,
            is_active

        FROM
            public.google_calendar_connections

        WHERE
            staff_account_id = CAST(
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

    if not row:
        raise ValueError(
            "Google Calendar is not connected."
        )

    if not row[
        "is_active"
    ]:
        raise ValueError(
            "Google Calendar connection "
            "is disabled."
        )

    access_token = decrypt_token(
        row[
            "access_token_encrypted"
        ]
    )

    refresh_token = decrypt_token(
        row[
            "refresh_token_encrypted"
        ]
    )

    credentials = Credentials(
        token=(
            access_token
        ),
        refresh_token=(
            refresh_token
        ),
        token_uri=(
            GOOGLE_TOKEN_URI
        ),
        client_id=(
            settings.google_calendar_client_id
        ),
        client_secret=(
            settings.google_calendar_client_secret
        ),
        scopes=(
            row[
                "scopes"
            ]
            or GOOGLE_CALENDAR_SCOPES
        ),
    )

    if row[
    "token_expiry"
]:
        expiry = (
        row[
            "token_expiry"
        ]
    )

    # Google Auth expects a naive UTC datetime.
    if expiry.tzinfo is not None:
        expiry = (
            expiry
            .astimezone(
                timezone.utc
            )
            .replace(
                tzinfo=None
            )
        )

    credentials.expiry = (
        expiry
    )

    if (
        credentials.expired
        and credentials.refresh_token
    ):
        credentials.refresh(
            Request()
        )

        update_google_calendar_tokens(
            staff_account_id=(
                staff_account_id
            ),
            credentials=(
                credentials
            ),
        )

    return credentials


# ============================================================
# UPDATE REFRESHED TOKENS
# ============================================================

def update_google_calendar_tokens(
    *,
    staff_account_id: str,
    credentials: Credentials,
):

    access_token = encrypt_token(
        credentials.token
    )

    refresh_token = encrypt_token(
        credentials.refresh_token
    )

    query = text(
        """
        UPDATE
            public.google_calendar_connections

        SET
            access_token_encrypted =
                :access_token_encrypted,

            refresh_token_encrypted =
                COALESCE(
                    :refresh_token_encrypted,
                    refresh_token_encrypted
                ),

            token_expiry =
                :token_expiry,

            updated_at =
                now()

        WHERE
            staff_account_id = CAST(
                :staff_account_id
                AS uuid
            )
        """
    )

    with engine.begin() as connection:
        connection.execute(
            query,
            {
                "staff_account_id": (
                    staff_account_id
                ),
                "access_token_encrypted": (
                    access_token
                ),
                "refresh_token_encrypted": (
                    refresh_token
                ),
                "token_expiry": (
                    credentials.expiry
                ),
            },
        )


# ============================================================
# DISCONNECT GOOGLE CALENDAR
# ============================================================

def disconnect_google_calendar(
    staff_account_id: str,
) -> bool:

    query = text(
        """
        UPDATE
            public.google_calendar_connections

        SET
            is_active = false,
            access_token_encrypted = '',
            refresh_token_encrypted = NULL,
            token_expiry = NULL,
            updated_at = now()

        WHERE
            staff_account_id = CAST(
                :staff_account_id
                AS uuid
            )

        RETURNING
            id
        """
    )

    with engine.begin() as connection:
        row = connection.execute(
            query,
            {
                "staff_account_id": (
                    staff_account_id
                ),
            },
        ).first()

    return row is not None