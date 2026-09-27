from collections.abc import Callable

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


# ============================================================
# REQUIRE STAFF ROLE
# ============================================================

def require_staff_role(
    *allowed_roles: str,
) -> Callable:

    normalised_roles = {
        str(
            role
        ).strip().upper()
        for role in allowed_roles
        if role
    }

    if not normalised_roles:

        raise ValueError(
            "At least one staff role "
            "must be supplied."
        )

    def role_dependency(
        current_staff: dict = Depends(
            get_current_staff
        ),
    ) -> dict:

        role_code = str(
            current_staff.get(
                "role_code"
            )
            or ""
        ).strip().upper()

        if (
            role_code
            not in normalised_roles
        ):

            raise HTTPException(
                status_code=403,
                detail=(
                    "You do not have permission "
                    "to access this staff area."
                ),
            )

        return current_staff

    return role_dependency


# ============================================================
# FACILITATOR ACCESS
# ============================================================

require_facilitator = (
    require_staff_role(
        "FACILITATOR"
    )
)


# ============================================================
# ASSESSOR ACCESS
# ============================================================

require_assessor = (
    require_staff_role(
        "ASSESSOR"
    )
)


# ============================================================
# MODERATOR ACCESS
# ============================================================

require_moderator = (
    require_staff_role(
        "MODERATOR"
    )
)


# ============================================================
# ADMIN ACCESS
# ============================================================

require_admin = (
    require_staff_role(
        "ADMIN"
    )
)


# ============================================================
# CFO ACCESS
# ============================================================

require_cfo = (
    require_staff_role(
        "CFO"
    )
)


# ============================================================
# CEO ACCESS
# ============================================================

require_ceo = (
    require_staff_role(
        "CEO"
    )
)


# ============================================================
# PRINCIPAL ACCESS
# ============================================================

require_principal = (
    require_staff_role(
        "PRINCIPAL"
    )
)


# ============================================================
# HR ACCESS
# ============================================================

require_hr = (
    require_staff_role(
        "HR"
    )
)