from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi.responses import FileResponse

from app.services.finance_document_service import (
    generate_student_invoice,
    generate_student_payment_plan,
    generate_student_receipt,
    generate_student_statement,
)
from app.student_auth_dependency import (
    require_full_student_access,
)

router = APIRouter(
    prefix="/api/student/finance/documents",
    tags=[
        "Student Portal"
    ],
)


# ============================================================
# FILE RESPONSE HELPER
# ============================================================

def return_pdf(
    file_path: Path,
    download_name: str,
):

    file_path = Path(
        file_path
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Generated PDF could not be found."
            ),
        )

    return FileResponse(
        path=str(
            file_path
        ),
        media_type="application/pdf",
        filename=download_name,
    )


# ============================================================
# INVOICE
# ============================================================

@router.get(
    "/invoice/{invoice_number}",
)
def download_invoice(
    invoice_number: str,
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

        file_path = (
            generate_student_invoice(
                student_number,
                invoice_number,
            )
        )

        return return_pdf(
            file_path,
            f"{invoice_number}.pdf",
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR generating student invoice:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Invoice could not be generated."
            ),
        )


# ============================================================
# RECEIPT
# ============================================================

@router.get(
    "/receipt/{receipt_number}",
)
def download_receipt(
    receipt_number: str,
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

        file_path = (
            generate_student_receipt(
                student_number,
                receipt_number,
            )
        )

        return return_pdf(
            file_path,
            f"{receipt_number}.pdf",
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR generating student receipt:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Receipt could not be generated."
            ),
        )


# ============================================================
# STATEMENT
# ============================================================

@router.get(
    "/statement",
)
def download_statement(
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

        file_path = (
            generate_student_statement(
                student_number
            )
        )

        return return_pdf(
            file_path,
            (
                f"STATEMENT-"
                f"{student_number}.pdf"
            ),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR generating student statement:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Statement could not be generated."
            ),
        )


# ============================================================
# PAYMENT PLAN
# ============================================================

@router.get(
    "/payment-plan/{payment_plan_id}",
)
def download_payment_plan(
    payment_plan_id: str,
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

        file_path = (
            generate_student_payment_plan(
                student_number,
                payment_plan_id,
            )
        )

        return return_pdf(
            file_path,
            (
                f"PAYMENT-PLAN-"
                f"{student_number}.pdf"
            ),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        )

    except Exception as error:

        print(
            "ERROR generating payment plan:",
            error,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Payment plan could not be generated."
            ),
        )