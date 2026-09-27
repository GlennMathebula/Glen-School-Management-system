from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.facilitator_attendance import (
    FacilitatorAttendanceCaptureRequest,
)
from app.services.attendance_service import (
    capture_attendance,
    create_attendance_session,
    get_attendance_roster,
    submit_attendance,
)
from app.services.facilitator_attendance_history_service import (
    get_facilitator_attendance_history,
    get_facilitator_class_attendance_history,
)
from app.services.facilitator_service import (
    facilitator_owns_attendance_session,
    facilitator_owns_timetable_session,
    get_facilitator_class,
    get_facilitator_classes,
    get_facilitator_class_learners,
    get_facilitator_class_timetable,
    get_facilitator_timetable,
)
from app.services.facilitator_google_calendar_service import (
    sync_facilitator_timetable_to_google,
)
from app.services.staff_auth_service import (
    get_staff_profile,
)
from app.staff_auth_dependency import (
    require_facilitator,
)

from app.models.facilitator_notifications import (
    FacilitatorSessionNotificationRequest,
)
from app.services.facilitator_session_notification_service import (
    notify_learners_about_session,
)
router = APIRouter(
    prefix="/api/staff/facilitator",
    tags=[
        "Facilitator Portal"
    ],
)


# ============================================================
# FACILITATOR PROFILE
# ============================================================

@router.get(
    "/me"
)
def facilitator_profile(
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        profile = get_staff_profile(
            current_staff[
                "staff_account_id"
            ]
        )

        return {
            "success": True,
            "facilitator": profile,
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
            "ERROR: Facilitator profile "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Facilitator profile could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR CLASSES
# ============================================================

@router.get(
    "/classes"
)
def facilitator_classes(
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        classes = (
            get_facilitator_classes(
                current_staff[
                    "staff_code"
                ]
            )
        )

        return {
            "success": True,
            "count": len(
                classes
            ),
            "classes": classes,
        }

    except Exception as error:
        print(
            "ERROR: Facilitator classes "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Facilitator classes could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR TIMETABLE
# ============================================================

@router.get(
    "/timetable"
)
def facilitator_timetable(
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        sessions = (
            get_facilitator_timetable(
                current_staff[
                    "staff_code"
                ]
            )
        )

        return {
            "success": True,
            "count": len(
                sessions
            ),
            "sessions": sessions,
        }

    except Exception as error:
        print(
            "ERROR: Facilitator timetable "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Facilitator timetable could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR ATTENDANCE HISTORY
# ============================================================

@router.get(
    "/attendance"
)
def facilitator_attendance_history(
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        history = (
            get_facilitator_attendance_history(
                current_staff[
                    "staff_code"
                ]
            )
        )

        return {
            "success": True,
            "count": len(
                history
            ),
            "attendance": history,
        }

    except Exception as error:
        print(
            "ERROR: Facilitator attendance "
            "history could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Attendance history could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR CLASS DETAIL
# ============================================================

@router.get(
    "/classes/{class_code}"
)
def facilitator_class_detail(
    class_code: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        class_record = (
            get_facilitator_class(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                class_code=(
                    class_code
                ),
            )
        )

        if not class_record:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Class not found or not "
                    "assigned to this facilitator."
                ),
            )

        return {
            "success": True,
            "class": class_record,
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "ERROR: Facilitator class "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Facilitator class could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR CLASS LEARNERS
# ============================================================

@router.get(
    "/classes/{class_code}/learners"
)
def facilitator_class_learners(
    class_code: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        learners = (
            get_facilitator_class_learners(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                class_code=(
                    class_code
                ),
            )
        )

        if learners is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Class not found or not "
                    "assigned to this facilitator."
                ),
            )

        return {
            "success": True,
            "class_code": class_code,
            "count": len(
                learners
            ),
            "learners": learners,
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "ERROR: Facilitator learner list "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Facilitator learner list could "
                "not be loaded."
            ),
        ) from error

# ============================================================
# SYNC TIMETABLE SESSION TO GOOGLE CALENDAR
# ============================================================

@router.post(
    "/timetable/{timetable_session_id}/sync-calendar"
)
def facilitator_sync_timetable_to_google_calendar(
    timetable_session_id: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        sync_result = (
            sync_facilitator_timetable_to_google(
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
                timetable_session_id=(
                    timetable_session_id
                ),
            )
        )

        notification_result = None

        delivery_mode = (
            sync_result.get(
                "delivery_mode"
            )
            or ""
        ).strip().lower()

        if delivery_mode in {
            "online",
            "hybrid",
            "blended",
        }:

            notification_result = (
                notify_learners_about_session(
                    staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    ),
                    timetable_session_id=(
                        timetable_session_id
                    ),
                    force_resend=False,
                )
            )

        return {
            "success": True,
            "message": (
                "Timetable session synced "
                "to Google Calendar successfully."
            ),
            "calendar": (
                sync_result
            ),
            "learner_notifications": (
                notification_result
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
            "ERROR: Google Calendar timetable "
            "sync failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Timetable session could not "
                "be synced to Google Calendar."
            ),
        ) from error
# ============================================================
# FACILITATOR CLASS TIMETABLE
# ============================================================

@router.get(
    "/classes/{class_code}/timetable"
)
def facilitator_class_timetable(
    class_code: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        sessions = (
            get_facilitator_class_timetable(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                class_code=(
                    class_code
                ),
            )
        )

        if sessions is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Class not found or not "
                    "assigned to this facilitator."
                ),
            )

        return {
            "success": True,
            "class_code": class_code,
            "count": len(
                sessions
            ),
            "sessions": sessions,
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "ERROR: Facilitator class timetable "
            "could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Facilitator class timetable "
                "could not be loaded."
            ),
        ) from error


# ============================================================
# FACILITATOR CLASS ATTENDANCE HISTORY
# ============================================================

@router.get(
    "/classes/{class_code}/attendance"
)
def facilitator_class_attendance_history(
    class_code: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        history = (
            get_facilitator_class_attendance_history(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                class_code=(
                    class_code
                ),
            )
        )

        if history is None:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Class not found or not "
                    "assigned to this facilitator."
                ),
            )

        return {
            "success": True,
            "class_code": class_code,
            "count": len(
                history
            ),
            "attendance": history,
        }

    except HTTPException:
        raise

    except Exception as error:
        print(
            "ERROR: Facilitator class attendance "
            "history could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Class attendance history could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# CREATE / OPEN ATTENDANCE SESSION
# ============================================================

@router.post(
    "/attendance/sessions/{timetable_session_id}"
)
def facilitator_create_attendance_session(
    timetable_session_id: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        owns_session = (
            facilitator_owns_timetable_session(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                timetable_session_id=(
                    timetable_session_id
                ),
            )
        )

        if not owns_session:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Timetable session not found "
                    "or not assigned to this "
                    "facilitator."
                ),
            )

        attendance_session = (
            create_attendance_session(
                timetable_session_id=(
                    timetable_session_id
                ),
                captured_by=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "attendance_session": (
                attendance_session
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
            "ERROR: Facilitator attendance "
            "session could not be created: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Attendance session could "
                "not be created."
            ),
        ) from error


# ============================================================
# GET ATTENDANCE ROSTER
# ============================================================

@router.get(
    "/attendance/{attendance_session_id}"
)
def facilitator_attendance_roster(
    attendance_session_id: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        owns_session = (
            facilitator_owns_attendance_session(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                attendance_session_id=(
                    attendance_session_id
                ),
            )
        )

        if not owns_session:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Attendance session not found "
                    "or not assigned to this "
                    "facilitator."
                ),
            )

        roster = (
            get_attendance_roster(
                attendance_session_id
            )
        )

        return {
            "success": True,
            "data": roster,
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
            "ERROR: Facilitator attendance "
            "roster could not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Attendance roster could "
                "not be loaded."
            ),
        ) from error


# ============================================================
# CAPTURE ATTENDANCE
# ============================================================

@router.put(
    "/attendance/{attendance_session_id}"
)
def facilitator_capture_attendance(
    attendance_session_id: str,
    payload: FacilitatorAttendanceCaptureRequest,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        owns_session = (
            facilitator_owns_attendance_session(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                attendance_session_id=(
                    attendance_session_id
                ),
            )
        )

        if not owns_session:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Attendance session not found "
                    "or not assigned to this "
                    "facilitator."
                ),
            )

        records = [
            record.model_dump()
            for record in payload.records
        ]

        result = (
            capture_attendance(
                attendance_session_id=(
                    attendance_session_id
                ),
                captured_by=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                records=(
                    records
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Attendance saved successfully."
            ),
            "data": result,
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
            "ERROR: Facilitator attendance "
            "capture failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Attendance could not "
                "be saved."
            ),
        ) from error


# ============================================================
# SUBMIT ATTENDANCE
# ============================================================

@router.post(
    "/attendance/{attendance_session_id}/submit"
)
def facilitator_submit_attendance(
    attendance_session_id: str,
    current_staff: dict = Depends(
        require_facilitator
    ),
):
    try:
        owns_session = (
            facilitator_owns_attendance_session(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                attendance_session_id=(
                    attendance_session_id
                ),
            )
        )

        if not owns_session:
            raise HTTPException(
                status_code=404,
                detail=(
                    "Attendance session not found "
                    "or not assigned to this "
                    "facilitator."
                ),
            )

        result = (
            submit_attendance(
                attendance_session_id=(
                    attendance_session_id
                ),
                submitted_by=(
                    current_staff[
                        "staff_code"
                    ]
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Attendance submitted "
                "successfully."
            ),
            "attendance_session": (
                result
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
            "ERROR: Facilitator attendance "
            "submission failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Attendance could not "
                "be submitted."
            ),
        ) from error
    
# ============================================================
# EMAIL LEARNERS ABOUT TIMETABLE SESSION
# ============================================================

@router.post(
    "/timetable/{timetable_session_id}/notify-learners"
)
def facilitator_notify_learners(
    timetable_session_id: str,
    payload: FacilitatorSessionNotificationRequest,
    current_staff: dict = Depends(
        require_facilitator
    ),
):

    try:

        result = (
            notify_learners_about_session(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),
                timetable_session_id=(
                    timetable_session_id
                ),
                force_resend=(
                    payload.force_resend
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Learner email notification "
                "process completed."
            ),
            "data": result,
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
            "ERROR: Learner timetable "
            "notification failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Learners could not be "
                "notified."
            ),
        ) from error