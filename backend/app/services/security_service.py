import base64
import hashlib
import hmac
import secrets
import string

# ============================================================
# PASSWORD HASH SETTINGS
# ============================================================

HASH_NAME = "sha256"

PBKDF2_ITERATIONS = 600_000

SALT_BYTES = 16


# ============================================================
# HASH SECRET
# ============================================================

def hash_secret(
    secret: str,
) -> str:

    if not secret:

        raise ValueError(
            "Secret cannot be empty."
        )

    salt = secrets.token_bytes(
        SALT_BYTES
    )

    derived_key = hashlib.pbkdf2_hmac(
        HASH_NAME,
        secret.encode(
            "utf-8"
        ),
        salt,
        PBKDF2_ITERATIONS,
    )

    salt_encoded = (
        base64.b64encode(
            salt
        ).decode(
            "utf-8"
        )
    )

    key_encoded = (
        base64.b64encode(
            derived_key
        ).decode(
            "utf-8"
        )
    )

    return (
        f"pbkdf2_{HASH_NAME}"
        f"${PBKDF2_ITERATIONS}"
        f"${salt_encoded}"
        f"${key_encoded}"
    )


# ============================================================
# VERIFY SECRET
# ============================================================

def verify_secret(
    secret: str,
    stored_hash: str,
) -> bool:

    if (
        not secret
        or not stored_hash
    ):

        return False

    try:

        (
            algorithm,
            iteration_text,
            salt_encoded,
            key_encoded,
        ) = stored_hash.split(
            "$",
            3,
        )

        if algorithm != "pbkdf2_sha256":

            return False

        iterations = int(
            iteration_text
        )

        salt = base64.b64decode(
            salt_encoded
        )

        expected_key = (
            base64.b64decode(
                key_encoded
            )
        )

        actual_key = hashlib.pbkdf2_hmac(
            HASH_NAME,
            secret.encode(
                "utf-8"
            ),
            salt,
            iterations,
        )

        return hmac.compare_digest(
            actual_key,
            expected_key,
        )

    except Exception:

        return False


# ============================================================
# PASSWORD VALIDATION
# ============================================================

def validate_password(
    password: str,
) -> None:

    if len(password) < 8:

        raise ValueError(
            "Password must contain at least "
            "8 characters."
        )

    if not any(
        character.isupper()
        for character in password
    ):

        raise ValueError(
            "Password must contain at least "
            "one capital letter."
        )

    if not any(
        character.isdigit()
        for character in password
    ):

        raise ValueError(
            "Password must contain at least "
            "one numeric character."
        )

    special_characters = (
        "!@#$%^&*()"
        "-_=+[]{}"
        ";:,.?/\\|"
    )

    if not any(
        character
        in special_characters
        for character in password
    ):

        raise ValueError(
            "Password must contain at least "
            "one special character."
        )


# ============================================================
# GENERATE TEMPORARY PASSWORD
# ============================================================

def generate_temporary_password(
    length: int = 12,
) -> str:

    length = max(length, 8)

    uppercase = (
        secrets.choice(
            string.ascii_uppercase
        )
    )

    lowercase = (
        secrets.choice(
            string.ascii_lowercase
        )
    )

    digit = (
        secrets.choice(
            string.digits
        )
    )

    special = (
        secrets.choice(
            "@#%&^*!"
        )
    )

    remaining_pool = (
        string.ascii_letters
        + string.digits
        + "@#%&^*!"
    )

    remaining = [
        secrets.choice(
            remaining_pool
        )
        for _ in range(
            length - 4
        )
    ]

    characters = [
        uppercase,
        lowercase,
        digit,
        special,
        *remaining,
    ]

    # Secure Fisher-Yates shuffle
    for index in range(
        len(characters) - 1,
        0,
        -1,
    ):

        random_index = (
            secrets.randbelow(
                index + 1
            )
        )

        (
            characters[index],
            characters[random_index],
        ) = (
            characters[random_index],
            characters[index],
        )

    password = "".join(
        characters
    )

    validate_password(
        password
    )

    return password


# ============================================================
# PIN VALIDATION
# ============================================================

def validate_pin(
    pin: str,
) -> None:

    # Rule 1 + Rule 4:
    # exactly five numeric characters
    if (
        len(pin) != 5
        or not pin.isdigit()
    ):

        raise ValueError(
            "PIN must contain exactly "
            "5 numeric digits."
        )

    # Rule 1:
    # may not begin with zero
    if pin.startswith(
        "0"
    ):

        raise ValueError(
            "PIN must not start with zero."
        )

    # Rule 2:
    # no identical adjacent digits:
    # 22, 33, 44, etc.
    for index in range(
        len(pin) - 1
    ):

        if (
            pin[index]
            == pin[index + 1]
        ):

            raise ValueError(
                "PIN must not contain "
                "two identical consecutive digits."
            )

    # Rule 3:
    # reject obvious ascending/descending sequences
    simple_pins = {
        "12345",
        "23456",
        "34567",
        "45678",
        "56789",
        "98765",
        "87654",
        "76543",
        "65432",
        "54321",
    }

    if pin in simple_pins:

        raise ValueError(
            "PIN is too easy to guess. "
            "Choose a less predictable PIN."
        )