from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)

from app.models.admin_admissions import (
    AcceptApplicationRequest,
    DocumentReviewRequest,
    OutstandingDocumentsRequest,
    RegistrationRetryRequest,
    RejectApplicationRequest,
)
from app.services.staff_admissions_service import (
    accept_application,
    get_application_detail,
    get_document_checklist,
    list_applications,
    registration_detail,
    reject_application,
    request_outstanding_documents,
    retry_registration,
    review_document,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/admissions",
    tags=["Staff Admin Admissions & Registration"],
)


require_view_applications = require_permission(
    "VIEW_APPLICATIONS"
)

require_manage_applications = require_permission(
    "MANAGE_APPLICATIONS"
)

require_review_documents = require_permission(
    "REVIEW_STUDENT_DOCUMENTS"
)

require_manage_registrations = require_permission(
    "MANAGE_REGISTRATIONS"
)


def _bad_request(error: ValueError):
    raise HTTPException(
        status_code=400,
        detail=str(error),
    ) from error


def _server_error(
    error: Exception,
    message: str,
):
    print(
        f"ERROR: {message}: {error}"
    )

    raise HTTPException(
        status_code=500,
        detail=str(error),
    ) from error


@router.get("/applications")
def admin_list_applications(
    status: str | None = Query(
        default=None
    ),
    course_code: str | None = Query(
        default=None
    ),
    cycle_code: str | None = Query(
        default=None
    ),
    search: str | None = Query(
        default=None
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    current_staff: dict = Depends(
        require_view_applications
    ),
):
    try:
        return {
            "success": True,
            **list_applications(
                status=status,
                course_code=course_code,
                cycle_code=cycle_code,
                search=search,
                limit=limit,
                offset=offset,
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Admin application list failed",
        )


@router.get(
    "/applications/{student_number}"
)
def admin_application_detail(
    student_number: str,
    current_staff: dict = Depends(
        require_view_applications
    ),
):
    try:
        return {
            "success": True,
            "data": get_application_detail(
                student_number
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Admin application detail failed",
        )


@router.get(
    "/applications/{student_number}/document-checklist"
)
def admin_application_document_checklist(
    student_number: str,
    current_staff: dict = Depends(
        require_view_applications
    ),
):
    try:
        return {
            "success": True,
            "data": get_document_checklist(
                student_number
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Application document checklist failed",
        )


@router.patch(
    "/documents/{document_id}/review"
)
def admin_review_application_document(
    document_id: str,
    payload: DocumentReviewRequest,
    current_staff: dict = Depends(
        require_review_documents
    ),
):
    try:
        return {
            "success": True,
            "data": review_document(
                document_id,
                action=payload.action,
                review_notes=(
                    payload.review_notes
                ),
                actor=current_staff[
                    "staff_code"
                ],
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Applicant document review failed",
        )


@router.post(
    "/applications/{student_number}/outstanding-documents"
)
def admin_request_outstanding_documents(
    student_number: str,
    payload: OutstandingDocumentsRequest,
    current_staff: dict = Depends(
        require_manage_applications
    ),
):
    try:
        return {
            "success": True,
            "message": (
                "Outstanding documents "
                "requested successfully."
            ),
            "data": (
                request_outstanding_documents(
                    student_number,
                    documents=[
                        item.model_dump()
                        for item
                        in payload.documents
                    ],
                    actor=current_staff[
                        "staff_code"
                    ],
                )
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Outstanding-document request failed",
        )


@router.post(
    "/applications/{student_number}/accept"
)
def admin_accept_application(
    student_number: str,
    payload: AcceptApplicationRequest,
    current_staff: dict = Depends(
        require_manage_applications
    ),
    registration_staff: dict = Depends(
        require_manage_registrations
    ),
):
    try:
        result = accept_application(
            student_number,
            funding_type=(
                payload.funding_type
            ),
            cycle_code=(
                payload.cycle_code
            ),
            program_start_date=(
                payload.program_start_date
            ),
            expected_completion_date=(
                payload.expected_completion_date
            ),
            enforce_documents=(
                payload.enforce_documents
            ),
            actor=current_staff[
                "staff_code"
            ],
        )

        return {
            "success": True,
            "message": (
                "Application accepted and "
                "registration processed."
            ),
            "data": result,
        }
    except ValueError as error:
        _bad_request(error)
    except RuntimeError as error:
        _server_error(
            error,
            "Application acceptance partially failed",
        )
    except Exception as error:
        _server_error(
            error,
            "Application acceptance failed",
        )


@router.post(
    "/applications/{student_number}/reject"
)
def admin_reject_application(
    student_number: str,
    payload: RejectApplicationRequest,
    current_staff: dict = Depends(
        require_manage_applications
    ),
):
    try:
        return {
            "success": True,
            "message": (
                "Application rejected."
            ),
            "data": reject_application(
                student_number,
                reason=payload.reason,
                actor=current_staff[
                    "staff_code"
                ],
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Application rejection failed",
        )


@router.post(
    "/applications/{student_number}/registration/retry"
)
def admin_retry_registration(
    student_number: str,
    payload: RegistrationRetryRequest,
    current_staff: dict = Depends(
        require_manage_registrations
    ),
):
    try:
        return {
            "success": True,
            "message": (
                "Registration processed."
            ),
            "data": retry_registration(
                student_number,
                funding_type=(
                    payload.funding_type
                ),
                cycle_code=(
                    payload.cycle_code
                ),
                program_start_date=(
                    payload.program_start_date
                ),
                expected_completion_date=(
                    payload.expected_completion_date
                ),
                actor=current_staff[
                    "staff_code"
                ],
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Registration retry failed",
        )


@router.get(
    "/registrations/{student_number}"
)
def admin_registration_detail(
    student_number: str,
    current_staff: dict = Depends(
        require_manage_registrations
    ),
):
    try:
        return {
            "success": True,
            "data": registration_detail(
                student_number
            ),
        }
    except ValueError as error:
        _bad_request(error)
    except Exception as error:
        _server_error(
            error,
            "Registration detail failed",
        )
