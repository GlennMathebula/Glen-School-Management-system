from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.services.staff_audit_service import (
    get_staff_audit_logs,
)

from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/audit",
    tags=[
        "Staff Audit",
    ],
)


# ============================================================
# VIEW AUDIT LOGS
# ============================================================

@router.get("")
def staff_audit_logs(
    actor_staff_code: str | None = Query(
        default=None
    ),

    module_code: str | None = Query(
        default=None
    ),

    action_code: str | None = Query(
        default=None
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),

    current_staff: dict = Depends(
        require_permission(
            "VIEW_AUDIT_LOG"
        )
    ),
):

    try:

        logs = (
            get_staff_audit_logs(
                actor_staff_code=(
                    actor_staff_code
                ),

                module_code=(
                    module_code
                ),

                action_code=(
                    action_code
                ),

                limit=(
                    limit
                ),
            )
        )

        return {
            "success": True,

            "requested_by": (
                current_staff[
                    "staff_code"
                ]
            ),

            "count": len(
                logs
            ),

            "logs": (
                logs
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
            "ERROR: Staff audit logs "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Audit logs could not "
                "be loaded."
            ),
        ) from error