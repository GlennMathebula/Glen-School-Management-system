from datetime import (
    datetime,
    timezone,
)
from pathlib import Path

from sqlalchemy import text

from app.database import engine
from app.services.email_service import (
    send_email,
)
from app.services.monthly_statement_service import (
    generate_monthly_statements_for_all,
)

# ============================================================
# HELPERS
# ============================================================

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


def get_month_name(
    month: int,
) -> str:

    if month not in MONTH_NAMES:

        raise ValueError(
            "Month must be between 1 and 12."
        )

    return MONTH_NAMES[
        month
    ]


# ============================================================
# GET DELIVERY RECORDS READY TO EMAIL
# ============================================================

def get_generated_statement_deliveries(
    year: int,
    month: int,
) -> list[dict]:

    query = text(
        """
        SELECT
            fsd.id,
            fsd.finance_account_id,
            fsd.statement_year,
            fsd.statement_month,
            fsd.period_start,
            fsd.period_end,
            fsd.opening_balance,
            fsd.total_charges,
            fsd.total_payments,
            fsd.closing_balance,
            fsd.pdf_path,
            fsd.recipient_email,
            fsd.delivery_status,

            r.student_number,

            a.first_name,
            a.middle_name,
            a.last_name

        FROM
            public.finance_statement_deliveries fsd

        JOIN public.finance_accounts fa
            ON fa.id
            = fsd.finance_account_id

        JOIN public.registrations r
            ON r.id
            = fa.registration_id

        JOIN public.applications a
            ON a.id
            = r.application_id

        WHERE
            fsd.statement_year
            = :statement_year

            AND fsd.statement_month
            = :statement_month

            AND fsd.had_activity
            = true

            AND fsd.delivery_status
            IN (
                'Generated',
                'Failed'
            )

        ORDER BY
            r.student_number
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "statement_year": (
                        year
                    ),
                    "statement_month": (
                        month
                    ),
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(
            row
        )
        for row in rows
    ]


# ============================================================
# STUDENT NAME
# ============================================================

def build_student_name(
    delivery: dict,
) -> str:

    return " ".join(
        value
        for value in [
            delivery.get(
                "first_name"
            ),
            delivery.get(
                "middle_name"
            ),
            delivery.get(
                "last_name"
            ),
        ]
        if value
    )


# ============================================================
# UPDATE DELIVERY STATUS
# ============================================================

def update_delivery_status(
    delivery_id: str,
    status: str,
    error_message: str | None = None,
) -> None:

    sent_at = None

    if status == "Sent":

        sent_at = datetime.now(
            timezone.utc
        )

    query = text(
        """
        UPDATE
            public.finance_statement_deliveries

        SET
            delivery_status
                = CAST(
                    :delivery_status
                    AS varchar(30)
                ),

            sent_at
                = :sent_at,

            error_message
                = CAST(
                    :error_message
                    AS text
                ),

            updated_at
                = now()

        WHERE
            id = CAST(
                :delivery_id
                AS uuid
            )
        """
    )

    with engine.begin() as connection:

        connection.execute(
            query,
            {
                "delivery_id": (
                    delivery_id
                ),

                "delivery_status": (
                    status
                ),

                "sent_at": (
                    sent_at
                ),

                "error_message": (
                    error_message
                ),
            },
        )


# ============================================================
# SEND ONE STATEMENT
# ============================================================

def send_statement_delivery(
    delivery: dict,
) -> dict:

    student_number = (
        delivery[
            "student_number"
        ]
    )

    recipient_email = (
        delivery.get(
            "recipient_email"
        )
    )

    if not recipient_email:

        error = (
            "Student does not have "
            "an email address."
        )

        update_delivery_status(
            str(
                delivery[
                    "id"
                ]
            ),
            "Failed",
            error,
        )

        return {
            "student_number": (
                student_number
            ),
            "status": "Failed",
            "error": error,
        }

    pdf_path = delivery.get(
        "pdf_path"
    )

    if not pdf_path:

        error = (
            "Statement PDF path "
            "is missing."
        )

        update_delivery_status(
            str(
                delivery[
                    "id"
                ]
            ),
            "Failed",
            error,
        )

        return {
            "student_number": (
                student_number
            ),
            "status": "Failed",
            "error": error,
        }

    pdf_path = Path(
        pdf_path
    )

    if not pdf_path.exists():

        error = (
            "Statement PDF file "
            "does not exist."
        )

        update_delivery_status(
            str(
                delivery[
                    "id"
                ]
            ),
            "Failed",
            error,
        )

        return {
            "student_number": (
                student_number
            ),
            "status": "Failed",
            "error": error,
        }

    month_name = (
        get_month_name(
            delivery[
                "statement_month"
            ]
        )
    )

    year = (
        delivery[
            "statement_year"
        ]
    )

    student_name = (
        build_student_name(
            delivery
        )
    )

    subject = (
        f"Glen Moniques Financial Statement "
        f"- {month_name} {year}"
    )

    text_body = (
        f"Dear {student_name},\n\n"
        f"Please find attached your Glen Moniques "
        f"financial statement for "
        f"{month_name} {year}.\n\n"
        f"Student Number: "
        f"{student_number}\n"
        f"Closing Balance: "
        f"R {float(delivery['closing_balance']):,.2f}\n\n"
        f"Regards,\n"
        f"Glen Moniques (Pty) Ltd"
    )

    html_body = f"""
    <html>
        <body
            style="
                font-family:
                    Arial,
                    Helvetica,
                    sans-serif;
                color: #1E2A35;
                background-color: #ffffff;
            "
        >
            <div
                style="
                    max-width: 650px;
                    margin: 0 auto;
                    border: 1px solid #D9E0E7;
                "
            >

                <div
                    style="
                        background-color: #0B2E59;
                        padding: 20px;
                        color: white;
                    "
                >

                    <h2
                        style="
                            margin: 0;
                        "
                    >
                        GLEN MONIQUES (PTY) LTD
                    </h2>

                    <p
                        style="
                            margin:
                                5px 0 0 0;
                            color: #F2B01E;
                        "
                    >
                        Monthly Financial Statement
                    </p>

                </div>

                <div
                    style="
                        padding: 24px;
                    "
                >

                    <p>
                        Dear {student_name},
                    </p>

                    <p>
                        Please find attached your
                        Glen Moniques financial
                        statement for
                        <strong>
                            {month_name} {year}
                        </strong>.
                    </p>

                    <table
                        style="
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                        "
                    >

                        <tr>

                            <td
                                style="
                                    padding: 10px;
                                    background: #F4F8FC;
                                    font-weight: bold;
                                "
                            >
                                Student Number
                            </td>

                            <td
                                style="
                                    padding: 10px;
                                "
                            >
                                {student_number}
                            </td>

                        </tr>

                        <tr>

                            <td
                                style="
                                    padding: 10px;
                                    background: #F4F8FC;
                                    font-weight: bold;
                                "
                            >
                                Statement Period
                            </td>

                            <td
                                style="
                                    padding: 10px;
                                "
                            >
                                {delivery['period_start']}
                                to
                                {delivery['period_end']}
                            </td>

                        </tr>

                        <tr>

                            <td
                                style="
                                    padding: 10px;
                                    background: #FFF3CD;
                                    font-weight: bold;
                                "
                            >
                                Closing Balance
                            </td>

                            <td
                                style="
                                    padding: 10px;
                                    font-weight: bold;
                                "
                            >
                                R
                                {float(delivery['closing_balance']):,.2f}
                            </td>

                        </tr>

                    </table>

                    <p>
                        The attached PDF contains
                        the detailed transactions
                        recorded on your account
                        during the statement period.
                    </p>

                    <p>
                        You may also access your
                        current financial information
                        through the Student Portal.
                    </p>

                    <p>
                        Regards,<br>
                        <strong>
                            Glen Moniques (Pty) Ltd
                        </strong>
                    </p>

                </div>

                <div
                    style="
                        border-top:
                            3px solid #F2B01E;
                        padding: 12px;
                        text-align: center;
                        font-size: 12px;
                        color: #0B2E59;
                    "
                >
                    015 880 2413
                    &nbsp; | &nbsp;
                    admin@glenmoniques.co.za
                    &nbsp; | &nbsp;
                    www.glenmoniques.co.za
                </div>

            </div>
        </body>
    </html>
    """

    try:

        send_email(
            recipient_email=(
                recipient_email
            ),
            subject=(
                subject
            ),
            html_body=(
                html_body
            ),
            text_body=(
                text_body
            ),
            attachment_path=(
                pdf_path
            ),
            attachment_name=(
                f"Financial-Statement-"
                f"{student_number}-"
                f"{year}-"
                f"{delivery['statement_month']:02d}"
                f".pdf"
            ),
        )

        update_delivery_status(
            str(
                delivery[
                    "id"
                ]
            ),
            "Sent",
            None,
        )

        return {
            "student_number": (
                student_number
            ),
            "recipient_email": (
                recipient_email
            ),
            "status": "Sent",
        }

    except Exception as error:

        update_delivery_status(
            str(
                delivery[
                    "id"
                ]
            ),
            "Failed",
            str(
                error
            ),
        )

        return {
            "student_number": (
                student_number
            ),
            "recipient_email": (
                recipient_email
            ),
            "status": "Failed",
            "error": str(
                error
            ),
        }


# ============================================================
# GENERATE + SEND MONTHLY STATEMENTS
# ============================================================

def process_monthly_statements(
    year: int,
    month: int,
) -> dict:

    generation_result = (
        generate_monthly_statements_for_all(
            year,
            month,
        )
    )

    deliveries = (
        get_generated_statement_deliveries(
            year,
            month,
        )
    )

    email_results = []

    sent = 0
    failed = 0

    for delivery in deliveries:

        result = (
            send_statement_delivery(
                delivery
            )
        )

        email_results.append(
            result
        )

        if (
            result[
                "status"
            ]
            == "Sent"
        ):

            sent += 1

        else:

            failed += 1

    return {
        "statement_year": (
            year
        ),

        "statement_month": (
            month
        ),

        "generation": (
            generation_result
        ),

        "emails_attempted": (
            len(
                deliveries
            )
        ),

        "emails_sent": (
            sent
        ),

        "emails_failed": (
            failed
        ),

        "email_results": (
            email_results
        ),
    }