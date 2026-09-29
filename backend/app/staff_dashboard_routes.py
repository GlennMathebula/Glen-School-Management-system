from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.services.staff_dashboard_service import (
    get_staff_dashboard,
)
from app.staff_auth_dependency import (
    get_current_staff,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/staff/dashboard",
    tags=[
        "Staff Dashboard",
    ],
)


# ============================================================
# COMMON STAFF DASHBOARD
# ============================================================

@router.get("")
def staff_dashboard(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        dashboard = (
            get_staff_dashboard(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,

            "data": (
                dashboard
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff dashboard "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff dashboard could "
                "not be loaded."
            ),
        ) from error