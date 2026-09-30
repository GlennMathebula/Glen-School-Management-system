from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.careers_hr import (
    HREmploymentUpdate,
)
from app.services.staff_hr_employment_service import (
    update_hr_employee_employment,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/hr",
    tags=["HR Recruitment & Employment"],
)


require_manage_employment = require_permission(
    "MANAGE_EMPLOYMENT"
)


@router.patch(
    "/employees/{employee_id}/employment"
)
def staff_hr_update_employee_employment(
    employee_id: str,
    payload: HREmploymentUpdate,
    current_staff: dict = Depends(
        require_manage_employment
    ),
):
    try:
        record = update_hr_employee_employment(
            actor_staff_code=(
                current_staff["staff_code"]
            ),
            employee_id=employee_id,
            updates=payload.model_dump(
                exclude_unset=True
            ),
        )

        return {
            "success": True,
            "employee": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
