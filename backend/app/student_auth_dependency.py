from fastapi import (
    Depends,
    HTTPException,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.services.jwt_service import (
    decode_student_access_token,
)
from app.services.student_auth_service import (
    get_student_account,
)

# ============================================================
# BEARER AUTHENTICATION
# ============================================================

bearer_scheme = HTTPBearer(
    auto_error=False
)


# ============================================================
# GET CURRENT AUTHENTICATED STUDENT
# ============================================================

def get_current_student(
    credentials: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(
        bearer_scheme
    ),
) -> dict:

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail=(
                "Authentication required."
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                )
            },
        )

    token = (
        credentials.credentials
    )

    try:

        payload = (
            decode_student_access_token(
                token
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=401,
            detail=str(error),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                )
            },
        )

    student_number = (
        payload.get(
            "sub"
        )
    )

    account = get_student_account(
        student_number
    )

    if not account:

        raise HTTPException(
            status_code=401,
            detail=(
                "Student account not found."
            ),
        )

    account_status = (
        account.get(
            "account_status"
        )
    )

    if (
        account_status
        != "Active"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Student account is not active."
            ),
        )

    return {
        "student_number": (
            student_number
        ),

        "login_method": (
            payload.get(
                "login_method"
            )
        ),

        "must_change_password": bool(
            account.get(
                "must_change_password"
            )
        ),

        "pin_created": bool(
            account.get(
                "pin_created"
            )
        ),

        "account_status": (
            account_status
        ),
    }


# ============================================================
# REQUIRE FULL STUDENT ACCESS
# ============================================================

def require_full_student_access(
    current_student: dict = Depends(
        get_current_student
    ),
) -> dict:

    if current_student.get(
        "must_change_password"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You must change your temporary "
                "password before accessing "
                "the student portal."
            ),
        )

    if not current_student.get(
        "pin_created"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "You must create your 5-digit PIN "
                "before accessing the student portal."
            ),
        )

    if (
        current_student.get(
            "login_method"
        )
        != "password+pin"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Complete PIN verification before accessing "
                "the student portal."
            ),
        )

    return current_student