from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.student_support import (
    StudentSupportReply,
    StudentSupportTicketCreate,
)
from app.services.student_support_service import (
    create_student_support_ticket,
    get_student_support_ticket,
    get_student_support_tickets,
    reply_to_student_support_ticket,
)
from app.student_auth_dependency import (
    require_full_student_access,
)

router = APIRouter(
    tags=[
        "Student Portal",
    ]
)


# ============================================================
# LIST SUPPORT TICKETS
# ============================================================

@router.get(
    "/api/student/support"
)
def student_support_tickets(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        tickets = (
            get_student_support_tickets(
                current_student[
                    "student_number"
                ]
            )
        )

        return {
            "success": True,
            "count": len(tickets),
            "tickets": tickets,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# GET ONE SUPPORT TICKET
# ============================================================

@router.get(
    "/api/student/support/{ticket_id}"
)
def student_support_ticket(
    ticket_id: str,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            get_student_support_ticket(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                ticket_id=ticket_id,
            )
        )

        return {
            "success": True,
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        )


# ============================================================
# CREATE SUPPORT TICKET
# ============================================================

@router.post(
    "/api/student/support"
)
def create_student_support(
    payload: StudentSupportTicketCreate,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            create_student_support_ticket(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                category=payload.category,
                subject=payload.subject,
                description=payload.description,
                priority=payload.priority,
            )
        )

        return {
            "success": True,
            "message": (
                "Support ticket created successfully."
            ),
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# REPLY TO SUPPORT TICKET
# ============================================================

@router.post(
    "/api/student/support/{ticket_id}/reply"
)
def reply_student_support(
    ticket_id: str,
    payload: StudentSupportReply,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            reply_to_student_support_ticket(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                ticket_id=ticket_id,
                message=payload.message,
            )
        )

        return {
            "success": True,
            "message": (
                "Support reply sent successfully."
            ),
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )