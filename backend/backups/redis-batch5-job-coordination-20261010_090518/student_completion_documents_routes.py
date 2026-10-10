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