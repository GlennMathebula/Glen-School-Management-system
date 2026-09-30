from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.admin_completion_service import (
    get_completion_record,
    list_completion_status,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/completion",
    tags=["Admin - Completion, Graduation & Certification"],
)


@router.get("")
def admin_completion(
    search: str | None = None,
    course_code: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    return {
        "success": True,
        **list_completion_status(
            search=search,
            course_code=course_code,
            limit=limit,
            offset=offset,
        ),
    }


@router.get("/{student_number}")
def admin_completion_detail(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    record = get_completion_record(student_number)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Completion record not found.",
        )

    return {
        "success": True,
        "completion": record,
    }

