from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.services.admin_enrolment_form_service import (
    get_latest_enrolment_form,
)
from app.services.registration_service import (
    resend_proof_of_registration,
)
from app.services.student_completion_documents_service import (
    generate_student_graduation_letter,
    generate_student_letter_of_completion,
    get_student_completion_documents,
)
from app.staff_admin_guard import require_admin_staff


router = APIRouter(
    prefix="/api/staff/admin/documents",
    tags=["Admin - Documents & Letters"],
)


def _pdf(path_value: str, filename: str):
    path = Path(path_value).resolve()

    if not path.exists() or not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Generated PDF could not be located.",
        )

    return FileResponse(
        str(path),
        filename=filename,
        media_type="application/pdf",
    )


@router.get("/{student_number}/overview")
def admin_document_overview(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff

    try:
        enrolment = get_latest_enrolment_form(
            student_number
        )
    except Exception:
        enrolment = None

    completion = None
    completion_error = None

    try:
        completion = get_student_completion_documents(
            student_number
        )
    except Exception as error:
        completion_error = str(error)

    return {
        "success": True,
        "student_number": student_number,
        "enrolment_form": (
            enrolment or {"available": False}
        ),
        "proof_of_registration": {
            "action": "Regenerate and email",
        },
        "completion": completion,
        "completion_error": completion_error,
        "document_locations": {
            "admissions_letters": "Admissions",
            "student_documents": "Student Records",
            "enrolment_and_completion": "Documents & Letters",
            "finance_documents": "Finance",
            "fisa_eisa_documents": "Assessment / EISA Administration",
        },
    }


@router.post(
    "/{student_number}/proof-of-registration/resend"
)
def admin_proof_of_registration_resend(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff

    try:
        result = resend_proof_of_registration(
            student_number
        )

        return {
            "success": True,
            "message": (
                "Proof of Registration was "
                "regenerated and processed."
            ),
            "result": result,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/{student_number}/letter-of-completion"
)
def admin_letter_of_completion(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff

    try:
        path = generate_student_letter_of_completion(
            student_number
        )

        return _pdf(
            path,
            f"{student_number}_Letter_of_Completion.pdf",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get(
    "/{student_number}/graduation-letter"
)
def admin_graduation_letter(
    student_number: str,
    current_staff: dict = Depends(require_admin_staff),
):
    del current_staff

    try:
        path = generate_student_graduation_letter(
            student_number
        )

        return _pdf(
            path,
            f"{student_number}_Graduation_Letter.pdf",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
