from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.admin_eisa_service import (
    list_eisa_learners,
    set_eisa_eligibility,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/eisa",
    tags=["Admin - EISA Administration"],
)


@router.get("/learners")
def admin_eisa_learners(
    eligible: bool | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    return {
        "success": True,
        **list_eisa_learners(
            eligible=eligible,
            search=search,
            limit=limit,
            offset=offset,
        ),
    }


@router.patch("/learners/{student_number}/eligibility")
def admin_set_eisa_eligibility(
    student_number: str,
    eligible: bool,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        record = set_eisa_eligibility(
            student_number=student_number,
            eligible=eligible,
        )
        return {
            "success": True,
            "message": "EISA eligibility updated.",
            "registration": record,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

