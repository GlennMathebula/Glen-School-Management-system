from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.staff_communications import (
    StaffAnnouncementCreate,
    StaffMessageReply,
    StaffMessageThreadCreate,
    StudentMessageStaffReply,
)
from app.services.staff_communications_service import (
    close_staff_message_thread,
    create_staff_announcement,
    create_staff_message_thread,
    get_staff_announcements,
    get_staff_message_directory,
    get_staff_message_thread,
    get_staff_message_threads,
    get_staff_student_message_thread,
    get_staff_student_message_threads,
    publish_staff_announcement,
    reply_to_staff_message_thread,
    reply_to_student_message_thread,
    resolve_student_message_thread,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/communications",
    tags=[
        "Staff Communications"
    ],
)


require_staff_messages = (
    require_permission(
        "USE_STAFF_MESSAGES"
    )
)

require_view_student_messages = (
    require_permission(
        "VIEW_STUDENT_MESSAGES"
    )
)

require_reply_student_messages = (
    require_permission(
        "REPLY_STUDENT_MESSAGES"
    )
)

require_view_announcements = (
    require_permission(
        "VIEW_ANNOUNCEMENTS"
    )
)

require_create_announcements = (
    require_permission(
        "CREATE_ANNOUNCEMENTS"
    )
)

require_publish_announcements = (
    require_permission(
        "PUBLISH_ANNOUNCEMENTS"
    )
)


# ============================================================
# INTERNAL STAFF MESSAGES
# ============================================================

@router.get(
    "/staff-directory"
)
def staff_message_directory(
    current_staff: dict = Depends(
        require_staff_messages
    ),
):
    try:
        records = (
            get_staff_message_directory(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                )
            )
        )

        return {
            "success": True,
            "count": len(
                records
            ),
            "staff": records,
        }

    except Exception as error:
        print(
            "ERROR: Staff messaging "
            "directory failed: "
            f"{error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Staff directory could "
                "not be loaded."
            ),
        ) from error


@router.get(
    "/staff-messages"
)
def staff_message_inbox(
    current_staff: dict = Depends(
        require_staff_messages
    ),
):
    try:
        records = (
            get_staff_message_threads(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                )
            )
        )

        return {
            "success": True,
            "count": len(
                records
            ),
            "threads": records,
        }

    except Exception as error:
        print(
            "ERROR: Staff message inbox "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Staff message inbox "
                "could not be loaded."
            ),
        ) from error


@router.post(
    "/staff-messages"
)
def staff_message_create(
    payload: StaffMessageThreadCreate,
    current_staff: dict = Depends(
        require_staff_messages
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
                subject=payload.subject,
                category=payload.category,
                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Staff message sent."
            ),
            "thread": thread,
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
            "ERROR: Staff message "
            f"creation failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Staff message could "
                "not be sent."
            ),
        ) from error


@router.get(
    "/staff-messages/{thread_id}"
)
def staff_message_detail(
    thread_id: str,
    current_staff: dict = Depends(
        require_staff_messages
    ),
):
    try:
        record = (
            get_staff_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                thread_id=thread_id,
            )
        )

        if not record:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Staff message thread "
                    "not found."
                ),
            )

        return {
            "success": True,
            "data": record,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/staff-messages/{thread_id}/reply"
)
def staff_message_reply(
    thread_id: str,
    payload: StaffMessageReply,
    current_staff: dict = Depends(
        require_staff_messages
    ),
):
    try:
        message = (
            reply_to_staff_message_thread(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                thread_id=thread_id,
                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Reply sent."
            ),
            "data": message,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.patch(
    "/staff-messages/{thread_id}/close"
)
def staff_message_close(
    thread_id: str,
    current_staff: dict = Depends(
        require_staff_messages
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
                thread_id=thread_id,
            )
        )

        return {
            "success": True,
            "message": (
                "Staff message thread closed."
            ),
            "thread": thread,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# STUDENT MESSAGE INBOX
# ============================================================

@router.get(
    "/student-messages"
)
def student_message_inbox(
    current_staff: dict = Depends(
        require_view_student_messages
    ),
):
    try:
        records = (
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
                records
            ),
            "threads": records,
        }

    except Exception as error:
        print(
            "ERROR: Student message inbox "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Student message inbox "
                "could not be loaded."
            ),
        ) from error


@router.get(
    "/student-messages/{thread_id}"
)
def student_message_detail(
    thread_id: str,
    current_staff: dict = Depends(
        require_view_student_messages
    ),
):
    try:
        record = (
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
                thread_id=thread_id,
            )
        )

        if not record:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Student message thread "
                    "not found."
                ),
            )

        return {
            "success": True,
            "data": record,
        }

    except HTTPException:
        raise

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/student-messages/{thread_id}/reply"
)
def student_message_reply(
    thread_id: str,
    payload: StudentMessageStaffReply,
    current_staff: dict = Depends(
        require_reply_student_messages
    ),
):
    try:
        message = (
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
                thread_id=thread_id,
                message_body=(
                    payload.message_body
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Reply sent to student."
            ),
            "data": message,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.patch(
    "/student-messages/{thread_id}/resolve"
)
def student_message_resolve(
    thread_id: str,
    current_staff: dict = Depends(
        require_reply_student_messages
    ),
):
    try:
        thread = (
            resolve_student_message_thread(
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
                thread_id=thread_id,
            )
        )

        return {
            "success": True,
            "message": (
                "Student message thread "
                "resolved."
            ),
            "thread": thread,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


# ============================================================
# ANNOUNCEMENTS
# ============================================================

@router.get(
    "/announcements"
)
def staff_announcements(
    current_staff: dict = Depends(
        require_view_announcements
    ),
):
    try:
        records = (
            get_staff_announcements(
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
                records
            ),
            "announcements": records,
        }

    except Exception as error:
        print(
            "ERROR: Staff announcements "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Announcements could not "
                "be loaded."
            ),
        ) from error


@router.post(
    "/announcements"
)
def staff_announcement_create(
    payload: StaffAnnouncementCreate,
    current_staff: dict = Depends(
        require_create_announcements
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
                role_code=(
                    current_staff[
                        "role_code"
                    ]
                ),
                title=payload.title,
                message=payload.message,
                announcement_type=(
                    payload.announcement_type
                ),
                priority=payload.priority,
                audience_type=(
                    payload.audience_type
                ),
                course_code=(
                    payload.course_code
                ),
                cycle_code=(
                    payload.cycle_code
                ),
                class_id=payload.class_id,
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
                "Announcement saved as Draft."
            ),
            "announcement": announcement,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/announcements/{announcement_id}/publish"
)
def staff_announcement_publish(
    announcement_id: str,
    current_staff: dict = Depends(
        require_publish_announcements
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
                "Announcement published."
            ),
            "announcement": announcement,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

