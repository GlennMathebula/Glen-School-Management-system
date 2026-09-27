from fastapi import (
    Depends,
    HTTPException,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.services.staff_auth_service import (
    get_staff_account_by_id,
)
from app.services.staff_jwt_service import (
    decode_staff_access_token,
)

# ============================================================
# STAFF BEARER AUTHENTICATION
# ============================================================

staff_bearer_scheme = HTTPBearer(
    auto_error=False
)


# ============================================================
# GET CURRENT STAFF
# ============================================================

def get_current_staff(
    credentials: (
        HTTPAuthorizationCredentials
        | None
    ) = Depends(
        staff_bearer_scheme
    ),
) -> dict:

    if not credentials:

        raise HTTPException(
            status_code=401,
            detail=(
                "Staff authentication required."
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
            decode_staff_access_token(
                token
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=401,
            detail=str(
                error
            ),
            headers={
                "WWW-Authenticate": (
                    "Bearer"
                )
            },
        ) from error

    staff_account_id = (
        payload.get(
            "staff_account_id"
        )
    )

    account = (
        get_staff_account_by_id(
            str(
                staff_account_id
            )
        )
        if staff_account_id
        else None
    )

    if not account:

        raise HTTPException(
            status_code=401,
            detail=(
                "Staff account not found."
            ),
        )

    if not account.get(
        "account_is_active"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Staff account is disabled."
            ),
        )

    if not account.get(
        "requires_system_access"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "This employee does not have "
                "system access."
            ),
        )

    if (
        account.get(
            "employment_status"
        )
        != "Active"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Employee record is not active."
            ),
        )

    if not account.get(
        "role_is_active"
    ):

        raise HTTPException(
            status_code=403,
            detail=(
                "Staff role is disabled."
            ),
        )

    return {
        "staff_account_id": str(
            account[
                "staff_account_id"
            ]
        ),

        "employee_id": str(
            account[
                "employee_id"
            ]
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

        "email": (
            account.get(
                "email"
            )
        ),
    }