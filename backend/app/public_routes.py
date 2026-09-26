from fastapi import (
    APIRouter,
    HTTPException,
)

from app.models.public_registration import (
    PublicRegistrationCreate,
)
from app.services.public_registration_service import (
    register_student_publicly,
)

# ============================================================
# PUBLIC ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/public",
    tags=["Public Registration"],
)


# ============================================================
# PUBLIC STUDENT REGISTRATION
# ============================================================

@router.post(
    "/registration",
)
def public_student_registration(
    request: PublicRegistrationCreate,
):

    try:

        result = (
            register_student_publicly(
                student_number=(
                    request.student_number
                ),
                id_or_passport=(
                    request.id_or_passport
                ),
                first_name=(
                    request.first_name
                ),
                second_name=(
                    request.second_name
                ),
                last_name=(
                    request.last_name
                ),
                birth_date=(
                    request.birth_date
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Registration completed successfully. "
                "Your Student Portal account has "
                "been created."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Public registration failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Registration could not "
                "be completed."
            ),
        )