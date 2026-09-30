from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.services.staff_notification_service import (
    get_staff_notifications,
    get_staff_unread_notification_count,
    mark_all_staff_notifications_read,
    mark_staff_notification_read,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/notifications",
    tags=[
        "Staff Notifications"
    ],
)


require_view_notifications = (
    require_permission(
        "VIEW_NOTIFICATIONS"
    )
)


@router.get(
    ""
)
def staff_notifications(
    unread_only: bool = False,
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_staff: dict = Depends(
        require_view_notifications
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
                limit=limit,
            )
        )

        return {
            "success": True,
            "count": len(
                notifications
            ),
            "notifications": (
                notifications
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


@router.get(
    "/unread-count"
)
def staff_notification_unread_count(
    current_staff: dict = Depends(
        require_view_notifications
    ),
):
    try:
        count = (
            get_staff_unread_notification_count(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                )
            )
        )

        return {
            "success": True,
            "unread_count": count,
        }

    except Exception as error:
        print(
            "ERROR: Staff unread notification "
            "count could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unread notification count "
                "could not be loaded."
            ),
        ) from error


@router.patch(
    "/read-all"
)
def staff_notifications_mark_all_read(
    current_staff: dict = Depends(
        require_view_notifications
    ),
):
    try:
        updated_count = (
            mark_all_staff_notifications_read(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                )
            )
        )

        return {
            "success": True,
            "message": (
                "Notifications marked as read."
            ),
            "updated_count": (
                updated_count
            ),
        }

    except Exception as error:
        print(
            "ERROR: Staff notifications "
            "could not all be marked read: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Notifications could not all "
                "be marked as read."
            ),
        ) from error


@router.patch(
    "/{notification_id}/read"
)
def staff_notification_mark_read(
    notification_id: str,
    current_staff: dict = Depends(
        require_view_notifications
    ),
):
    try:
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

        if not notification:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Notification not found."
                ),
            )

        return {
            "success": True,
            "message": (
                "Notification marked as read."
            ),
            "notification": (
                notification
            ),
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

    except Exception as error:
        print(
            "ERROR: Staff notification "
            "could not be marked read: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Notification could not be "
                "marked as read."
            ),
        ) from error

