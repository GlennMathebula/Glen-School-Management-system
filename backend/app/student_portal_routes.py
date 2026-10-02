from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from app.services.student_assessment_service import (
    get_student_assessment_status,
)
from app.services.student_document_service import (
    MAX_DOCUMENT_SIZE_BYTES,
    upload_student_document,
)
from app.services.student_portal_service import (
    get_student_attendance,
    get_student_documents,
    get_student_modules,
    get_student_portal_registration,
)
from app.services.student_results_service import (
    get_student_results,
)
from app.services.student_timetable_service import (
    get_student_timetable,
)
from app.student_auth_dependency import (
    require_full_student_access,
)

# ============================================================
# STUDENT PORTAL ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/student",
    tags=["Student Portal"],
)


# ============================================================
# MY REGISTRATION
# ============================================================

@router.get(
    "/registration",
)
def my_registration(
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

        registration = (
            get_student_portal_registration(
                student_number
            )
        )

        if not registration:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Registration record "
                    "not found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                registration
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Student portal "
            "registration lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Registration information "
                "could not be retrieved."
            ),
        )


# ============================================================
# MY MODULES
# ============================================================

@router.get(
    "/modules",
)
def my_modules(
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

        modules = (
            get_student_modules(
                student_number
            )
        )

        if not modules:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Module registration "
                    "information not found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                modules
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Student portal "
            "module lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Module information could "
                "not be retrieved."
            ),
        )


# ============================================================
# MY RESULTS
# ============================================================

@router.get(
    "/results",
)
def my_results(
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

        results = (
            get_student_results(
                student_number
            )
        )

        if not results:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Student registration "
                    "could not be found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                results
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Student results "
            "lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student results could "
                "not be retrieved."
            ),
        )

# ============================================================
# MY FISA / EISA ASSESSMENT STATUS
# ============================================================

@router.get(
    "/assessment-status",
)
def my_assessment_status(
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

        assessment = (
            get_student_assessment_status(
                student_number
            )
        )

        if not assessment:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Student registration "
                    "could not be found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                assessment
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Student assessment "
            "status lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Assessment status could "
                "not be retrieved."
            ),
        )

# ============================================================
# MY OFFICIAL ATTENDANCE
# ============================================================

@router.get(
    "/attendance",
)
def my_attendance(
    current_student: dict = Depends(
        require_full_student_access
    ),
):
    student_number = current_student[
        "student_number"
    ]

    try:
        attendance = (
            get_student_attendance(
                student_number
            )
        )

        return {
            "success": True,
            "student_number": (
                student_number
            ),
            "data": attendance,
        }

    except Exception as error:
        print(
            "ERROR: Student attendance "
            "lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student attendance could "
                "not be retrieved."
            ),
        )

# ============================================================
# MY TIMETABLE
# ============================================================

@router.get(
    "/timetable",
)
def my_timetable(
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

        timetable = (
            get_student_timetable(
                student_number
            )
        )

        if not timetable:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Student registration "
                    "could not be found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                timetable
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Student timetable "
            "lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student timetable could "
                "not be retrieved."
            ),
        )

# ============================================================
# MY DOCUMENTS
# ============================================================

@router.get(
    "/documents",
)
def my_documents(
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

        documents = (
            get_student_documents(
                student_number
            )
        )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "data": (
                documents
            ),
        }

    except Exception as error:

        print(
            "ERROR: Student document "
            "centre lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student documents could "
                "not be retrieved."
            ),
        )


# ============================================================
# UPLOAD REQUESTED DOCUMENT
# ============================================================

@router.post(
    "/documents/upload",
)
async def upload_requested_document(
    request_id: str = Form(...),

    file: UploadFile = File(...),

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

        file_bytes = await file.read(
            MAX_DOCUMENT_SIZE_BYTES
            + 1
        )

        result = (
            upload_student_document(
                student_number=(
                    student_number
                ),

                request_id=(
                    request_id
                ),

                filename=(
                    file.filename
                    or "document"
                ),

                mime_type=(
                    file.content_type
                ),

                file_bytes=(
                    file_bytes
                ),
            )
        )

        return {
            "success": True,

            "message": (
                "Document uploaded "
                "successfully and submitted "
                "for review."
            ),

            "data": (
                result
            ),
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        )

    except RuntimeError as error:

        print(
            "ERROR: Document upload "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The document could not "
                "be uploaded."
            ),
        )

    except Exception as error:

        print(
            "ERROR: Unexpected student "
            "document upload failure: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The document could not "
                "be uploaded."
            ),
        )

    finally:

        await file.close()