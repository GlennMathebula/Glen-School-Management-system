from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse

from app.models.staff_finance import (
    FinanceChargeCreate,
    FinanceCreditCreate,
    FinancePaymentCreate,
    FinancePaymentPlanCreate,
    FinancePaymentReverse,
    FinanceSponsorAssign,
    FinanceSponsorCreate,
)
from app.services.staff_finance_service import (
    apply_credit,
    assign_sponsor,
    create_charge,
    create_payment_plan,
    create_sponsor,
    create_statement,
    generate_finance_document,
    get_finance_dashboard,
    get_latest_payment_plan,
    get_student_finance,
    list_sponsors,
    list_statements,
    list_student_invoices,
    list_student_payments,
    list_student_receipts,
    record_payment,
    reverse_payment,
    run_finance_report,
    search_finance_students,
)
from app.services.staff_permission_service import (
    require_permission,
)


router = APIRouter(
    prefix="/api/staff/finance",
    tags=[
        "CFO & Financial Officer"
    ],
)


require_view_finance = (
    require_permission(
        "VIEW_FINANCE"
    )
)

require_manage_payments = (
    require_permission(
        "MANAGE_PAYMENTS"
    )
)

require_manage_invoices = (
    require_permission(
        "MANAGE_INVOICES"
    )
)

require_manage_payment_plans = (
    require_permission(
        "MANAGE_PAYMENT_PLANS"
    )
)

require_manage_sponsors = (
    require_permission(
        "MANAGE_SPONSORS"
    )
)

require_assign_sponsors = (
    require_permission(
        "ASSIGN_SPONSORS"
    )
)

require_generate_statements = (
    require_permission(
        "GENERATE_FINANCE_STATEMENTS"
    )
)

require_view_finance_reports = (
    require_permission(
        "VIEW_FINANCE_REPORTS"
    )
)

require_approve_adjustments = (
    require_permission(
        "APPROVE_FINANCE_ADJUSTMENTS"
    )
)


@router.get(
    "/dashboard"
)
def finance_dashboard(
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    try:
        return {
            "success": True,
            "data": (
                get_finance_dashboard()
            ),
        }
    except Exception as error:
        print(
            "ERROR: Finance dashboard "
            f"failed: {error}"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "Finance dashboard could "
                "not be loaded."
            ),
        ) from error


@router.get(
    "/students"
)
def finance_students(
    search: str | None = None,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    records = (
        search_finance_students(
            search=search,
            limit=limit,
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "students": records,
    }


@router.get(
    "/students/{student_number}"
)
def finance_student_detail(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    try:
        return {
            "success": True,
            "data": (
                get_student_finance(
                    student_number=(
                        student_number
                    )
                )
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/students/{student_number}/charges"
)
def finance_charge_create(
    student_number: str,
    payload: FinanceChargeCreate,
    current_staff: dict = Depends(
        require_manage_invoices
    ),
):
    try:
        record = create_charge(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            student_number=(
                student_number
            ),
            charge_type=(
                payload.charge_type
            ),
            amount=payload.amount,
            description=(
                payload.description
            ),
            due_date=(
                payload.due_date
            ),
        )

        return {
            "success": True,
            "message": (
                "Charge and invoice created."
            ),
            "invoice": record,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/students/{student_number}/payments"
)
def finance_student_payments(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    records = list_student_payments(
        student_number=(
            student_number
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "payments": records,
    }


@router.post(
    "/students/{student_number}/payments"
)
def finance_payment_create(
    student_number: str,
    payload: FinancePaymentCreate,
    current_staff: dict = Depends(
        require_manage_payments
    ),
):
    try:
        record = record_payment(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            student_number=(
                student_number
            ),
            amount=payload.amount,
            method=payload.method,
            reference=(
                payload.reference
            ),
            invoice_number=(
                payload.invoice_number
            ),
        )

        return {
            "success": True,
            "message": (
                "Payment recorded and "
                "receipt created."
            ),
            "data": record,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/payments/{payment_id}/reverse"
)
def finance_payment_reverse(
    payment_id: str,
    payload: FinancePaymentReverse,
    current_staff: dict = Depends(
        require_approve_adjustments
    ),
):
    try:
        return {
            "success": True,
            "message": (
                "Payment reversed."
            ),
            "data": (
                reverse_payment(
                    actor_staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    ),
                    payment_id=payment_id,
                    reason=payload.reason,
                )
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/students/{student_number}/credit"
)
def finance_credit_create(
    student_number: str,
    payload: FinanceCreditCreate,
    current_staff: dict = Depends(
        require_approve_adjustments
    ),
):
    try:
        account = apply_credit(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            student_number=(
                student_number
            ),
            amount=payload.amount,
            reason=payload.reason,
        )

        return {
            "success": True,
            "message": (
                "Finance credit applied."
            ),
            "account": account,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/students/{student_number}/invoices"
)
def finance_student_invoices(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    records = list_student_invoices(
        student_number=(
            student_number
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "invoices": records,
    }


@router.get(
    "/students/{student_number}/receipts"
)
def finance_student_receipts(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    records = list_student_receipts(
        student_number=(
            student_number
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "receipts": records,
    }


@router.get(
    "/students/{student_number}/payment-plan"
)
def finance_student_payment_plan(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    return {
        "success": True,
        "payment_plan": (
            get_latest_payment_plan(
                student_number=(
                    student_number
                )
            )
        ),
    }


@router.post(
    "/students/{student_number}/payment-plan"
)
def finance_payment_plan_create(
    student_number: str,
    payload: FinancePaymentPlanCreate,
    current_staff: dict = Depends(
        require_manage_payment_plans
    ),
):
    try:
        plan = create_payment_plan(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            student_number=(
                student_number
            ),
            plan_months=(
                payload.plan_months
            ),
            deposit=payload.deposit,
            interest_rate=(
                payload.interest_rate
            ),
            start_date=(
                payload.start_date
            ),
        )

        return {
            "success": True,
            "message": (
                "Payment plan created."
            ),
            "payment_plan": plan,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/sponsors"
)
def finance_sponsors(
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    records = list_sponsors()

    return {
        "success": True,
        "count": len(
            records
        ),
        "sponsors": records,
    }


@router.post(
    "/sponsors"
)
def finance_sponsor_create(
    payload: FinanceSponsorCreate,
    current_staff: dict = Depends(
        require_manage_sponsors
    ),
):
    try:
        sponsor = create_sponsor(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            sponsor_name=(
                payload.sponsor_name
            ),
            sponsor_type=(
                payload.sponsor_type
            ),
            approval_number=(
                payload.approval_number
            ),
            approved_amount=(
                payload.approved_amount
            ),
        )

        return {
            "success": True,
            "message": (
                "Sponsor created."
            ),
            "sponsor": sponsor,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.post(
    "/students/{student_number}/sponsor"
)
def finance_sponsor_assign(
    student_number: str,
    payload: FinanceSponsorAssign,
    current_staff: dict = Depends(
        require_assign_sponsors
    ),
):
    try:
        return {
            "success": True,
            "message": (
                "Sponsor allocation created."
            ),
            "data": (
                assign_sponsor(
                    actor_staff_code=(
                        current_staff[
                            "staff_code"
                        ]
                    ),
                    student_number=(
                        student_number
                    ),
                    sponsor_id=(
                        payload.sponsor_id
                    ),
                    amount_covered=(
                        payload.amount_covered
                    ),
                    reference=(
                        payload.reference
                    ),
                )
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/students/{student_number}/statements"
)
def finance_student_statements(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    records = list_statements(
        student_number=(
            student_number
        )
    )

    return {
        "success": True,
        "count": len(
            records
        ),
        "statements": records,
    }


@router.post(
    "/students/{student_number}/statements"
)
def finance_statement_create(
    student_number: str,
    current_staff: dict = Depends(
        require_generate_statements
    ),
):
    try:
        statement = create_statement(
            actor_staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
            student_number=(
                student_number
            ),
        )

        pdf_path = None
        pdf_error = None

        try:
            path = generate_finance_document(
                kind="statement",
                student_number=(
                    student_number
                ),
            )

            pdf_path = str(
                path
            )

        except Exception as error:
            pdf_error = str(
                error
            )

        return {
            "success": True,
            "message": (
                "Finance statement created."
            ),
            "statement": statement,
            "pdf_path": pdf_path,
            "pdf_warning": pdf_error,
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/reports/{report_code}"
)
def finance_report(
    report_code: str,
    current_staff: dict = Depends(
        require_view_finance_reports
    ),
):
    try:
        return {
            "success": True,
            "report": (
                run_finance_report(
                    report_code=(
                        report_code
                    )
                )
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


def _finance_file_response(
    path: Path,
):
    return FileResponse(
        path=str(
            path
        ),
        media_type="application/pdf",
        filename=path.name,
    )


@router.get(
    "/documents/invoice/{invoice_number}"
)
def finance_invoice_document(
    invoice_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    try:
        return _finance_file_response(
            generate_finance_document(
                kind="invoice",
                identifier=(
                    invoice_number
                ),
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/documents/receipt/{receipt_number}"
)
def finance_receipt_document(
    receipt_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    try:
        return _finance_file_response(
            generate_finance_document(
                kind="receipt",
                identifier=(
                    receipt_number
                ),
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/documents/payment-plan/{payment_plan_id}"
)
def finance_payment_plan_document(
    payment_plan_id: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    try:
        return _finance_file_response(
            generate_finance_document(
                kind="payment_plan",
                identifier=(
                    payment_plan_id
                ),
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error


@router.get(
    "/documents/statement/{student_number}"
)
def finance_statement_document(
    student_number: str,
    current_staff: dict = Depends(
        require_view_finance
    ),
):
    try:
        return _finance_file_response(
            generate_finance_document(
                kind="statement",
                student_number=(
                    student_number
                ),
            )
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error
