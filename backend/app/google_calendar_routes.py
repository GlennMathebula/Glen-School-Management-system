from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.services.google_calendar_service import (
    complete_google_calendar_connection,
    create_google_calendar_authorization_url,
    disconnect_google_calendar,
    get_google_calendar_connection,
)
from app.staff_auth_dependency import (
    get_current_staff,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/google/calendar",
    tags=[
        "Google Calendar"
    ],
)


# ============================================================
# CONNECTION STATUS
# ============================================================

@router.get(
    "/status"
)
def google_calendar_status(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        connection = (
            get_google_calendar_connection(
                current_staff[
                    "staff_account_id"
                ]
            )
        )

        if not connection:

            return {
                "success": True,
                "connected": False,
                "connection": None,
            }

        return {
            "success": True,
            "connected": bool(
                connection[
                    "is_active"
                ]
            ),
            "connection": connection,
        }

    except Exception as error:

        print(
            "ERROR: Google Calendar status "
            f"lookup failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Calendar connection "
                "status could not be retrieved."
            ),
        ) from error


# ============================================================
# CREATE GOOGLE AUTHORIZATION URL
# ============================================================

@router.get(
    "/connect"
)
def connect_google_calendar(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        authorization_url = (
            create_google_calendar_authorization_url(
                staff_account_id=(
                    current_staff[
                        "staff_account_id"
                    ]
                ),
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
                "Open the authorization URL "
                "to connect Google Calendar."
            ),
            "authorization_url": (
                authorization_url
            ),
        }

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Google Calendar OAuth URL "
            f"could not be created: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Calendar connection "
                "could not be started."
            ),
        ) from error


# ============================================================
# GOOGLE OAUTH CALLBACK
# ============================================================

@router.get(
    "/callback"
)
def google_calendar_callback(
    code: str | None = Query(
        default=None
    ),
    state: str | None = Query(
        default=None
    ),
    error: str | None = Query(
        default=None
    ),
):

    if error:

        raise HTTPException(
            status_code=400,
            detail=(
                "Google Calendar authorization "
                f"was not completed: {error}"
            ),
        )

    if not code:

        raise HTTPException(
            status_code=400,
            detail=(
                "Google authorization code "
                "was not provided."
            ),
        )

    if not state:

        raise HTTPException(
            status_code=400,
            detail=(
                "Google OAuth state "
                "was not provided."
            ),
        )

    try:

        connection = (
            complete_google_calendar_connection(
                code=(
                    code
                ),
                state=(
                    state
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Google Calendar connected "
                "successfully."
            ),
            "connection": connection,
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
            "ERROR: Google Calendar callback "
            f"failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Calendar authorization "
                "could not be completed."
            ),
        ) from error


# ============================================================
# DISCONNECT GOOGLE CALENDAR
# ============================================================

@router.post(
    "/disconnect"
)
def disconnect_staff_google_calendar(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        disconnected = (
            disconnect_google_calendar(
                current_staff[
                    "staff_account_id"
                ]
            )
        )

        if not disconnected:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Google Calendar connection "
                    "was not found."
                ),
            )

        return {
            "success": True,
            "connected": False,
            "message": (
                "Google Calendar disconnected "
                "successfully."
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Google Calendar disconnect "
            f"failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Google Calendar could "
                "not be disconnected."
            ),
        ) from error