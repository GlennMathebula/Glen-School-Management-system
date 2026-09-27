from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.services.staff_permission_service import (
    get_staff_permission_context,
)

from app.staff_auth_dependency import (
    get_current_staff,
)


router = APIRouter(
    prefix="/api/staff/permissions",
    tags=[
        "Staff Permissions",
    ],
)


@router.get(
    "/me"
)
def staff_my_permissions(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        context = (
            get_staff_permission_context(
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
                context
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
            "ERROR: Staff permission context "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff permissions could "
                "not be loaded."
            ),
        ) from error