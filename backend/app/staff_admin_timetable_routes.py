from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.admin_timetable_service import (
    list_admin_timetable,
    update_timetable_session_status,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/timetable",
    tags=["Admin - Timetable & Calendar"],
)


@router.get("")
def admin_timetable(
    date_from: date | None = None,
    date_to: date | None = None,
    class_code: str | None = None,
    course_code: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        return {
            "success": True,
            **list_admin_timetable(
                date_from=date_from,
                date_to=date_to,
                class_code=class_code,
                course_code=course_code,
                status=status,
                limit=limit,
                offset=offset,
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.patch("/sessions/{timetable_session_id}/status")
def admin_timetable_status(
    timetable_session_id: str,
    new_status: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff
    try:
        session = update_timetable_session_status(
            timetable_session_id=timetable_session_id,
            new_status=new_status,
        )
        return {
            "success": True,
            "message": "Timetable session status updated.",
            "session": session,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

