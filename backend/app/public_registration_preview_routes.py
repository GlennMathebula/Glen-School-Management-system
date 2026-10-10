from app.abuse_rate_limit import enforce_abuse_rate_limit
from fastapi import (
    APIRouter,
    HTTPException,
)
from pydantic import BaseModel, Field

from app.services.public_registration_preview_service import (
    get_public_registration_preview,
)


class PublicRegistrationVerifyRequest(
    BaseModel
):
    student_number: str = Field(
        min_length=8,
        max_length=8,
        pattern=r"^\d{8}$",
    )

    id_or_passport: str = Field(
        min_length=1,
        max_length=50,
    )


router = APIRouter(
    prefix="/api/public/registration",
    tags=["Public Registration"],
)


@router.post("/verify")
def verify_public_registration(
    request: PublicRegistrationVerifyRequest,
):
    # REDIS_ABUSE_RATE_LIMIT: public-registration-verify
    enforce_abuse_rate_limit(
        scope="public-registration-verify",
        identity=(
            f"{request.student_number}|"
            f"{request.id_or_passport}"
        ),
        limit=8,
        window_seconds=300,
    )
    try:
        result = (
            get_public_registration_preview(
                student_number=(
                    request.student_number
                ),
                id_or_passport=(
                    request.id_or_passport
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Accepted application verified."
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
            "ERROR: Public registration "
            f"verification failed: {error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Registration verification "
                "could not be completed."
            ),
        )
