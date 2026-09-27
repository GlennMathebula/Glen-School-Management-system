from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.models.staff_notifications import (
    StaffNotificationReadUpdate,
)

from app.services.staff_notification_service import (
    get_pending_desktop_notifications,
    get_staff_notification,
    get_staff_notifications,
    get_staff_unread_notification_count,
    mark_all_staff_notifications_read,
    mark_desktop_popup_delivered,
    mark_staff_notification_read,
    mark_staff_notification_unread,
)

from app.staff_auth_dependency import (
    get_current_staff,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/staff/notifications",
    tags=[
        "Staff Notifications",
    ],
)


# ============================================================
# LIST NOTIFICATIONS
# ============================================================

@router.get("")
def staff_notifications(
    unread_only: bool = Query(
        default=False
    ),

    limit: int = Query(
        default=100,
        ge=1,
        le=200,
    ),

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        notifications = (
            get_staff_notifications(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                unread_only=(
                    unread_only
                ),

                limit=(
                    limit
                ),
            )
        )

        return {
            "success": True,

            "staff_code": (
                current_staff[
                    "staff_code"
                ]
            ),

            "count": len(
                notifications
            ),

            "notifications": (
                notifications
            ),
        }

    except Exception as error:

        print(
            "ERROR: Staff notifications "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff notifications could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# UNREAD COUNT
# ============================================================

@router.get(
    "/unread-count"
)
def staff_notification_unread_count(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        count = (
            get_staff_unread_notification_count(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,

            "staff_code": (
                current_staff[
                    "staff_code"
                ]
            ),

            "unread_count": (
                count
            ),
        }

    except Exception as error:

        print(
            "ERROR: Staff notification "
            "unread count failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unread notification count "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# DESKTOP POPUP QUEUE
# ============================================================

@router.get(
    "/desktop-pending"
)
def staff_pending_desktop_notifications(
    limit: int = Query(
        default=20,
        ge=1,
        le=50,
    ),

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        notifications = (
            get_pending_desktop_notifications(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                limit=(
                    limit
                ),
            )
        )

        return {
            "success": True,

            "staff_code": (
                current_staff[
                    "staff_code"
                ]
            ),

            "count": len(
                notifications
            ),

            "notifications": (
                notifications
            ),
        }

    except Exception as error:

        print(
            "ERROR: Desktop notification "
            "queue failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Desktop notifications "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# MARK ALL AS READ
# ============================================================

@router.post(
    "/read-all"
)
def staff_mark_all_notifications_read(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        result = (
            mark_all_staff_notifications_read(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "All notifications marked "
                "as read."
            ),

            "data": (
                result
            ),
        }

    except Exception as error:

        print(
            "ERROR: Mark all staff "
            "notifications read failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Notifications could not "
                "be marked as read."
            ),
        ) from error


# ============================================================
# GET ONE NOTIFICATION
# ============================================================

@router.get(
    "/{notification_id}"
)
def staff_notification_detail(
    notification_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        notification = (
            get_staff_notification(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                notification_id=(
                    notification_id
                ),
            )
        )

        return {
            "success": True,
            "data": (
                notification
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
            "ERROR: Staff notification "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Notification could not "
                "be loaded."
            ),
        ) from error


# ============================================================
# MARK READ / UNREAD
# ============================================================

@router.patch(
    "/{notification_id}/read"
)
def staff_update_notification_read_status(
    notification_id: str,

    payload: StaffNotificationReadUpdate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        if payload.is_read:

            notification = (
                mark_staff_notification_read(
                    staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    ),

                    notification_id=(
                        notification_id
                    ),
                )
            )

            message = (
                "Notification marked as read."
            )

        else:

            notification = (
                mark_staff_notification_unread(
                    staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    ),

                    notification_id=(
                        notification_id
                    ),
                )
            )

            message = (
                "Notification marked as unread."
            )

        return {
            "success": True,
            "message": (
                message
            ),
            "data": (
                notification
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
            "ERROR: Notification read "
            "status update failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Notification read status "
                "could not be updated."
            ),
        ) from error


# ============================================================
# CONFIRM DESKTOP POPUP DELIVERED
# ============================================================

@router.post(
    "/{notification_id}/popup-delivered"
)
def staff_notification_popup_delivered(
    notification_id: str,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        notification = (
            mark_desktop_popup_delivered(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                notification_id=(
                    notification_id
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Desktop popup delivery "
                "recorded successfully."
            ),

            "data": (
                notification
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
            "ERROR: Desktop popup delivery "
            "could not be recorded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Desktop popup delivery "
                "could not be recorded."
            ),
        ) from error