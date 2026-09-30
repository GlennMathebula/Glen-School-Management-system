from fastapi import APIRouter, Depends, HTTPException

from app.models.backend_finalization import (
    StudentSupportReply,
    StudentSupportStatusUpdate,
)
from app.services.staff_permission_service import require_permission
from app.services.staff_student_support_service import (
    get_student_support_ticket,
    list_student_support_tickets,
    reply_student_support_ticket,
    update_student_support_status,
)


router = APIRouter(
    prefix="/api/staff/student-support",
    tags=["Staff Student Support"],
)

require_view_support = require_permission("VIEW_STUDENT_SUPPORT")
require_reply_support = require_permission("REPLY_STUDENT_SUPPORT")


@router.get("/tickets")
def staff_student_support_tickets(
    status: str | None = None,
    current_staff: dict = Depends(require_view_support),
):
    records = list_student_support_tickets(status=status)
    return {"success": True, "count": len(records), "tickets": records}


@router.get("/tickets/{ticket_id}")
def staff_student_support_ticket(
    ticket_id: str,
    current_staff: dict = Depends(require_view_support),
):
    try:
        return {
            "success": True,
            "data": get_student_support_ticket(ticket_id),
        }
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/tickets/{ticket_id}/reply")
def staff_student_support_reply(
    ticket_id: str,
    payload: StudentSupportReply,
    current_staff: dict = Depends(require_reply_support),
):
    try:
        return {
            "success": True,
            "message": reply_student_support_ticket(
                staff_code=current_staff["staff_code"],
                ticket_id=ticket_id,
                message_body=payload.message_body,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.patch("/tickets/{ticket_id}/status")
def staff_student_support_status(
    ticket_id: str,
    payload: StudentSupportStatusUpdate,
    current_staff: dict = Depends(require_reply_support),
):
    try:
        return {
            "success": True,
            "ticket": update_student_support_status(
                staff_code=current_staff["staff_code"],
                ticket_id=ticket_id,
                status=payload.status,
            ),
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
