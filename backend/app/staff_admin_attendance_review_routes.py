from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.admin_attendance_review_service import (
    confirm_attendance_review,
    get_attendance_review,
    list_attendance_reviews,
    return_attendance_review,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/attendance-review",
    tags=["Admin - Attendance Review"],
)


class AttendanceReturnRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)


@router.get("")
def admin_attendance_review_queue(
    status: str | None = Query(default="Submitted"),
    limit: int = Query(default=200, ge=1, le=500),
    current_staff: dict = Depends(require_admin_staff),
):
    try:
        records = list_attendance_reviews(
            status=status,
            limit=limit,
        )
        return {
            "success": True,
            "count": len(records),
            "records": records,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(f"ERROR: Admin attendance queue failed: {error}")
        raise HTTPException(
            status_code=500,
            detail="Attendance review queue could not be loaded.",
        ) from error


@router.get("/{attendance_session_id}")
def admin_attendance_review_detail(
    attendance_session_id: str,
    current_staff: dict = Depends(require_admin_staff),
):
    try:
        return {
            "success": True,
            "data": get_attendance_review(attendance_session_id),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(f"ERROR: Admin attendance detail failed: {error}")
        raise HTTPException(
            status_code=500,
            detail="Attendance review could not be loaded.",
        ) from error


@router.post("/{attendance_session_id}/confirm")
def admin_confirm_attendance(
    attendance_session_id: str,
    current_staff: dict = Depends(require_admin_staff),
):
    try:
        result = confirm_attendance_review(
            attendance_session_id=attendance_session_id,
            confirmed_by=current_staff["staff_code"],
        )
        return {
            "success": True,
            "message": "Attendance confirmed as official.",
            "data": result,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(f"ERROR: Admin attendance confirmation failed: {error}")
        raise HTTPException(
            status_code=500,
            detail="Attendance could not be confirmed.",
        ) from error


@router.post("/{attendance_session_id}/return")
def admin_return_attendance(
    attendance_session_id: str,
    payload: AttendanceReturnRequest,
    current_staff: dict = Depends(require_admin_staff),
):
    try:
        result = return_attendance_review(
            attendance_session_id=attendance_session_id,
            returned_by=current_staff["staff_code"],
            reason=payload.reason,
        )
        return {
            "success": True,
            "message": "Attendance returned for correction.",
            "data": result,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
    except Exception as error:
        print(f"ERROR: Admin attendance return failed: {error}")
        raise HTTPException(
            status_code=500,
            detail="Attendance could not be returned.",
        ) from error
