from pathlib import Path

from sqlalchemy import text

from app.database import engine

from app.services.finance_document_service import (
    generate_student_payment_plan,
    generate_student_receipt,
)


STUDENT_NUMBER = "20260007"


# ============================================================
# GET STUDENT FINANCE ACCOUNT
# ============================================================

with engine.begin() as connection:

    finance = (
        connection.execute(
            text(
                """
                SELECT
                    fa.id AS finance_account_id

                FROM public.finance_accounts fa

                JOIN public.registrations r
                    ON r.id = fa.registration_id

                WHERE
                    r.student_number = :student_number

                LIMIT 1
                """
            ),
            {
                "student_number": (
                    STUDENT_NUMBER
                ),
            },
        )
        .mappings()
        .first()
    )

    if not finance:

        raise RuntimeError(
            "Finance account not found."
        )

    finance_account_id = str(
        finance[
            "finance_account_id"
        ]
    )


    # ========================================================
    # FIND EXISTING RECEIPT
    # ========================================================

    receipt = (
        connection.execute(
            text(
                """
                SELECT
                    fr.receipt_number

                FROM public.finance_receipts fr

                JOIN public.finance_payments fp
                    ON fp.id = fr.payment_id

                WHERE
                    fp.finance_account_id
                    = CAST(
                        :finance_account_id
                        AS uuid
                    )

                ORDER BY
                    fr.created_at DESC

                LIMIT 1
                """
            ),
            {
                "finance_account_id": (
                    finance_account_id
                ),
            },
        )
        .mappings()
        .first()
    )

    if not receipt:

        raise RuntimeError(
            "No receipt found for this student."
        )

    receipt_number = (
        receipt[
            "receipt_number"
        ]
    )


    # ========================================================
    # FIND / CREATE DUMMY PAYMENT PLAN
    # ========================================================

    plan = (
        connection.execute(
            text(
                """
                SELECT
                    id

                FROM public.finance_payment_plans

                WHERE
                    finance_account_id
                    = CAST(
                        :finance_account_id
                        AS uuid
                    )

                    AND plan_name
                        = 'Outstanding Balance Plan'

                LIMIT 1
                """
            ),
            {
                "finance_account_id": (
                    finance_account_id
                ),
            },
        )
        .mappings()
        .first()
    )

    if not plan:

        plan = (
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.finance_payment_plans
                    (
                        finance_account_id,
                        plan_name,
                        start_date,
                        end_date,
                        total_plan_amount,
                        status,
                        notes,
                        created_by
                    )

                    VALUES
                    (
                        CAST(
                            :finance_account_id
                            AS uuid
                        ),

                        'Outstanding Balance Plan',

                        DATE '2026-10-01',
                        DATE '2026-12-31',

                        5500.00,

                        'Active',

                        'Dummy payment plan for finance testing.',

                        'ADMIN-TEST'
                    )

                    RETURNING id
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                },
            )
            .mappings()
            .one()
        )

        payment_plan_id = str(
            plan[
                "id"
            ]
        )

        installments = [
            (
                1,
                "2026-10-31",
                2000.00,
            ),
            (
                2,
                "2026-11-30",
                2000.00,
            ),
            (
                3,
                "2026-12-31",
                1500.00,
            ),
        ]

        for (
            installment_number,
            due_date,
            amount_due,
        ) in installments:

            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.finance_payment_plan_installments
                    (
                        payment_plan_id,
                        installment_number,
                        due_date,
                        amount_due,
                        status
                    )

                    VALUES
                    (
                        CAST(
                            :payment_plan_id
                            AS uuid
                        ),

                        :installment_number,

                        CAST(
                            :due_date
                            AS date
                        ),

                        :amount_due,

                        'Pending'
                    )
                    """
                ),
                {
                    "payment_plan_id": (
                        payment_plan_id
                    ),

                    "installment_number": (
                        installment_number
                    ),

                    "due_date": (
                        due_date
                    ),

                    "amount_due": (
                        amount_due
                    ),
                },
            )

    else:

        payment_plan_id = str(
            plan[
                "id"
            ]
        )


# ============================================================
# GENERATE DOCUMENTS
# ============================================================

receipt_path = (
    generate_student_receipt(
        STUDENT_NUMBER,
        receipt_number,
    )
)

payment_plan_path = (
    generate_student_payment_plan(
        STUDENT_NUMBER,
        payment_plan_id,
    )
)


print()
print(
    "Receipt:",
    receipt_path,
)

print(
    "Receipt Number:",
    receipt_number,
)

print()

print(
    "Payment Plan:",
    payment_plan_path,
)

print(
    "Payment Plan ID:",
    payment_plan_id,
)