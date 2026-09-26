from calendar import monthrange
from datetime import (
    date,
    datetime,
    timezone,
)
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.database import engine
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


def get_month_period(
    year: int,
    month: int,
) -> tuple[date, date]:

    if month < 1 or month > 12:

        raise ValueError(
            "Month must be between 1 and 12."
        )

    last_day = monthrange(
        year,
        month,
    )[1]

    return (
        date(
            year,
            month,
            1,
        ),
        date(
            year,
            month,
            last_day,
        ),
    )


def get_monthly_output_directory(
    year: int,
    month: int,
) -> Path:

    path = (
        Path(__file__)
        .resolve()
        .parents[1]
        / "generated_pdfs"
        / "finance"
        / "monthly"
        / str(year)
        / f"{month:02d}"
    )

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


# ============================================================
# ACCOUNT IDENTITY
# ============================================================

def get_finance_account_identity(
    finance_account_id: str,
) -> dict:

    query = text(
        """
        SELECT
            fa.id AS finance_account_id,
            fa.account_status,
            fa.funding_type,

            r.student_number,
            r.course_code,

            a.first_name,
            a.middle_name,
            a.last_name,
            a.email,

            c.course_name

        FROM public.finance_accounts fa

        JOIN public.registrations r
            ON r.id = fa.registration_id

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        WHERE
            fa.id = CAST(
                :finance_account_id
                AS uuid
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        raise ValueError(
            "Finance account not found."
        )

    result = dict(
        row
    )

    result[
        "student_name"
    ] = " ".join(
        value
        for value in [
            result.get(
                "first_name"
            ),
            result.get(
                "middle_name"
            ),
            result.get(
                "last_name"
            ),
        ]
        if value
    )

    return result


# ============================================================
# OPENING BALANCE
# ============================================================

def calculate_opening_balance(
    finance_account_id: str,
    period_start: date,
) -> Decimal:

    with engine.connect() as connection:

        charges = (
            connection.execute(
                text(
                    """
                    SELECT
                        COALESCE(
                            SUM(total_amount),
                            0
                        )

                    FROM public.finance_invoices

                    WHERE
                        finance_account_id
                        = CAST(
                            :finance_account_id
                            AS uuid
                        )

                        AND status <> 'Cancelled'

                        AND invoice_date
                            < :period_start
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                    "period_start": (
                        period_start
                    ),
                },
            )
            .scalar_one()
        )

        payments = (
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

                        AND payment_date
                            < :period_start
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                    "period_start": (
                        period_start
                    ),
                },
            )
            .scalar_one()
        )

    return (
        money(
            charges
        )
        - money(
            payments
        )
    )


# ============================================================
# MONTH TRANSACTIONS
# ============================================================

def get_month_transactions(
    finance_account_id: str,
    period_start: date,
    period_end: date,
) -> list[dict]:

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

                        AND invoice_date
                            BETWEEN
                                :period_start
                                AND :period_end

                    ORDER BY
                        invoice_date,
                        created_at
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                    "period_start": (
                        period_start
                    ),
                    "period_end": (
                        period_end
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

                        AND payment_date
                            BETWEEN
                                :period_start
                                AND :period_end

                    ORDER BY
                        payment_date,
                        created_at
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                    "period_start": (
                        period_start
                    ),
                    "period_end": (
                        period_end
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
                "credit": Decimal(
                    "0.00"
                ),
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
                "debit": Decimal(
                    "0.00"
                ),
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

    return transactions


# ============================================================
# BUILD MONTHLY STATEMENT DATA
# ============================================================

def build_monthly_statement_data(
    finance_account_id: str,
    year: int,
    month: int,
) -> dict:

    period_start, period_end = (
        get_month_period(
            year,
            month,
        )
    )

    student = (
        get_finance_account_identity(
            finance_account_id
        )
    )

    opening_balance = (
        calculate_opening_balance(
            finance_account_id,
            period_start,
        )
    )

    transactions = (
        get_month_transactions(
            finance_account_id,
            period_start,
            period_end,
        )
    )

    had_activity = bool(
        transactions
    )

    running_balance = (
        opening_balance
    )

    for transaction in transactions:

        running_balance += (
            transaction[
                "debit"
            ]
            - transaction[
                "credit"
            ]
        )

        transaction[
            "balance"
        ] = running_balance

    total_charges = sum(
        (
            transaction[
                "debit"
            ]
            for transaction
            in transactions
        ),
        Decimal(
            "0.00"
        ),
    )

    total_payments = sum(
        (
            transaction[
                "credit"
            ]
            for transaction
            in transactions
        ),
        Decimal(
            "0.00"
        ),
    )

    closing_balance = (
        opening_balance
        + total_charges
        - total_payments
    )

    return {
        "finance_account_id": (
            finance_account_id
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

        "recipient_email": (
            student.get(
                "email"
            )
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
            student.get(
                "funding_type"
            )
        ),

        "account_status": (
            student[
                "account_status"
            ]
        ),

        "statement_year": (
            year
        ),

        "statement_month": (
            month
        ),

        "period_start": (
            period_start
        ),

        "period_end": (
            period_end
        ),

        "opening_balance": (
            opening_balance
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

        "closing_balance": (
            closing_balance
        ),

        "outstanding": (
            max(
                closing_balance,
                Decimal(
                    "0.00"
                ),
            )
        ),

        "had_activity": (
            had_activity
        ),

        "generated_at": None,
    }


# ============================================================
# DELIVERY RECORD
# ============================================================

def save_delivery_record(
    data: dict,
    pdf_path: str | None,
    delivery_status: str,
    error_message: str | None = None,
) -> None:

    query = text(
        """
        INSERT INTO
            public.finance_statement_deliveries
        (
            finance_account_id,
            statement_year,
            statement_month,

            period_start,
            period_end,

            opening_balance,
            total_charges,
            total_payments,
            closing_balance,

            had_activity,

            pdf_path,
            recipient_email,

            delivery_status,

            generated_at,
            error_message,

            updated_at
        )

        VALUES
        (
            CAST(
                :finance_account_id
                AS uuid
            ),

            :statement_year,
            :statement_month,

            :period_start,
            :period_end,

            :opening_balance,
            :total_charges,
            :total_payments,
            :closing_balance,

            :had_activity,

            CAST(
                :pdf_path
                AS text
            ),

            CAST(
                :recipient_email
                AS text
            ),

            CAST(
                :delivery_status
                AS varchar(30)
            ),

            :generated_at,

            CAST(
                :error_message
                AS text
            ),

            now()
        )

        ON CONFLICT
        (
            finance_account_id,
            statement_year,
            statement_month
        )

        DO UPDATE SET

            period_start
                = EXCLUDED.period_start,

            period_end
                = EXCLUDED.period_end,

            opening_balance
                = EXCLUDED.opening_balance,

            total_charges
                = EXCLUDED.total_charges,

            total_payments
                = EXCLUDED.total_payments,

            closing_balance
                = EXCLUDED.closing_balance,

            had_activity
                = EXCLUDED.had_activity,

            pdf_path
                = EXCLUDED.pdf_path,

            recipient_email
                = EXCLUDED.recipient_email,

            delivery_status
                = EXCLUDED.delivery_status,

            generated_at
                = COALESCE(
                    EXCLUDED.generated_at,
                    public
                    .finance_statement_deliveries
                    .generated_at
                ),

            error_message
                = EXCLUDED.error_message,

            updated_at
                = now()
        """
    )

    parameters = {
        "finance_account_id": (
            data[
                "finance_account_id"
            ]
        ),

        "statement_year": (
            data[
                "statement_year"
            ]
        ),

        "statement_month": (
            data[
                "statement_month"
            ]
        ),

        "period_start": (
            data[
                "period_start"
            ]
        ),

        "period_end": (
            data[
                "period_end"
            ]
        ),

        "opening_balance": (
            data[
                "opening_balance"
            ]
        ),

        "total_charges": (
            data[
                "total_charges"
            ]
        ),

        "total_payments": (
            data[
                "total_payments"
            ]
        ),

        "closing_balance": (
            data[
                "closing_balance"
            ]
        ),

        "had_activity": (
            data[
                "had_activity"
            ]
        ),

        "pdf_path": (
            pdf_path
        ),

        "recipient_email": (
            data.get(
                "recipient_email"
            )
        ),

        "delivery_status": (
            delivery_status
        ),

        "generated_at": (
            data.get(
                "generated_at"
            )
        ),

        "error_message": (
            error_message
        ),
    }

    with engine.begin() as connection:

        connection.execute(
            query,
            parameters,
        )


# ============================================================
# GENERATE ONE MONTHLY STATEMENT
# ============================================================

def generate_monthly_statement(
    finance_account_id: str,
    year: int,
    month: int,
) -> dict:

    data = (
        build_monthly_statement_data(
            finance_account_id,
            year,
            month,
        )
    )

    # --------------------------------------------------------
    # NO ACTIVITY
    # --------------------------------------------------------

    if not data[
        "had_activity"
    ]:

        save_delivery_record(
            data=data,
            pdf_path=None,
            delivery_status="Skipped",
            error_message=None,
        )

        return {
            "student_number": (
                data[
                    "student_number"
                ]
            ),

            "status": (
                "Skipped"
            ),

            "reason": (
                "No financial activity "
                "during the statement month."
            ),

            "pdf_path": None,
        }

    # --------------------------------------------------------
    # GENERATE PDF
    # --------------------------------------------------------

    output_directory = (
        get_monthly_output_directory(
            year,
            month,
        )
    )

    output_path = (
        output_directory
        / (
            f"STATEMENT-"
            f"{data['student_number']}-"
            f"{year}-"
            f"{month:02d}.pdf"
        )
    )

    try:

        generate_statement_pdf(
            output_path,
            data,
        )

        data[
            "generated_at"
        ] = datetime.now(
            timezone.utc
        )

        save_delivery_record(
            data=data,
            pdf_path=str(
                output_path
            ),
            delivery_status="Generated",
            error_message=None,
        )

        return {
            "student_number": (
                data[
                    "student_number"
                ]
            ),

            "status": (
                "Generated"
            ),

            "period_start": (
                data[
                    "period_start"
                ]
            ),

            "period_end": (
                data[
                    "period_end"
                ]
            ),

            "opening_balance": (
                data[
                    "opening_balance"
                ]
            ),

            "total_charges": (
                data[
                    "total_charges"
                ]
            ),

            "total_payments": (
                data[
                    "total_payments"
                ]
            ),

            "closing_balance": (
                data[
                    "closing_balance"
                ]
            ),

            "pdf_path": str(
                output_path
            ),
        }

    except Exception as error:

        save_delivery_record(
            data=data,
            pdf_path=None,
            delivery_status="Failed",
            error_message=str(
                error
            ),
        )

        raise


# ============================================================
# GENERATE ALL ACTIVE ACCOUNTS
# ============================================================

def generate_monthly_statements_for_all(
    year: int,
    month: int,
) -> dict:

    with engine.connect() as connection:

        accounts = (
            connection.execute(
                text(
                    """
                    SELECT
                        id

                    FROM public.finance_accounts

                    WHERE
                        account_status
                        IN (
                            'Active',
                            'Paid'
                        )

                    ORDER BY
                        created_at
                    """
                )
            )
            .mappings()
            .all()
        )

    results = []

    generated = 0
    skipped = 0
    failed = 0

    for account in accounts:

        finance_account_id = str(
            account[
                "id"
            ]
        )

        try:

            result = (
                generate_monthly_statement(
                    finance_account_id,
                    year,
                    month,
                )
            )

            results.append(
                result
            )

            if (
                result[
                    "status"
                ]
                == "Generated"
            ):

                generated += 1

            elif (
                result[
                    "status"
                ]
                == "Skipped"
            ):

                skipped += 1

        except Exception as error:

            failed += 1

            results.append(
                {
                    "finance_account_id": (
                        finance_account_id
                    ),

                    "status": (
                        "Failed"
                    ),

                    "error": str(
                        error
                    ),
                }
            )

    return {
        "statement_year": (
            year
        ),

        "statement_month": (
            month
        ),

        "accounts_checked": (
            len(
                accounts
            )
        ),

        "generated": (
            generated
        ),

        "skipped": (
            skipped
        ),

        "failed": (
            failed
        ),

        "results": (
            results
        ),
    }