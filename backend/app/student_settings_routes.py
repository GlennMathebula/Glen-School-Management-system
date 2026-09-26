from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.student_settings import (
    StudentContactUpdate,
    StudentPreferenceUpdate,
)
from app.services.student_settings_service import (
    get_student_settings,
    update_student_contact_details,
    update_student_preferences,
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
# GET SETTINGS
# ============================================================

@router.get(
    "/api/student/settings"
)
def student_settings(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        settings = (
            get_student_settings(
                current_student[
                    "student_number"
                ]
            )
        )

        return {
            "success": True,
            "settings": settings,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# UPDATE CONTACT DETAILS
# ============================================================

@router.patch(
    "/api/student/settings/contact"
)
def update_student_contact(
    payload: StudentContactUpdate,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        changes = (
            payload.model_dump(
                exclude_unset=True
            )
        )

        result = (
            update_student_contact_details(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                changes=changes,
            )
        )

        return {
            "success": True,
            "message": (
                "Contact details updated successfully."
            ),
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


# ============================================================
# UPDATE PREFERENCES
# ============================================================

@router.patch(
    "/api/student/settings/preferences"
)
def student_update_preferences(
    payload: StudentPreferenceUpdate,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            update_student_preferences(
                student_number=(
                    current_student[
                        "student_number"
                    ]
                ),
                preferred_notification_channel=(
                    payload.preferred_notification_channel
                ),
                preferred_language=(
                    payload.preferred_language
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Preferences updated successfully."
            ),
            "preferences": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )