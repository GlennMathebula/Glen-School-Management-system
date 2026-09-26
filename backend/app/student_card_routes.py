from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import (
    FileResponse,
)
from pydantic import BaseModel, Field

from app.services.student_card_asset_service import (
    generate_student_card_qr,
    get_avatar_file_path,
    get_student_card_avatar_state,
    request_avatar_replacement,
    save_student_card_avatar,
)
from app.services.student_card_service import (
    generate_student_card_document,
    get_student_card_data,
    verify_student_card,
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
# REQUEST MODELS
# ============================================================

class AvatarReplacementRequest(
    BaseModel
):

    reason: str = Field(
        ...,
        min_length=5,
        max_length=500,
    )


# ============================================================
# GET MY STUDENT CARD
# ============================================================

@router.get(
    "/api/student/card"
)
def get_my_student_card(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        data = (
            get_student_card_data(
                student_number
            )
        )

        avatar_state = (
            get_student_card_avatar_state(
                data[
                    "card_id"
                ]
            )
        )

        avatar_available = bool(
            data[
                "avatar"
            ][
                "available"
            ]
        )

        has_official_avatar = bool(
            avatar_state.get(
                "avatar_path"
            )
        )

        replacement_requested = bool(
            avatar_state.get(
                "avatar_replacement_requested"
            )
        )

        replacement_authorized = bool(
            avatar_state.get(
                "avatar_replacement_authorized"
            )
        )

        pending_replacement = bool(
            avatar_state.get(
                "pending_avatar_path"
            )
        )

        # ----------------------------------------------------
        # Determine what the student may do
        # ----------------------------------------------------

        if not has_official_avatar:

            upload_permission = (
                "FirstUploadAllowed"
            )

            can_upload = True

            can_request_replacement = False

        elif pending_replacement:

            upload_permission = (
                "ReplacementPendingAdminReview"
            )

            can_upload = False

            can_request_replacement = False

        elif replacement_authorized:

            upload_permission = (
                "ReplacementUploadAuthorized"
            )

            can_upload = True

            can_request_replacement = False

        elif replacement_requested:

            upload_permission = (
                "ReplacementRequestPending"
            )

            can_upload = False

            can_request_replacement = False

        else:

            upload_permission = (
                "Locked"
            )

            can_upload = False

            can_request_replacement = True

        return {
            "success": True,

            "data": {
                "card_id": (
                    data[
                        "card_id"
                    ]
                ),

                "student_number": (
                    data[
                        "student_number"
                    ]
                ),

                "full_name": (
                    data[
                        "full_name"
                    ]
                ),

                "identity_type": (
                    data[
                        "identity_type"
                    ]
                ),

                "course": (
                    data[
                        "course"
                    ]
                ),

                "registration": (
                    data[
                        "registration"
                    ]
                ),

                "card": (
                    data[
                        "card"
                    ]
                ),

                "avatar": {
                    "available": (
                        avatar_available
                    ),

                    "url": (
                        "/api/student/card/avatar"
                        if avatar_available
                        else None
                    ),

                    "upload_count": (
                        avatar_state.get(
                            "avatar_upload_count"
                        )
                        or 0
                    ),

                    "upload_locked": (
                        avatar_state.get(
                            "avatar_upload_locked"
                        )
                    ),

                    "upload_permission": (
                        upload_permission
                    ),

                    "can_upload": (
                        can_upload
                    ),

                    "can_request_replacement": (
                        can_request_replacement
                    ),

                    "replacement_requested": (
                        replacement_requested
                    ),

                    "replacement_reason": (
                        avatar_state.get(
                            "avatar_replacement_reason"
                        )
                    ),

                    "replacement_requested_at": (
                        avatar_state.get(
                            "avatar_replacement_requested_at"
                        )
                    ),

                    "replacement_authorized": (
                        replacement_authorized
                    ),

                    "pending_replacement": (
                        pending_replacement
                    ),

                    "pending_status": (
                        avatar_state.get(
                            "pending_avatar_status"
                        )
                    ),
                },

                "qr_url": (
                    "/api/student/card/qr"
                ),

                "pdf_url": (
                    "/api/student/card/pdf"
                ),
            },
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR loading student card:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student card could not "
                "be loaded."
            ),
        )


# ============================================================
# UPLOAD FIRST AVATAR OR AUTHORIZED REPLACEMENT
# ============================================================

@router.post(
    "/api/student/card/avatar"
)
async def upload_student_card_avatar(
    avatar: UploadFile = File(
        ...
    ),
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        content = await avatar.read()

        mime_type = (
            avatar.content_type
            or ""
        )

        card_data = (
            get_student_card_data(
                student_number
            )
        )

        result = (
            save_student_card_avatar(
                card_id=(
                    card_data[
                        "card_id"
                    ]
                ),

                student_number=(
                    student_number
                ),

                content=(
                    content
                ),

                mime_type=(
                    mime_type
                ),
            )
        )

        if (
            result.get(
                "upload_type"
            )
            == "FirstUpload"
        ):

            message = (
                "Student card photo uploaded "
                "successfully. This photo is now "
                "locked as your official card photo."
            )

        else:

            message = (
                "Replacement photo uploaded "
                "successfully. Your existing official "
                "photo will remain in use until an "
                "administrator approves the replacement."
            )

        return {
            "success": True,

            "message": (
                message
            ),

            "upload_type": (
                result.get(
                    "upload_type"
                )
            ),

            "official": (
                result.get(
                    "official"
                )
            ),

            "pending_review": (
                result.get(
                    "pending_review",
                    False,
                )
            ),

            "avatar_upload_locked": (
                result.get(
                    "avatar_upload_locked"
                )
            ),

            "avatar_upload_count": (
                result.get(
                    "avatar_upload_count"
                )
            ),

            "updated_at": (
                result.get(
                    "avatar_updated_at"
                )
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR uploading student avatar:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student avatar could not "
                "be uploaded."
            ),
        )

    finally:

        await avatar.close()


# ============================================================
# REQUEST AVATAR REPLACEMENT
# ============================================================

@router.post(
    "/api/student/card/avatar/replacement-request"
)
def request_student_avatar_replacement(
    payload: AvatarReplacementRequest,
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        card_data = (
            get_student_card_data(
                student_number
            )
        )

        result = (
            request_avatar_replacement(
                card_id=(
                    card_data[
                        "card_id"
                    ]
                ),

                student_number=(
                    student_number
                ),

                reason=(
                    payload.reason
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Your request to replace your "
                "student card photo has been sent "
                "to administration."
            ),

            "replacement_request": {
                "requested": (
                    result[
                        "avatar_replacement_requested"
                    ]
                ),

                "reason": (
                    result[
                        "avatar_replacement_reason"
                    ]
                ),

                "requested_at": (
                    result[
                        "avatar_replacement_requested_at"
                    ]
                ),

                "status": (
                    "AwaitingAdminAuthorization"
                ),
            },
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR requesting avatar replacement:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Photo replacement request "
                "could not be submitted."
            ),
        )


# ============================================================
# GET MY OFFICIAL AVATAR
# ============================================================

@router.get(
    "/api/student/card/avatar"
)
def get_student_card_avatar(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        data = (
            get_student_card_data(
                student_number
            )
        )

        avatar_path = (
            get_avatar_file_path(
                data[
                    "avatar"
                ][
                    "path"
                ]
            )
        )

        if not avatar_path:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Student card photo "
                    "has not been uploaded."
                ),
            )

        return FileResponse(
            path=str(
                avatar_path
            ),

            media_type=(
                data[
                    "avatar"
                ][
                    "mime_type"
                ]
                or "image/jpeg"
            ),

            filename=(
                f"{student_number}_avatar.jpg"
            ),
        )

    except HTTPException:

        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR loading student avatar:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student avatar could not "
                "be loaded."
            ),
        )


# ============================================================
# GET MY QR CODE
# ============================================================

@router.get(
    "/api/student/card/qr"
)
def get_student_card_qr(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        data = (
            get_student_card_data(
                student_number
            )
        )

        qr_buffer = (
            generate_student_card_qr(
                data[
                    "verification"
                ][
                    "url"
                ]
            )
        )

        return Response(
            content=(
                qr_buffer.getvalue()
            ),

            media_type="image/png",

            headers={
                "Content-Disposition": (
                    "inline; "
                    f'filename="QR_{student_number}.png"'
                ),
            },
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR generating student card QR:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student card QR code could "
                "not be generated."
            ),
        )


# ============================================================
# GET MY STUDENT CARD PDF
# ============================================================

@router.get(
    "/api/student/card/pdf"
)
def get_student_card_pdf(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        pdf_path = (
            generate_student_card_document(
                student_number
            )
        )

        if not pdf_path.exists():

            raise HTTPException(
                status_code=500,
                detail=(
                    "Student card PDF "
                    "was not created."
                ),
            )

        return FileResponse(
            path=str(
                pdf_path
            ),

            media_type="application/pdf",

            filename=(
                f"Student_Card_"
                f"{student_number}.pdf"
            ),
        )

    except HTTPException:

        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR generating student card PDF:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student card PDF could "
                "not be generated."
            ),
        )


# ============================================================
# PUBLIC CARD VERIFICATION
# ============================================================

@router.get(
    "/api/public/student-card/verify/{token}",
    tags=[
        "Public",
    ],
)
def public_verify_student_card(
    token: str,
):

    try:

        result = (
            verify_student_card(
                token
            )
        )

        if not result[
            "valid"
        ]:

            return {
                "success": True,

                "valid": False,

                "message": (
                    result.get(
                        "reason"
                    )
                    or (
                        "This student card "
                        "is not currently valid."
                    )
                ),

                "card_status": (
                    result.get(
                        "card_status"
                    )
                ),
            }

        return {
            "success": True,

            "valid": True,

            "message": (
                "Valid Glen Moniques "
                "student card."
            ),

            "student": {
                "student_number": (
                    result[
                        "student_number"
                    ]
                ),

                "full_name": (
                    result[
                        "student_name"
                    ]
                ),
            },

            "programme": {
                "course_code": (
                    result[
                        "course_code"
                    ]
                ),

                "course_name": (
                    result[
                        "course_name"
                    ]
                ),

                "nqf_level": (
                    result[
                        "nqf_level"
                    ]
                ),

                "cycle": (
                    result[
                        "cycle"
                    ]
                ),
            },

            "card": {
                "status": (
                    result[
                        "card_status"
                    ]
                ),

                "issued_date": (
                    result[
                        "issued_date"
                    ]
                ),

                "expiry_date": (
                    result[
                        "expiry_date"
                    ]
                ),
            },
        }

    except ValueError:

        return {
            "success": True,

            "valid": False,

            "message": (
                "Invalid student card "
                "verification reference."
            ),
        }

    except Exception as error:

        print(
            "ERROR verifying student card:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student card verification "
                "could not be completed."
            ),
        )