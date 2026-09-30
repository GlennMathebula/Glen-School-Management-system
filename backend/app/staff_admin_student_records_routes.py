from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.admin_student_records_service import (
    get_student_document_inventory,
    get_student_record,
    list_students,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/students",
    tags=["Admin - Student Records & Documents"],
)


@router.get("")
def admin_students(
    search: str | None = None,
    course_code: str | None = None,
    registration_status: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        return {
            "success": True,
            **list_students(
                search=search,
                course_code=course_code,
                registration_status=registration_status,
                limit=limit,
                offset=offset,
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get("/{student_number}")
def admin_student_detail(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    record = get_student_record(student_number)

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Student record not found.",
        )

    return {
        "success": True,
        "student": record,
    }


@router.get("/{student_number}/documents")
def admin_student_documents(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        return {
            "success": True,
            **get_student_document_inventory(
                student_number
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

