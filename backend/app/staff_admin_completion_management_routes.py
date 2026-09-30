from fastapi import APIRouter, Depends, HTTPException

from app.models.backend_finalization import (
    CertificationUpdate,
    CompletionStatusUpdate,
    GraduationUpdate,
)
from app.services.admin_completion_management_service import (
    get_completion_tracking,
    update_certification,
    update_completion_status,
    update_graduation,
)
from app.services.staff_permission_service import require_permission


router = APIRouter(
    prefix="/api/staff/admin/completion-management",
    tags=["Admin - Completion Management"],
)

require_completion = require_permission("MANAGE_COMPLETION")
require_certification = require_permission("MANAGE_CERTIFICATION")


@router.get("/{student_number}")
def admin_completion_tracking(
    student_number: str,
    current_staff: dict = Depends(require_completion),
):
    return {
        "success": True,
        "data": get_completion_tracking(student_number),
    }


@router.patch("/{student_number}/completion")
def admin_completion_status_update(
    student_number: str,
    payload: CompletionStatusUpdate,
    current_staff: dict = Depends(require_completion),
):
    try:
        return {
            "success": True,
            "data": update_completion_status(
                actor_staff_code=current_staff["staff_code"],
                student_number=student_number,
                completion_status=payload.completion_status,
                completion_date=payload.completion_date,
                notes=payload.notes,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/{student_number}/certification")
def admin_certification_update(
    student_number: str,
    payload: CertificationUpdate,
    current_staff: dict = Depends(require_certification),
):
    try:
        return {
            "success": True,
            "data": update_certification(
                actor_staff_code=current_staff["staff_code"],
                student_number=student_number,
                certificate_status=payload.certificate_status,
                certificate_number=payload.certificate_number,
                certificate_date=payload.certificate_date,
                certificate_received_date=payload.certificate_received_date,
                certificate_issued_date=payload.certificate_issued_date,
                notes=payload.notes,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/{student_number}/graduation")
def admin_graduation_update(
    student_number: str,
    payload: GraduationUpdate,
    current_staff: dict = Depends(require_certification),
):
    try:
        return {
            "success": True,
            "data": update_graduation(
                actor_staff_code=current_staff["staff_code"],
                student_number=student_number,
                graduation_status=payload.graduation_status,
                graduation_date=payload.graduation_date,
                notes=payload.notes,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
