from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import (
    FileResponse,
)

from app.services.admin_enrolment_form_service import (
    generate_admin_enrolment_form,
    get_latest_enrolment_form,
    require_latest_enrolment_form,
)
from app.staff_admin_student_records_routes import (
    require_admin_staff,
)


router = APIRouter(
    prefix="/api/staff/admin/students",
    tags=[
        "Admin - Student Records & Documents"
    ],
)


def _urls(
    student_number: str,
) -> dict:
    base = (
        "/api/staff/admin/students/"
        f"{student_number}/enrolment-form"
    )

    return {
        "view_url": base,
        "download_url": (
            base + "/download"
        ),
        "status_url": (
            base + "/status"
        ),
    }


@router.get(
    "/{student_number}/enrolment-form/status"
)
def admin_enrolment_form_status(
    student_number: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    try:
        record = (
            get_latest_enrolment_form(
                student_number
            )
        )

        if not record:
            return {
                "success": True,
                "student_number": (
                    student_number
                ),
                "available": False,
                **_urls(
                    student_number
                ),
            }

        record = dict(record)
        record.pop(
            "pdf_path",
            None,
        )

        return {
            "success": True,
            **record,
            **_urls(
                student_number
            ),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.post(
    "/{student_number}/enrolment-form/generate"
)
def admin_generate_enrolment_form(
    student_number: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    try:
        record = (
            generate_admin_enrolment_form(
                student_number
            )
        )

        record = dict(record)
        record.pop(
            "pdf_path",
            None,
        )

        return {
            "success": True,
            "message": (
                "Enrolment form generated."
            ),
            **record,
            **_urls(
                student_number
            ),
        }

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error


@router.get(
    "/{student_number}/enrolment-form"
)
def admin_view_enrolment_form(
    student_number: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    try:
        record = (
            require_latest_enrolment_form(
                student_number
            )
        )

        filename = record["filename"]

        return FileResponse(
            path=record["pdf_path"],
            media_type="application/pdf",
            headers={
                "Content-Disposition": (
                    "inline; "
                    f'filename="{filename}"'
                ),
                "Cache-Control": (
                    "private, no-store"
                ),
            },
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@router.get(
    "/{student_number}/enrolment-form/download"
)
def admin_download_enrolment_form(
    student_number: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    try:
        record = (
            require_latest_enrolment_form(
                student_number
            )
        )

        return FileResponse(
            path=record["pdf_path"],
            media_type="application/pdf",
            filename=record["filename"],
            headers={
                "Cache-Control": (
                    "private, no-store"
                ),
            },
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
