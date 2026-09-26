from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.database import engine
from app.pdfs.finance.invoice_pdf import (
    generate_invoice_pdf,
)
from app.pdfs.finance.payment_plan_pdf import (
    generate_payment_plan_pdf,
)
from app.pdfs.finance.receipt_pdf import (
    generate_receipt_pdf,
)
from app.pdfs.finance.statement_pdf import (
    generate_statement_pdf,
)

# ============================================================
# HELPERS
# ============================================================

def money(value) -> Decimal:

    if value is None:
        return Decimal("0.00")

    return Decimal(
        str(value)
    ).quantize(
        Decimal("0.01")
    )


def get_output_directory() -> Path:

    path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "finance"
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


# ============================================================
# STUDENT CORE
# ============================================================

def get_student_finance_identity(
    student_number: str,
) -> dict:

    query = text(
        """
        SELECT
            r.student_number,
            r.course_code,
            r.funding_type,

            a.first_name,
            a.middle_name,
            a.last_name,

            c.course_name,

            fa.id AS finance_account_id,
            fa.account_status

        FROM public.registrations r

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        JOIN public.finance_accounts fa
            ON fa.registration_id = r.id

        WHERE
            r.student_number = :student_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Student finance account not found."
        )

    result = dict(row)

    result[
        "student_name"
    ] = " ".join(
        value
        for value in [
            result.get("first_name"),
            result.get("middle_name"),
            result.get("last_name"),
        ]
        if value
    )

    return result


# ============================================================
# INVOICE PDF
# ============================================================

def generate_student_invoice(
    student_number: str,
    invoice_number: str,
) -> Path:

    student = (
        get_student_finance_identity(
            student_number
        )
    )

    query = text(
        """
        SELECT
            fi.id,
            fi.invoice_number,
            fi.invoice_date,
            fi.due_date,
            fi.subtotal,
            fi.discount_amount,
            fi.total_amount,
            fi.status

        FROM public.finance_invoices fi

        WHERE
            fi.finance_account_id
            = CAST(
                :finance_account_id
                AS uuid
            )

            AND fi.invoice_number
            = :invoice_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        invoice = (
            connection.execute(
                query,
                {
                    "finance_account_id": str(
                        student[
                            "finance_account_id"
                        ]
                    ),
                    "invoice_number": (
                        invoice_number
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not invoice:

            raise ValueError(
                "Invoice not found."
            )

        items = (
            connection.execute(
                text(
                    """
                    SELECT
                        description,
                        quantity,
                        unit_price,
                        line_total

                    FROM public.finance_invoice_items

                    WHERE
                        invoice_id
                        = CAST(
                            :invoice_id
                            AS uuid
                        )

                    ORDER BY created_at
                    """
                ),
                {
                    "invoice_id": str(
                        invoice[
                            "id"
                        ]
                    ),
                },
            )
            .mappings()
            .all()
        )

        total_paid = (
            connection.execute(
                text(
                    """
                    SELECT
                        COALESCE(
                            SUM(amount),
                            0
                        )

                    FROM public.finance_payments

                    WHERE
                        finance_account_id
                        = CAST(
                            :finance_account_id
                            AS uuid
                        )

                        AND status = 'Completed'
                    """
                ),
                {
                    "finance_account_id": str(
                        student[
                            "finance_account_id"
                        ]
                    ),
                },
            )
            .scalar_one()
        )

    total_paid = money(
        total_paid
    )

    total_amount = money(
        invoice[
            "total_amount"
        ]
    )

    outstanding = max(
        total_amount
        - total_paid,
        Decimal("0.00"),
    )

    data = {
        "invoice_number": (
            invoice[
                "invoice_number"
            ]
        ),
        "invoice_date": (
            invoice[
                "invoice_date"
            ]
        ),
        "due_date": (
            invoice[
                "due_date"
            ]
        ),
        "status": (
            invoice[
                "status"
            ]
        ),
        "student_number": (
            student[
                "student_number"
            ]
        ),
        "student_name": (
            student[
                "student_name"
            ]
        ),
        "course_name": (
            student[
                "course_name"
            ]
        ),
        "course_code": (
            student[
                "course_code"
            ]
        ),
        "subtotal": (
            invoice[
                "subtotal"
            ]
        ),
        "discount_amount": (
            invoice[
                "discount_amount"
            ]
        ),
        "total_amount": (
            invoice[
                "total_amount"
            ]
        ),
        "amount_paid": (
            total_paid
        ),
        "outstanding": (
            outstanding
        ),
        "items": [
            dict(item)
            for item in items
        ],
    }

    output_path = (
        get_output_directory()
        / f"{invoice_number}.pdf"
    )

    return generate_invoice_pdf(
        output_path,
        data,
    )


# ============================================================
# RECEIPT PDF
# ============================================================

def generate_student_receipt(
    student_number: str,
    receipt_number: str,
) -> Path:

    student = (
        get_student_finance_identity(
            student_number
        )
    )

    query = text(
        """
        SELECT
            fr.receipt_number,
            fr.issued_at,

            fp.payment_reference,
            fp.payment_date,
            fp.amount,
            fp.payment_method,
            fp.external_reference

        FROM public.finance_receipts fr

        JOIN public.finance_payments fp
            ON fp.id = fr.payment_id

        WHERE
            fp.finance_account_id
            = CAST(
                :finance_account_id
                AS uuid
            )

            AND fr.receipt_number
            = :receipt_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "finance_account_id": str(
                        student[
                            "finance_account_id"
                        ]
                    ),
                    "receipt_number": (
                        receipt_number
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Receipt not found."
        )

    data = {
        "receipt_number": (
            row[
                "receipt_number"
            ]
        ),
        "student_number": (
            student[
                "student_number"
            ]
        ),
        "student_name": (
            student[
                "student_name"
            ]
        ),
        "payment_date": (
            row[
                "payment_date"
            ]
        ),
        "payment_reference": (
            row[
                "payment_reference"
            ]
        ),
        "payment_method": (
            row[
                "payment_method"
            ]
        ),
        "external_reference": (
            row[
                "external_reference"
            ]
        ),
        "amount": (
            row[
                "amount"
            ]
        ),
    }

    output_path = (
        get_output_directory()
        / f"{receipt_number}.pdf"
    )

    return generate_receipt_pdf(
        output_path,
        data,
    )


# ============================================================
# STATEMENT PDF
# ============================================================

def generate_student_statement(
    student_number: str,
) -> Path:

    student = (
        get_student_finance_identity(
            student_number
        )
    )

    finance_account_id = str(
        student[
            "finance_account_id"
        ]
    )

    transactions = []

    with engine.connect() as connection:

        invoices = (
            connection.execute(
                text(
                    """
                    SELECT
                        invoice_date,
                        invoice_number,
                        total_amount

                    FROM public.finance_invoices

                    WHERE
                        finance_account_id
                        = CAST(
                            :finance_account_id
                            AS uuid
                        )

                        AND status <> 'Cancelled'

                    ORDER BY
                        invoice_date,
                        created_at
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                },
            )
            .mappings()
            .all()
        )

        payments = (
            connection.execute(
                text(
                    """
                    SELECT
                        payment_date,
                        payment_reference,
                        amount

                    FROM public.finance_payments

                    WHERE
                        finance_account_id
                        = CAST(
                            :finance_account_id
                            AS uuid
                        )

                        AND status = 'Completed'

                    ORDER BY
                        payment_date,
                        created_at
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    for invoice in invoices:

        transactions.append(
            {
                "date": (
                    invoice[
                        "invoice_date"
                    ]
                ),
                "sort_order": 1,
                "reference": (
                    invoice[
                        "invoice_number"
                    ]
                ),
                "description": (
                    "Student fee invoice"
                ),
                "debit": money(
                    invoice[
                        "total_amount"
                    ]
                ),
                "credit": Decimal("0.00"),
            }
        )

    for payment in payments:

        transactions.append(
            {
                "date": (
                    payment[
                        "payment_date"
                    ]
                ),
                "sort_order": 2,
                "reference": (
                    payment[
                        "payment_reference"
                    ]
                ),
                "description": (
                    "Payment received"
                ),
                "debit": Decimal("0.00"),
                "credit": money(
                    payment[
                        "amount"
                    ]
                ),
            }
        )

    transactions.sort(
        key=lambda item: (
            item[
                "date"
            ],
            item[
                "sort_order"
            ],
        )
    )

    running_balance = Decimal("0.00")

    for item in transactions:

        running_balance += (
            item[
                "debit"
            ]
            - item[
                "credit"
            ]
        )

        item[
            "balance"
        ] = running_balance

    total_charges = sum(
        (
            item[
                "debit"
            ]
            for item in transactions
        ),
        Decimal("0.00"),
    )

    total_payments = sum(
        (
            item[
                "credit"
            ]
            for item in transactions
        ),
        Decimal("0.00"),
    )

    data = {
        "student_number": (
            student[
                "student_number"
            ]
        ),
        "student_name": (
            student[
                "student_name"
            ]
        ),
        "course_name": (
            student[
                "course_name"
            ]
        ),
        "course_code": (
            student[
                "course_code"
            ]
        ),
        "funding_type": (
            student[
                "funding_type"
            ]
        ),
        "account_status": (
            student[
                "account_status"
            ]
        ),
        "transactions": (
            transactions
        ),
        "total_charges": (
            total_charges
        ),
        "total_payments": (
            total_payments
        ),
        "outstanding": max(
            total_charges
            - total_payments,
            Decimal("0.00"),
        ),
    }

    output_path = (
        get_output_directory()
        / f"STATEMENT-{student_number}.pdf"
    )

    return generate_statement_pdf(
        output_path,
        data,
    )


# ============================================================
# PAYMENT PLAN PDF
# ============================================================

def generate_student_payment_plan(
    student_number: str,
    payment_plan_id: str,
) -> Path:

    student = (
        get_student_finance_identity(
            student_number
        )
    )

    with engine.connect() as connection:

        plan = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        plan_name,
                        start_date,
                        end_date,
                        total_plan_amount,
                        status

                    FROM public.finance_payment_plans

                    WHERE
                        id = CAST(
                            :payment_plan_id
                            AS uuid
                        )

                        AND finance_account_id
                            = CAST(
                                :finance_account_id
                                AS uuid
                            )

                    LIMIT 1
                    """
                ),
                {
                    "payment_plan_id": (
                        payment_plan_id
                    ),
                    "finance_account_id": str(
                        student[
                            "finance_account_id"
                        ]
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not plan:

            raise ValueError(
                "Payment plan not found."
            )

        installments = (
            connection.execute(
                text(
                    """
                    SELECT
                        installment_number,
                        due_date,
                        amount_due,
                        status

                    FROM
                        public.finance_payment_plan_installments

                    WHERE
                        payment_plan_id
                        = CAST(
                            :payment_plan_id
                            AS uuid
                        )

                    ORDER BY
                        installment_number
                    """
                ),
                {
                    "payment_plan_id": (
                        payment_plan_id
                    ),
                },
            )
            .mappings()
            .all()
        )

    data = {
        "student_number": (
            student[
                "student_number"
            ]
        ),
        "student_name": (
            student[
                "student_name"
            ]
        ),
        "course_name": (
            student[
                "course_name"
            ]
        ),
        "plan_name": (
            plan[
                "plan_name"
            ]
        ),
        "start_date": (
            plan[
                "start_date"
            ]
        ),
        "end_date": (
            plan[
                "end_date"
            ]
        ),
        "total_plan_amount": (
            plan[
                "total_plan_amount"
            ]
        ),
        "status": (
            plan[
                "status"
            ]
        ),
        "installments": [
            dict(item)
            for item in installments
        ],
    }

    output_path = (
        get_output_directory()
        / (
            f"PAYMENT-PLAN-"
            f"{student_number}-"
            f"{payment_plan_id}.pdf"
        )
    )

    return generate_payment_plan_pdf(
        output_path,
        data,
    )