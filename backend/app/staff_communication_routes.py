from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.staff_communications import (
    StaffAnnouncementCreate,
    StaffAnnouncementUpdate,
    StaffMessageReplyCreate,
    StaffMessageThreadCreate,
    StaffSupportReplyCreate,
    StaffSupportStatusUpdate,
    StaffSupportTicketCreate,
)

from app.services.staff_announcement_service import (
    archive_staff_announcement,
    create_staff_announcement,
    get_staff_announcement,
    get_staff_announcements,
    publish_staff_announcement,
    update_staff_announcement,
)

from app.services.staff_message_service import (
    close_staff_message_thread,
    create_staff_message_thread,
    get_staff_message_thread,
    get_staff_message_threads,
    mark_staff_message_thread_read,
    reopen_staff_message_thread,
    reply_to_staff_message_thread,
)

from app.services.staff_student_communication_service import (
    get_staff_student_message_thread,
    get_staff_student_message_threads,
    get_staff_student_support_ticket,
    get_staff_student_support_tickets,
    mark_student_message_thread_read,
    mark_student_support_ticket_read,
    reply_to_student_message_thread,
    reply_to_student_support_ticket,
)

from app.services.staff_support_service import (
    create_staff_support_ticket,
    get_staff_support_ticket,
    get_staff_support_tickets,
    mark_staff_support_ticket_read,
    reply_to_staff_support_ticket,
    update_staff_support_status,
)

from app.staff_auth_dependency import (
    get_current_staff,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/staff/communications",
    tags=[
        "Staff Communications",
    ],
)


# ============================================================
# STAFF <-> STUDENT MESSAGES - LIST
# ============================================================

@router.get(
    "/messages/students"
)
def staff_student_message_threads(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        threads = (
            get_staff_student_message_threads(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "count": len(
                threads
            ),
            "threads": (
                threads
            ),
        }

    except Exception as error:

        print(
            "ERROR: Student message threads "
            "could not be loaded for staff: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student messages could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT MESSAGES - ONE THREAD
# ============================================================

@router.get(
    "/messages/students/{thread_id}"
)
def staff_student_message_thread_detail(
    thread_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            get_staff_student_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),
            )
        )

        return {
            "success": True,
            "data": (
                thread
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Student message thread "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student message thread "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT MESSAGES - REPLY
# ============================================================

@router.post(
    "/messages/students/{thread_id}/reply"
)
def staff_reply_student_message_thread(
    thread_id: str,
    payload: StaffMessageReplyCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            reply_to_student_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),

                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Reply sent to student "
                "successfully."
            ),
            "data": (
                thread
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
            "ERROR: Reply to student "
            "message failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Reply could not be sent "
                "to the student."
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT MESSAGES - MARK READ
# ============================================================

@router.post(
    "/messages/students/{thread_id}/read"
)
def staff_mark_student_message_thread_read(
    thread_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            mark_student_message_thread_read(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Student message thread "
                "marked as read."
            ),
            "data": (
                thread
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Student message read "
            "update failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student message thread "
                "could not be marked as read."
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - LIST
# ============================================================

@router.get(
    "/messages"
)
def staff_message_threads(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        threads = (
            get_staff_message_threads(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "count": len(
                threads
            ),
            "threads": (
                threads
            ),
        }

    except Exception as error:

        print(
            "ERROR: Staff message threads "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff messages could not "
                "be loaded."
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - CREATE THREAD
# ============================================================

@router.post(
    "/messages"
)
def staff_create_message_thread(
    payload: StaffMessageThreadCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            create_staff_message_thread(
                sender_staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                recipient_staff_code=(
                    payload.recipient_staff_code
                ),

                subject=(
                    payload.subject
                ),

                category=(
                    payload.category
                ),

                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Staff message thread "
                "created successfully."
            ),
            "data": (
                thread
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
            "ERROR: Staff message thread "
            "creation failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff message thread "
                "could not be created."
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - ONE THREAD
# ============================================================

@router.get(
    "/messages/{thread_id}"
)
def staff_message_thread_detail(
    thread_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            get_staff_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),
            )
        )

        return {
            "success": True,
            "data": (
                thread
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff message thread "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff message thread "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - REPLY
# ============================================================

@router.post(
    "/messages/{thread_id}/reply"
)
def staff_reply_message_thread(
    thread_id: str,
    payload: StaffMessageReplyCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            reply_to_staff_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),

                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Reply sent successfully."
            ),
            "data": (
                thread
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
            "ERROR: Staff message reply "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Reply could not be sent."
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - MARK READ
# ============================================================

@router.post(
    "/messages/{thread_id}/read"
)
def staff_mark_message_thread_read(
    thread_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            mark_staff_message_thread_read(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Message thread marked "
                "as read."
            ),
            "data": (
                thread
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff message read "
            "update failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Message thread could not "
                "be marked as read."
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - CLOSE
# ============================================================

@router.post(
    "/messages/{thread_id}/close"
)
def staff_close_message_thread(
    thread_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            close_staff_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Message thread closed."
            ),
            "data": (
                thread
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF <-> STAFF MESSAGES - REOPEN
# ============================================================

@router.post(
    "/messages/{thread_id}/reopen"
)
def staff_reopen_message_thread(
    thread_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        thread = (
            reopen_staff_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                thread_id=(
                    thread_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Message thread reopened."
            ),
            "data": (
                thread
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT SUPPORT - LIST
# ============================================================

@router.get(
    "/support/students"
)
def staff_student_support_tickets(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        tickets = (
            get_staff_student_support_tickets(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "count": len(
                tickets
            ),
            "tickets": (
                tickets
            ),
        }

    except Exception as error:

        print(
            "ERROR: Student support tickets "
            "could not be loaded for staff: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student support tickets "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT SUPPORT - ONE TICKET
# ============================================================

@router.get(
    "/support/students/{ticket_id}"
)
def staff_student_support_ticket_detail(
    ticket_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            get_staff_student_support_ticket(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),
            )
        )

        return {
            "success": True,
            "data": (
                ticket
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Student support ticket "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student support ticket "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT SUPPORT - REPLY
# ============================================================

@router.post(
    "/support/students/{ticket_id}/reply"
)
def staff_reply_student_support_ticket(
    ticket_id: str,
    payload: StaffSupportReplyCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            reply_to_student_support_ticket(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),

                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Reply sent to student "
                "support ticket successfully."
            ),
            "data": (
                ticket
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
            "ERROR: Student support reply "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student support reply "
                "could not be sent."
            ),
        ) from error


# ============================================================
# STAFF <-> STUDENT SUPPORT - MARK READ
# ============================================================

@router.post(
    "/support/students/{ticket_id}/read"
)
def staff_mark_student_support_ticket_read(
    ticket_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            mark_student_support_ticket_read(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Student support ticket "
                "marked as read."
            ),
            "data": (
                ticket
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Student support read "
            "update failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student support ticket "
                "could not be marked as read."
            ),
        ) from error


# ============================================================
# STAFF SUPPORT - LIST
# ============================================================

@router.get(
    "/support"
)
def staff_support_tickets(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        tickets = (
            get_staff_support_tickets(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "count": len(
                tickets
            ),
            "tickets": (
                tickets
            ),
        }

    except Exception as error:

        print(
            "ERROR: Staff support tickets "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff support tickets "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# STAFF SUPPORT - CREATE
# ============================================================

@router.post(
    "/support"
)
def staff_create_support_ticket(
    payload: StaffSupportTicketCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            create_staff_support_ticket(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                category=(
                    payload.category
                ),

                subject=(
                    payload.subject
                ),

                description=(
                    payload.description
                ),

                priority=(
                    payload.priority
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Support ticket created "
                "successfully."
            ),
            "data": (
                ticket
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
            "ERROR: Staff support ticket "
            "creation failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Support ticket could "
                "not be created."
            ),
        ) from error


# ============================================================
# STAFF SUPPORT - ONE TICKET
# ============================================================

@router.get(
    "/support/{ticket_id}"
)
def staff_support_ticket_detail(
    ticket_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            get_staff_support_ticket(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),
            )
        )

        return {
            "success": True,
            "data": (
                ticket
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF SUPPORT - REPLY
# ============================================================

@router.post(
    "/support/{ticket_id}/reply"
)
def staff_reply_support_ticket(
    ticket_id: str,
    payload: StaffSupportReplyCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            reply_to_staff_support_ticket(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),

                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Support reply sent "
                "successfully."
            ),
            "data": (
                ticket
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF SUPPORT - MARK READ
# ============================================================

@router.post(
    "/support/{ticket_id}/read"
)
def staff_mark_support_ticket_read(
    ticket_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            mark_staff_support_ticket_read(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Support ticket marked "
                "as read."
            ),
            "data": (
                ticket
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF SUPPORT - UPDATE STATUS
# ============================================================

@router.put(
    "/support/{ticket_id}/status"
)
def staff_update_support_status(
    ticket_id: str,
    payload: StaffSupportStatusUpdate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        ticket = (
            update_staff_support_status(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                ticket_id=(
                    ticket_id
                ),

                status=(
                    payload.status
                ),

                resolution_notes=(
                    payload.resolution_notes
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Support ticket status "
                "updated successfully."
            ),
            "data": (
                ticket
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF ANNOUNCEMENTS - LIST
# ============================================================

@router.get(
    "/announcements"
)
def staff_announcements(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        announcements = (
            get_staff_announcements(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "count": len(
                announcements
            ),
            "announcements": (
                announcements
            ),
        }

    except Exception as error:

        print(
            "ERROR: Staff announcements "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff announcements "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# STAFF ANNOUNCEMENTS - CREATE
# ============================================================

@router.post(
    "/announcements"
)
def staff_create_announcement(
    payload: StaffAnnouncementCreate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        announcement = (
            create_staff_announcement(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                title=(
                    payload.title
                ),

                message=(
                    payload.message
                ),

                announcement_type=(
                    payload.announcement_type
                ),

                priority=(
                    payload.priority
                ),

                audience_type=(
                    payload.audience_type
                ),

                course_code=(
                    payload.course_code
                ),

                cycle_code=(
                    payload.cycle_code
                ),

                class_id=(
                    payload.class_id
                ),

                student_number=(
                    payload.student_number
                ),

                expires_at=(
                    payload.expires_at
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Announcement created "
                "successfully as a draft."
            ),
            "data": (
                announcement
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
            "ERROR: Staff announcement "
            "creation failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Announcement could not "
                "be created."
            ),
        ) from error


# ============================================================
# STAFF ANNOUNCEMENTS - ONE
# ============================================================

@router.get(
    "/announcements/{announcement_id}"
)
def staff_announcement_detail(
    announcement_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        announcement = (
            get_staff_announcement(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                announcement_id=(
                    announcement_id
                ),
            )
        )

        return {
            "success": True,
            "data": (
                announcement
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF ANNOUNCEMENTS - UPDATE DRAFT
# ============================================================

@router.put(
    "/announcements/{announcement_id}"
)
def staff_update_announcement(
    announcement_id: str,
    payload: StaffAnnouncementUpdate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        updates = (
            payload.model_dump(
                exclude_unset=True
            )
        )

        announcement = (
            update_staff_announcement(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                announcement_id=(
                    announcement_id
                ),

                updates=(
                    updates
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Announcement updated "
                "successfully."
            ),
            "data": (
                announcement
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF ANNOUNCEMENTS - PUBLISH
# ============================================================

@router.post(
    "/announcements/{announcement_id}/publish"
)
def staff_publish_announcement(
    announcement_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        announcement = (
            publish_staff_announcement(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                announcement_id=(
                    announcement_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Announcement published "
                "successfully."
            ),
            "data": (
                announcement
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STAFF ANNOUNCEMENTS - ARCHIVE
# ============================================================

@router.post(
    "/announcements/{announcement_id}/archive"
)
def staff_archive_announcement(
    announcement_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        announcement = (
            archive_staff_announcement(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                announcement_id=(
                    announcement_id
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Announcement archived "
                "successfully."
            ),
            "data": (
                announcement
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error