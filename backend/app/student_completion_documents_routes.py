from app.critical_write_guard import redis_guarded_endpoint
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import FileResponse

from app.services.student_completion_documents_service import (
    generate_student_graduation_letter,
    generate_student_letter_of_completion,
    get_student_completion_documents,
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
# COMPLETION DOCUMENTS DASHBOARD
# ============================================================

@router.get(
    "/api/student/completion-documents"
)
def student_completion_documents(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        result = (
            get_student_completion_documents(
                current_student[
                    "student_number"
                ]
            )
        )

        return {
            "success": True,
            **result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )


# ============================================================
# LETTER OF COMPLETION
# ============================================================

@router.get(
    "/api/student/completion-documents/"
    "letter-of-completion"
)
@redis_guarded_endpoint("job:completion-letter", key_fields=("current_student.student_number",), ttl_seconds=300, busy_message="Your completion letter is already being generated.", unavailable_message="Completion-letter generation protection is temporarily unavailable. Please try again shortly.", fail_open=False)
def download_letter_of_completion(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        pdf_path = (
            generate_student_letter_of_completion(
                current_student[
                    "student_number"
                ]
            )
        )

        path = Path(
            pdf_path
        )

        return FileResponse(
            path=str(
                path
            ),
            media_type="application/pdf",
            filename=path.name,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=409,
            detail=str(
                error
            ),
        )


# ============================================================
# GRADUATION LETTER
# ============================================================

@router.get(
    "/api/student/completion-documents/"
    "graduation-letter"
)
@redis_guarded_endpoint("job:graduation-letter", key_fields=("current_student.student_number",), ttl_seconds=300, busy_message="Your graduation letter is already being generated.", unavailable_message="Graduation-letter generation protection is temporarily unavailable. Please try again shortly.", fail_open=False)
def download_graduation_letter(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    try:

        pdf_path = (
            generate_student_graduation_letter(
                current_student[
                    "student_number"
                ]
            )
        )

        path = Path(
            pdf_path
        )

        return FileResponse(
            path=str(
                path
            ),
            media_type="application/pdf",
            filename=path.name,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=409,
            detail=str(
                error
            ),
        )