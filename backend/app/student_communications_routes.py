from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.student_communications import (
    StudentMessageCreate,
    StudentMessageReply,
)
from app.services.student_communications_service import (
    create_student_message_thread,
    get_student_announcement,
    get_student_announcements,
    get_student_message_thread,
    get_student_message_threads,
    mark_announcement_read,
    reply_to_student_message_thread,
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
# ANNOUNCEMENTS
# ============================================================

@router.get(
    "/api/student/announcements"
)
def student_announcements(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        announcements = (
            get_student_announcements(
                current_student[
                    "student_number"
                ]
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

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )


@router.get(
    "/api/student/announcements/{announcement_id}"
)
def student_announcement(
    announcement_id: str,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        announcement = (
            get_student_announcement(
                current_student[
                    "student_number"
                ],
                announcement_id,
            )
        )

        return {
            "success": True,
            "announcement": (
                announcement
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )


@router.post(
    "/api/student/announcements/{announcement_id}/read"
)
def student_mark_announcement_read(
    announcement_id: str,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            mark_announcement_read(
                current_student[
                    "student_number"
                ],
                announcement_id,
            )
        )

        return {
            "success": True,
            "message": (
                "Announcement marked as read."
            ),
            "read": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )


# ============================================================
# MESSAGES
# ============================================================

@router.get(
    "/api/student/messages"
)
def student_messages(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        threads = (
            get_student_message_threads(
                current_student[
                    "student_number"
                ]
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

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )


@router.get(
    "/api/student/messages/{thread_id}"
)
def student_message_thread(
    thread_id: str,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            get_student_message_thread(
                current_student[
                    "student_number"
                ],
                thread_id,
            )
        )

        return {
            "success": True,
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )


@router.post(
    "/api/student/messages"
)
def create_student_message(
    payload: StudentMessageCreate,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            create_student_message_thread(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                subject=(
                    payload.subject
                ),
                category=(
                    payload.category
                ),
                message=(
                    payload.message
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Your message has been sent."
            ),
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )


@router.post(
    "/api/student/messages/{thread_id}/reply"
)
def reply_student_message(
    thread_id: str,
    payload: StudentMessageReply,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        message = (
            reply_to_student_message_thread(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                thread_id=(
                    thread_id
                ),
                message=(
                    payload.message
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Reply sent successfully."
            ),
            "reply": (
                message
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )