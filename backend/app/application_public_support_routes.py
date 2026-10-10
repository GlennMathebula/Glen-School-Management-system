from app.redis_read_cache import redis_cached_endpoint
from app.abuse_rate_limit import enforce_abuse_rate_limit
from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.redis_client import (
    RedisLockBusyError,
    RedisLockUnavailableError,
)
from app.models.application import (
    ApplicationIdentityRequest,
)
from app.services.student_document_service import MAX_DOCUMENT_SIZE_BYTES
from app.services.application_public_service import (
    get_public_application_catalogue,
    get_public_application_status,
    upload_application_document,
)


router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"],
)


@router.post("/status")
def public_application_status(
    identity: ApplicationIdentityRequest,
):
    # REDIS_ABUSE_RATE_LIMIT: public-application-status
    enforce_abuse_rate_limit(
        scope="public-application-status",
        identity=(
            f"{identity.student_number}|"
            f"{identity.national_id}"
        ),
        limit=12,
        window_seconds=300,
    )
    try:
        result = get_public_application_status(
            identity.student_number,
            identity.national_id,
        )

        return {
            "success": True,
            "application": result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print(
            "ERROR: Public application status "
            f"lookup failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "The application status could "
                "not be retrieved."
            ),
        )


@router.get("/catalogue")
@redis_cached_endpoint("academic-reference", key_fields=(), ttl_seconds=180)
def public_application_catalogue():
    try:
        return {
            "success": True,
            "catalogue": (
                get_public_application_catalogue()
            ),
        }
    except Exception as error:
        print(
            "ERROR: Public application catalogue "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "The application catalogue "
                "could not be loaded."
            ),
        )


@router.post(
    "/{student_number}/documents"
)
async def public_application_document_upload(
    student_number: str,
    national_id: str = Form(...),
    document_type: str = Form(...),
    document_label: str | None = Form(
        default=None
    ),
    file: UploadFile = File(...),
):
    try:
        file_bytes = await file.read(
            MAX_DOCUMENT_SIZE_BYTES + 1
        )

        result = upload_application_document(
            student_number=student_number,
            national_id=national_id,
            document_type=document_type,
            document_label=document_label,
            filename=(
                file.filename
                or "document"
            ),
            mime_type=file.content_type,
            file_bytes=file_bytes,
        )

        return {
            "success": True,
            "message": (
                "Application document uploaded "
                "successfully."
            ),
            "document": result,
        }

    except RedisLockBusyError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error),
        ) from error

    except RedisLockUnavailableError as error:
        raise HTTPException(
            status_code=503,
            detail=(
                "Document upload protection is "
                "temporarily unavailable. Please "
                "try again shortly."
            ),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        print(
            "ERROR: Public application document "
            f"upload failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "The application document "
                "could not be uploaded."
            ),
        )
