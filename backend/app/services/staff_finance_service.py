from __future__ import annotations

import inspect
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from app.database import engine
from app.services.staff_audit_service import (
    create_staff_audit_log,
)


VALID_CHARGE_TYPES = {
    "registration",
    "tuition",
    "other",
}

VALID_PLAN_MONTHS = {
    1,
    3,
    6,
    12,
    24,
    36,
}

VALID_SPONSOR_TYPES = {
    "NSFAS",
    "SETA",
    "Company",
    "Employer",
    "Private",
}


def _money(
    value,
) -> Decimal:
    if value is None:
        return Decimal(
            "0.00"
        )

    return Decimal(
        str(
            value
        )
    ).quantize(
        Decimal(
            "0.01"
        )
    )


def _clean_student_number(
    value: str,
) -> str:
    value = str(
        value
        or ""
    ).strip()

    if not value:
        raise ValueError(
            "Student number is required."
        )

    return value


def _clean_optional(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    value = str(
        value
    ).strip()

    return value or None


def _write_audit(
    *,
    actor_staff_code: str,
    action_code: str,
    entity_type: str,
    entity_id: str,
    description: str,
    before_data: dict | None = None,
    after_data: dict | None = None,
    metadata: dict | None = None,
) -> None:
    try:
        create_staff_audit_log(
            actor_staff_code=(
                actor_staff_code
            ),
            action_code=action_code,
            module_code="FINANCE",
            entity_type=entity_type,
            entity_id=str(
                entity_id
            ),
            description=description,
            before_data=before_data,
            after_data=after_data,
            metadata=(
                metadata
                or {}
            ),
        )
    except Exception as error:
        print(
            "WARNING: Finance action "
            "succeeded but audit logging "
            f"failed: {error}"
        )


def _student_exists(
    connection,
    student_number: str,
) -> bool:
    return bool(
        connection.execute(
            text(
                """
                SELECT 1
                FROM public.applications
                WHERE student_number =
                    :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).first()
    )


def _ensure_account(
    connection,
    student_number: str,
) -> None:
    if not _student_exists(
        connection,
        student_number,
    ):
        raise ValueError(
            "Student not found."
        )

    connection.execute(
        text(
            """
            INSERT INTO
                public.student_accounts (
                    student_number
                )
            VALUES (
                :student_number
            )
            ON CONFLICT (
                student_number
            )
            DO NOTHING
            """
        ),
        {
            "student_number": (
                student_number
            )
        },
    )


def recalculate_student_account(
    *,
    student_number: str,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    with engine.begin() as connection:
        _ensure_account(
            connection,
            student_number,
        )

        payments_total = _money(
            connection.execute(
                text(
                    """
                    SELECT COALESCE(
                        SUM(amount),
                        0
                    )
                    FROM public.payments
                    WHERE student_number =
                        :student_number
                      AND status =
                        'Completed'
                    """
                ),
                {
                    "student_number": (
                        student_number
                    )
                },
            ).scalar_one()
        )

        account = connection.execute(
            text(
                """
                SELECT *
                FROM public.student_accounts
                WHERE student_number =
                    :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().first()

        registration_fee = _money(
            account[
                "registration_fee"
            ]
        )
        tuition_fee = _money(
            account[
                "tuition_fee"
            ]
        )
        other_charges = _money(
            account[
                "other_charges"
            ]
        )
        credits = _money(
            account[
                "credits"
            ]
        )
        sponsor_amount = _money(
            account[
                "sponsor_amount_covered"
            ]
        )

        balance = (
            registration_fee
            + tuition_fee
            + other_charges
            - credits
            - payments_total
            - sponsor_amount
        )

        if balance < 0:
            balance = Decimal(
                "0.00"
            )

        updated = connection.execute(
            text(
                """
                UPDATE public.student_accounts
                SET
                    payments_total =
                        :payments_total,
                    outstanding_balance =
                        :outstanding_balance,
                    updated_at = NOW()
                WHERE student_number =
                    :student_number
                RETURNING *
                """
            ),
            {
                "student_number": (
                    student_number
                ),
                "payments_total": (
                    payments_total
                ),
                "outstanding_balance": (
                    balance
                ),
            },
        ).mappings().first()

    return dict(
        updated
    )


def get_finance_dashboard() -> dict:
    with engine.connect() as connection:
        summary = connection.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_accounts,
                    COALESCE(
                        SUM(
                            registration_fee
                            + tuition_fee
                            + other_charges
                        ),
                        0
                    ) AS expected_income,
                    COALESCE(
                        SUM(payments_total),
                        0
                    ) AS collected_income,
                    COALESCE(
                        SUM(outstanding_balance),
                        0
                    ) AS outstanding_fees,
                    COUNT(*) FILTER (
                        WHERE
                            sponsor_amount_covered
                            > 0
                    ) AS sponsored_students
                FROM public.student_accounts
                """
            )
        ).mappings().first()

        monthly = connection.execute(
            text(
                """
                SELECT COALESCE(
                    SUM(amount),
                    0
                )
                FROM public.payments
                WHERE status = 'Completed'
                  AND payment_date >=
                      date_trunc(
                          'month',
                          CURRENT_DATE
                      )
                """
            )
        ).scalar_one()

        recent = connection.execute(
            text(
                """
                SELECT *
                FROM public.payments
                ORDER BY payment_date DESC
                LIMIT 10
                """
            )
        ).mappings().all()

    result = dict(
        summary
    )

    result[
        "monthly_collections"
    ] = monthly

    result[
        "recent_payments"
    ] = [
        dict(
            row
        )
        for row in recent
    ]

    return result


def search_finance_students(
    *,
    search: str | None,
    limit: int = 100,
) -> list[dict]:
    search = _clean_optional(
        search
    )

    where_sql = ""

    params = {
        "limit": int(
            limit
        )
    }

    if search:
        where_sql = """
            WHERE
                a.student_number
                    ILIKE :search
                OR a.first_name
                    ILIKE :search
                OR a.last_name
                    ILIKE :search
                OR COALESCE(
                    a.course_name,
                    ''
                ) ILIKE :search
        """

        params[
            "search"
        ] = (
            "%"
            + search
            + "%"
        )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT
                    a.student_number,
                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    a.course_name,
                    sa.registration_fee,
                    sa.tuition_fee,
                    sa.other_charges,
                    sa.credits,
                    sa.payments_total,
                    sa.outstanding_balance,
                    sa.sponsor_name,
                    sa.sponsor_amount_covered,
                    sa.status AS account_status,
                    sa.updated_at
                FROM public.applications a
                LEFT JOIN public.student_accounts sa
                    ON sa.student_number =
                       a.student_number
                {where_sql}
                ORDER BY
                    a.last_name,
                    a.first_name,
                    a.student_number
                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_student_finance(
    *,
    student_number: str,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    recalculate_student_account(
        student_number=(
            student_number
        )
    )

    with engine.connect() as connection:
        student = connection.execute(
            text(
                """
                SELECT
                    student_number,
                    first_name,
                    middle_name,
                    last_name,
                    course_name,
                    email,
                    cell_number
                FROM public.applications
                WHERE student_number =
                    :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().first()

        if not student:
            raise ValueError(
                "Student not found."
            )

        account = connection.execute(
            text(
                """
                SELECT *
                FROM public.student_accounts
                WHERE student_number =
                    :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().first()

        plan = connection.execute(
            text(
                """
                SELECT *
                FROM public.payment_plans
                WHERE student_number =
                    :student_number
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().first()

        payments = connection.execute(
            text(
                """
                SELECT *
                FROM public.payments
                WHERE student_number =
                    :student_number
                ORDER BY payment_date DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

        invoices = connection.execute(
            text(
                """
                SELECT *
                FROM public.invoices
                WHERE student_number =
                    :student_number
                ORDER BY date_issued DESC,
                         created_at DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

        receipts = connection.execute(
            text(
                """
                SELECT *
                FROM public.receipts
                WHERE student_number =
                    :student_number
                ORDER BY payment_date DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

        allocations = connection.execute(
            text(
                """
                SELECT
                    ssa.*,
                    s.sponsor_name,
                    s.sponsor_type
                FROM
                    public.student_sponsor_allocations
                    ssa
                JOIN public.sponsors s
                    ON s.sponsor_id =
                       ssa.sponsor_id
                WHERE ssa.student_number =
                    :student_number
                ORDER BY ssa.created_at DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

        statements = connection.execute(
            text(
                """
                SELECT *
                FROM public.statements
                WHERE student_number =
                    :student_number
                ORDER BY generated_at DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

    return {
        "student": dict(
            student
        ),
        "account": (
            dict(
                account
            )
            if account
            else None
        ),
        "payment_plan": (
            dict(
                plan
            )
            if plan
            else None
        ),
        "payments": [
            dict(
                row
            )
            for row in payments
        ],
        "invoices": [
            dict(
                row
            )
            for row in invoices
        ],
        "receipts": [
            dict(
                row
            )
            for row in receipts
        ],
        "sponsor_allocations": [
            dict(
                row
            )
            for row in allocations
        ],
        "statements": [
            dict(
                row
            )
            for row in statements
        ],
    }


def create_charge(
    *,
    actor_staff_code: str,
    student_number: str,
    charge_type: str,
    amount: Decimal,
    description: str,
    due_date=None,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )
    charge_type = str(
        charge_type
        or ""
    ).strip().lower()

    if charge_type not in (
        VALID_CHARGE_TYPES
    ):
        raise ValueError(
            "Charge type must be "
            "registration, tuition or other."
        )

    amount = _money(
        amount
    )

    if amount <= 0:
        raise ValueError(
            "Charge amount must be "
            "greater than zero."
        )

    description = str(
        description
        or ""
    ).strip()

    if not description:
        raise ValueError(
            "Charge description is required."
        )

    invoice_number = (
        "INV-"
        + date.today().strftime(
            "%Y%m%d"
        )
        + "-"
        + uuid4().hex[
            :8
        ].upper()
    )

    column = {
        "registration": (
            "registration_fee"
        ),
        "tuition": "tuition_fee",
        "other": "other_charges",
    }[
        charge_type
    ]

    with engine.begin() as connection:
        _ensure_account(
            connection,
            student_number,
        )

        connection.execute(
            text(
                f"""
                UPDATE public.student_accounts
                SET
                    {column} =
                        {column}
                        + :amount,
                    updated_at = NOW()
                WHERE student_number =
                    :student_number
                """
            ),
            {
                "student_number": (
                    student_number
                ),
                "amount": amount,
            },
        )

        row = connection.execute(
            text(
                """
                INSERT INTO public.invoices (
                    invoice_number,
                    student_number,
                    charge_type,
                    description,
                    amount,
                    date_issued,
                    due_date,
                    status,
                    created_by
                )
                VALUES (
                    :invoice_number,
                    :student_number,
                    :charge_type,
                    :description,
                    :amount,
                    CURRENT_DATE,
                    :due_date,
                    'Unpaid',
                    :created_by
                )
                RETURNING *
                """
            ),
            {
                "invoice_number": (
                    invoice_number
                ),
                "student_number": (
                    student_number
                ),
                "charge_type": (
                    charge_type
                ),
                "description": (
                    description
                ),
                "amount": amount,
                "due_date": due_date,
                "created_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

    recalculate_student_account(
        student_number=(
            student_number
        )
    )

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="FINANCE_CHARGE_ADDED",
        entity_type="INVOICE",
        entity_id=(
            invoice_number
        ),
        description=(
            "Finance charge and invoice "
            "created."
        ),
        after_data=record,
        metadata={
            "student_number": (
                student_number
            ),
            "charge_type": (
                charge_type
            ),
        },
    )

    return record


def list_student_payments(
    *,
    student_number: str,
) -> list[dict]:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.payments
                WHERE student_number =
                    :student_number
                ORDER BY payment_date DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def record_payment(
    *,
    actor_staff_code: str,
    student_number: str,
    amount: Decimal,
    method: str,
    reference: str | None,
    invoice_number: str | None,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )
    amount = _money(
        amount
    )

    if amount <= 0:
        raise ValueError(
            "Payment amount must be "
            "greater than zero."
        )

    method = str(
        method
        or ""
    ).strip()

    if not method:
        raise ValueError(
            "Payment method is required."
        )

    reference = _clean_optional(
        reference
    )
    invoice_number = (
        _clean_optional(
            invoice_number
        )
    )

    payment_id = (
        "PAY-"
        + date.today().strftime(
            "%Y%m%d"
        )
        + "-"
        + uuid4().hex[
            :10
        ].upper()
    )

    receipt_number = (
        "RCT-"
        + date.today().strftime(
            "%Y%m%d"
        )
        + "-"
        + uuid4().hex[
            :10
        ].upper()
    )

    with engine.begin() as connection:
        _ensure_account(
            connection,
            student_number,
        )

        if invoice_number:
            invoice = connection.execute(
                text(
                    """
                    SELECT *
                    FROM public.invoices
                    WHERE invoice_number =
                        :invoice_number
                      AND student_number =
                        :student_number
                    LIMIT 1
                    """
                ),
                {
                    "invoice_number": (
                        invoice_number
                    ),
                    "student_number": (
                        student_number
                    ),
                },
            ).mappings().first()

            if not invoice:
                raise ValueError(
                    "Invoice not found for "
                    "this student."
                )

        payment = connection.execute(
            text(
                """
                INSERT INTO public.payments (
                    payment_id,
                    student_number,
                    invoice_number,
                    amount,
                    method,
                    payment_date,
                    status,
                    reference,
                    recorded_by
                )
                VALUES (
                    :payment_id,
                    :student_number,
                    :invoice_number,
                    :amount,
                    :method,
                    NOW(),
                    'Completed',
                    :reference,
                    :recorded_by
                )
                RETURNING *
                """
            ),
            {
                "payment_id": payment_id,
                "student_number": (
                    student_number
                ),
                "invoice_number": (
                    invoice_number
                ),
                "amount": amount,
                "method": method,
                "reference": reference,
                "recorded_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

        receipt = connection.execute(
            text(
                """
                INSERT INTO public.receipts (
                    receipt_number,
                    student_number,
                    payment_id,
                    amount,
                    payment_date,
                    created_by
                )
                VALUES (
                    :receipt_number,
                    :student_number,
                    :payment_id,
                    :amount,
                    NOW(),
                    :created_by
                )
                RETURNING *
                """
            ),
            {
                "receipt_number": (
                    receipt_number
                ),
                "student_number": (
                    student_number
                ),
                "payment_id": payment_id,
                "amount": amount,
                "created_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

        if invoice_number:
            paid_total = _money(
                connection.execute(
                    text(
                        """
                        SELECT COALESCE(
                            SUM(amount),
                            0
                        )
                        FROM public.payments
                        WHERE invoice_number =
                            :invoice_number
                          AND status =
                            'Completed'
                        """
                    ),
                    {
                        "invoice_number": (
                            invoice_number
                        )
                    },
                ).scalar_one()
            )

            invoice_amount = _money(
                invoice[
                    "amount"
                ]
            )

            invoice_status = (
                "Paid"
                if paid_total
                >= invoice_amount
                else "Partially Paid"
            )

            connection.execute(
                text(
                    """
                    UPDATE public.invoices
                    SET
                        status =
                            :invoice_status,
                        updated_at = NOW()
                    WHERE invoice_number =
                        :invoice_number
                    """
                ),
                {
                    "invoice_number": (
                        invoice_number
                    ),
                    "invoice_status": (
                        invoice_status
                    ),
                },
            )

    account = (
        recalculate_student_account(
            student_number=(
                student_number
            )
        )
    )

    result = {
        "payment": dict(
            payment
        ),
        "receipt": dict(
            receipt
        ),
        "account": account,
    }

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="PAYMENT_RECEIVED",
        entity_type="PAYMENT",
        entity_id=payment_id,
        description=(
            "Student payment recorded."
        ),
        after_data=dict(
            payment
        ),
        metadata={
            "student_number": (
                student_number
            ),
            "receipt_number": (
                receipt_number
            ),
        },
    )

    return result


def reverse_payment(
    *,
    actor_staff_code: str,
    payment_id: str,
    reason: str,
) -> dict:
    payment_id = str(
        payment_id
        or ""
    ).strip()

    reason = str(
        reason
        or ""
    ).strip()

    if not payment_id:
        raise ValueError(
            "Payment ID is required."
        )

    if not reason:
        raise ValueError(
            "Reversal reason is required."
        )

    with engine.begin() as connection:
        before = connection.execute(
            text(
                """
                SELECT *
                FROM public.payments
                WHERE payment_id =
                    :payment_id
                LIMIT 1
                """
            ),
            {
                "payment_id": payment_id
            },
        ).mappings().first()

        if not before:
            raise ValueError(
                "Payment not found."
            )

        if str(
            before[
                "status"
            ]
        ) != "Completed":
            raise ValueError(
                "Only completed payments "
                "can be reversed."
            )

        row = connection.execute(
            text(
                """
                UPDATE public.payments
                SET
                    status = 'Reversed',
                    reversed_by =
                        :reversed_by,
                    reversed_at = NOW(),
                    reversal_reason =
                        :reversal_reason,
                    updated_at = NOW()
                WHERE payment_id =
                    :payment_id
                RETURNING *
                """
            ),
            {
                "payment_id": payment_id,
                "reversed_by": (
                    actor_staff_code
                ),
                "reversal_reason": (
                    reason
                ),
            },
        ).mappings().first()

        invoice_number = before[
            "invoice_number"
        ]

        if invoice_number:
            paid_total = _money(
                connection.execute(
                    text(
                        """
                        SELECT COALESCE(
                            SUM(amount),
                            0
                        )
                        FROM public.payments
                        WHERE invoice_number =
                            :invoice_number
                          AND status =
                            'Completed'
                        """
                    ),
                    {
                        "invoice_number": (
                            invoice_number
                        )
                    },
                ).scalar_one()
            )

            invoice = connection.execute(
                text(
                    """
                    SELECT amount
                    FROM public.invoices
                    WHERE invoice_number =
                        :invoice_number
                    LIMIT 1
                    """
                ),
                {
                    "invoice_number": (
                        invoice_number
                    )
                },
            ).mappings().first()

            if invoice:
                invoice_amount = _money(
                    invoice[
                        "amount"
                    ]
                )

                if paid_total <= 0:
                    status = "Unpaid"
                elif paid_total >= invoice_amount:
                    status = "Paid"
                else:
                    status = (
                        "Partially Paid"
                    )

                connection.execute(
                    text(
                        """
                        UPDATE public.invoices
                        SET
                            status = :status,
                            updated_at = NOW()
                        WHERE invoice_number =
                            :invoice_number
                        """
                    ),
                    {
                        "status": status,
                        "invoice_number": (
                            invoice_number
                        ),
                    },
                )

    account = (
        recalculate_student_account(
            student_number=(
                before[
                    "student_number"
                ]
            )
        )
    )

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="PAYMENT_REVERSED",
        entity_type="PAYMENT",
        entity_id=payment_id,
        description=(
            "CFO reversed a student "
            "payment."
        ),
        before_data=dict(
            before
        ),
        after_data=record,
        metadata={
            "reason": reason
        },
    )

    return {
        "payment": record,
        "account": account,
    }


def apply_credit(
    *,
    actor_staff_code: str,
    student_number: str,
    amount: Decimal,
    reason: str,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )
    amount = _money(
        amount
    )

    if amount <= 0:
        raise ValueError(
            "Credit amount must be "
            "greater than zero."
        )

    reason = str(
        reason
        or ""
    ).strip()

    if not reason:
        raise ValueError(
            "Credit reason is required."
        )

    with engine.begin() as connection:
        _ensure_account(
            connection,
            student_number,
        )

        before = connection.execute(
            text(
                """
                SELECT *
                FROM public.student_accounts
                WHERE student_number =
                    :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().first()

        connection.execute(
            text(
                """
                UPDATE public.student_accounts
                SET
                    credits =
                        credits + :amount,
                    updated_at = NOW()
                WHERE student_number =
                    :student_number
                """
            ),
            {
                "student_number": (
                    student_number
                ),
                "amount": amount,
            },
        )

    account = (
        recalculate_student_account(
            student_number=(
                student_number
            )
        )
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="FINANCE_CREDIT_APPLIED",
        entity_type="STUDENT_ACCOUNT",
        entity_id=student_number,
        description=(
            "CFO applied a finance "
            "account credit."
        ),
        before_data=(
            dict(
                before
            )
            if before
            else None
        ),
        after_data=account,
        metadata={
            "credit_amount": str(
                amount
            ),
            "reason": reason,
        },
    )

    return account


def list_student_invoices(
    *,
    student_number: str,
) -> list[dict]:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.invoices
                WHERE student_number =
                    :student_number
                ORDER BY date_issued DESC,
                         created_at DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def list_student_receipts(
    *,
    student_number: str,
) -> list[dict]:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.receipts
                WHERE student_number =
                    :student_number
                ORDER BY payment_date DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def get_latest_payment_plan(
    *,
    student_number: str,
) -> dict | None:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT *
                FROM public.payment_plans
                WHERE student_number =
                    :student_number
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().first()

    return (
        dict(
            row
        )
        if row
        else None
    )


def create_payment_plan(
    *,
    actor_staff_code: str,
    student_number: str,
    plan_months: int,
    deposit: Decimal,
    interest_rate: Decimal,
    start_date=None,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    if plan_months not in (
        VALID_PLAN_MONTHS
    ):
        raise ValueError(
            "Plan months must be one of: "
            "1, 3, 6, 12, 24 or 36."
        )

    account = (
        recalculate_student_account(
            student_number=(
                student_number
            )
        )
    )

    outstanding = _money(
        account[
            "outstanding_balance"
        ]
    )

    deposit = _money(
        deposit
    )

    interest_rate = _money(
        interest_rate
    )

    if deposit > outstanding:
        raise ValueError(
            "Deposit cannot exceed the "
            "outstanding balance."
        )

    remaining_principal = (
        outstanding
        - deposit
    )

    total_with_interest = (
        remaining_principal
        * (
            Decimal(
                "1.00"
            )
            + (
                interest_rate
                / Decimal(
                    "100.00"
                )
            )
        )
    )

    monthly_instalment = (
        total_with_interest
        / Decimal(
            str(
                plan_months
            )
        )
    ).quantize(
        Decimal(
            "0.01"
        )
    )

    plan_start = (
        start_date
        or date.today()
    )

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE public.payment_plans
                SET
                    status = 'Replaced',
                    updated_at = NOW()
                WHERE student_number =
                    :student_number
                  AND status = 'Active'
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        )

        row = connection.execute(
            text(
                """
                INSERT INTO
                    public.payment_plans (
                        student_number,
                        plan_months,
                        total_fee,
                        deposit,
                        monthly_instalment,
                        start_date,
                        next_due_date,
                        remaining_months,
                        interest_rate,
                        status,
                        created_by
                    )
                VALUES (
                    :student_number,
                    :plan_months,
                    :total_fee,
                    :deposit,
                    :monthly_instalment,
                    :start_date,
                    :next_due_date,
                    :remaining_months,
                    :interest_rate,
                    'Active',
                    :created_by
                )
                RETURNING *
                """
            ),
            {
                "student_number": (
                    student_number
                ),
                "plan_months": (
                    plan_months
                ),
                "total_fee": (
                    outstanding
                ),
                "deposit": deposit,
                "monthly_instalment": (
                    monthly_instalment
                ),
                "start_date": (
                    plan_start
                ),
                "next_due_date": (
                    plan_start
                ),
                "remaining_months": (
                    plan_months
                ),
                "interest_rate": (
                    interest_rate
                ),
                "created_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="PAYMENT_PLAN_CREATED",
        entity_type="PAYMENT_PLAN",
        entity_id=record[
            "id"
        ],
        description=(
            "Student payment plan created."
        ),
        after_data=record,
        metadata={
            "student_number": (
                student_number
            )
        },
    )

    return record


def list_sponsors() -> list[dict]:
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.sponsors
                ORDER BY
                    sponsor_name,
                    created_at DESC
                """
            )
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def create_sponsor(
    *,
    actor_staff_code: str,
    sponsor_name: str,
    sponsor_type: str,
    approval_number: str | None,
    approved_amount: Decimal,
) -> dict:
    sponsor_name = str(
        sponsor_name
        or ""
    ).strip()

    sponsor_type = str(
        sponsor_type
        or ""
    ).strip()

    if sponsor_type not in (
        VALID_SPONSOR_TYPES
    ):
        raise ValueError(
            "Sponsor type must be NSFAS, "
            "SETA, Company, Employer or "
            "Private."
        )

    approved_amount = _money(
        approved_amount
    )

    if approved_amount <= 0:
        raise ValueError(
            "Approved amount must be "
            "greater than zero."
        )

    sponsor_id = (
        "SPN-"
        + uuid4().hex[
            :10
        ].upper()
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.sponsors (
                    sponsor_id,
                    sponsor_name,
                    sponsor_type,
                    approval_number,
                    approved_amount,
                    remaining_amount,
                    status,
                    created_by
                )
                VALUES (
                    :sponsor_id,
                    :sponsor_name,
                    :sponsor_type,
                    :approval_number,
                    :approved_amount,
                    :approved_amount,
                    'Active',
                    :created_by
                )
                RETURNING *
                """
            ),
            {
                "sponsor_id": sponsor_id,
                "sponsor_name": (
                    sponsor_name
                ),
                "sponsor_type": (
                    sponsor_type
                ),
                "approval_number": (
                    _clean_optional(
                        approval_number
                    )
                ),
                "approved_amount": (
                    approved_amount
                ),
                "created_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="SPONSOR_CREATED",
        entity_type="SPONSOR",
        entity_id=sponsor_id,
        description=(
            "Finance sponsor created."
        ),
        after_data=record,
    )

    return record


def assign_sponsor(
    *,
    actor_staff_code: str,
    student_number: str,
    sponsor_id: str,
    amount_covered: Decimal,
    reference: str | None,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    sponsor_id = str(
        sponsor_id
        or ""
    ).strip()

    amount_covered = _money(
        amount_covered
    )

    if amount_covered <= 0:
        raise ValueError(
            "Sponsor allocation must be "
            "greater than zero."
        )

    with engine.begin() as connection:
        _ensure_account(
            connection,
            student_number,
        )

        sponsor = connection.execute(
            text(
                """
                SELECT *
                FROM public.sponsors
                WHERE sponsor_id =
                    :sponsor_id
                  AND status = 'Active'
                LIMIT 1
                FOR UPDATE
                """
            ),
            {
                "sponsor_id": sponsor_id
            },
        ).mappings().first()

        if not sponsor:
            raise ValueError(
                "Active sponsor not found."
            )

        remaining = _money(
            sponsor[
                "remaining_amount"
            ]
        )

        if amount_covered > remaining:
            raise ValueError(
                "Allocation exceeds the "
                "sponsor remaining balance."
            )

        allocation = connection.execute(
            text(
                """
                INSERT INTO
                    public.student_sponsor_allocations (
                        student_number,
                        sponsor_id,
                        amount_covered,
                        reference,
                        allocated_by
                    )
                VALUES (
                    :student_number,
                    :sponsor_id,
                    :amount_covered,
                    :reference,
                    :allocated_by
                )
                RETURNING *
                """
            ),
            {
                "student_number": (
                    student_number
                ),
                "sponsor_id": sponsor_id,
                "amount_covered": (
                    amount_covered
                ),
                "reference": (
                    _clean_optional(
                        reference
                    )
                ),
                "allocated_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

        connection.execute(
            text(
                """
                UPDATE public.sponsors
                SET
                    remaining_amount =
                        remaining_amount
                        - :amount_covered,
                    updated_at = NOW()
                WHERE sponsor_id =
                    :sponsor_id
                """
            ),
            {
                "sponsor_id": sponsor_id,
                "amount_covered": (
                    amount_covered
                ),
            },
        )

        total_sponsored = _money(
            connection.execute(
                text(
                    """
                    SELECT COALESCE(
                        SUM(amount_covered),
                        0
                    )
                    FROM
                        public.student_sponsor_allocations
                    WHERE student_number =
                        :student_number
                    """
                ),
                {
                    "student_number": (
                        student_number
                    )
                },
            ).scalar_one()
        )

        connection.execute(
            text(
                """
                UPDATE public.student_accounts
                SET
                    sponsor_name =
                        :sponsor_name,
                    sponsor_amount_covered =
                        :total_sponsored,
                    updated_at = NOW()
                WHERE student_number =
                    :student_number
                """
            ),
            {
                "student_number": (
                    student_number
                ),
                "sponsor_name": sponsor[
                    "sponsor_name"
                ],
                "total_sponsored": (
                    total_sponsored
                ),
            },
        )

    account = (
        recalculate_student_account(
            student_number=(
                student_number
            )
        )
    )

    record = dict(
        allocation
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="SPONSOR_ASSIGNED",
        entity_type="SPONSOR_ALLOCATION",
        entity_id=record[
            "id"
        ],
        description=(
            "Sponsor funding allocated "
            "to student."
        ),
        after_data=record,
        metadata={
            "student_number": (
                student_number
            ),
            "sponsor_id": sponsor_id,
        },
    )

    return {
        "allocation": record,
        "account": account,
    }


def create_statement(
    *,
    actor_staff_code: str,
    student_number: str,
) -> dict:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    account = (
        recalculate_student_account(
            student_number=(
                student_number
            )
        )
    )

    period = (
        date.today().strftime(
            "%Y-%m"
        )
    )

    statement_number = (
        "STM-"
        + date.today().strftime(
            "%Y%m"
        )
        + "-"
        + uuid4().hex[
            :8
        ].upper()
    )

    charges = (
        _money(
            account[
                "registration_fee"
            ]
        )
        + _money(
            account[
                "tuition_fee"
            ]
        )
        + _money(
            account[
                "other_charges"
            ]
        )
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.statements (
                    statement_number,
                    student_number,
                    period,
                    opening_balance,
                    charges,
                    payments,
                    credits,
                    sponsor_covered,
                    closing_balance,
                    amount_due,
                    generated_by
                )
                VALUES (
                    :statement_number,
                    :student_number,
                    :period,
                    :opening_balance,
                    :charges,
                    :payments,
                    :credits,
                    :sponsor_covered,
                    :closing_balance,
                    :amount_due,
                    :generated_by
                )
                RETURNING *
                """
            ),
            {
                "statement_number": (
                    statement_number
                ),
                "student_number": (
                    student_number
                ),
                "period": period,
                "opening_balance": (
                    account[
                        "outstanding_balance"
                    ]
                ),
                "charges": charges,
                "payments": account[
                    "payments_total"
                ],
                "credits": account[
                    "credits"
                ],
                "sponsor_covered": (
                    account[
                        "sponsor_amount_covered"
                    ]
                ),
                "closing_balance": (
                    account[
                        "outstanding_balance"
                    ]
                ),
                "amount_due": (
                    account[
                        "outstanding_balance"
                    ]
                ),
                "generated_by": (
                    actor_staff_code
                ),
            },
        ).mappings().first()

    record = dict(
        row
    )

    _write_audit(
        actor_staff_code=(
            actor_staff_code
        ),
        action_code="FINANCE_STATEMENT_CREATED",
        entity_type="STATEMENT",
        entity_id=(
            statement_number
        ),
        description=(
            "Student finance statement "
            "record created."
        ),
        after_data=record,
    )

    return record


def list_statements(
    *,
    student_number: str,
) -> list[dict]:
    student_number = (
        _clean_student_number(
            student_number
        )
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.statements
                WHERE student_number =
                    :student_number
                ORDER BY generated_at DESC
                """
            ),
            {
                "student_number": (
                    student_number
                )
            },
        ).mappings().all()

    return [
        dict(
            row
        )
        for row in rows
    ]


def run_finance_report(
    *,
    report_code: str,
) -> dict:
    report_code = str(
        report_code
        or ""
    ).strip().lower()

    with engine.connect() as connection:
        if report_code == (
            "monthly-income"
        ):
            rows = connection.execute(
                text(
                    """
                    SELECT
                        TO_CHAR(
                            date_trunc(
                                'month',
                                payment_date
                            ),
                            'YYYY-MM'
                        ) AS period,
                        SUM(amount) AS amount
                    FROM public.payments
                    WHERE status =
                        'Completed'
                    GROUP BY 1
                    ORDER BY 1 DESC
                    """
                )
            ).mappings().all()

            title = (
                "Monthly Income Report"
            )

        elif report_code == (
            "outstanding-fees"
        ):
            rows = connection.execute(
                text(
                    """
                    SELECT
                        sa.student_number,
                        a.first_name,
                        a.last_name,
                        a.course_name,
                        sa.outstanding_balance
                    FROM public.student_accounts sa
                    LEFT JOIN public.applications a
                        ON a.student_number =
                           sa.student_number
                    WHERE
                        sa.outstanding_balance
                        > 0
                    ORDER BY
                        sa.outstanding_balance DESC
                    """
                )
            ).mappings().all()

            title = (
                "Outstanding Fees Report"
            )

        elif report_code == (
            "collection-rate"
        ):
            row = connection.execute(
                text(
                    """
                    SELECT
                        COALESCE(
                            SUM(
                                registration_fee
                                + tuition_fee
                                + other_charges
                            ),
                            0
                        ) AS billed,
                        COALESCE(
                            SUM(payments_total),
                            0
                        ) AS collected
                    FROM public.student_accounts
                    """
                )
            ).mappings().first()

            billed = _money(
                row[
                    "billed"
                ]
            )
            collected = _money(
                row[
                    "collected"
                ]
            )

            rate = (
                (
                    collected
                    / billed
                    * Decimal(
                        "100.00"
                    )
                ).quantize(
                    Decimal(
                        "0.01"
                    )
                )
                if billed > 0
                else Decimal(
                    "0.00"
                )
            )

            rows = [
                {
                    "billed": billed,
                    "collected": (
                        collected
                    ),
                    "collection_rate_percent": (
                        rate
                    ),
                }
            ]

            title = (
                "Collection Rate Report"
            )

        elif report_code == (
            "sponsors"
        ):
            rows = connection.execute(
                text(
                    """
                    SELECT
                        sponsor_id,
                        sponsor_name,
                        sponsor_type,
                        approved_amount,
                        remaining_amount,
                        (
                            approved_amount
                            - remaining_amount
                        ) AS allocated_amount,
                        status
                    FROM public.sponsors
                    ORDER BY sponsor_name
                    """
                )
            ).mappings().all()

            title = (
                "Sponsor Funding Report"
            )

        elif report_code == (
            "student-balances"
        ):
            rows = connection.execute(
                text(
                    """
                    SELECT
                        sa.student_number,
                        a.first_name,
                        a.last_name,
                        a.course_name,
                        sa.registration_fee,
                        sa.tuition_fee,
                        sa.other_charges,
                        sa.credits,
                        sa.payments_total,
                        sa.sponsor_amount_covered,
                        sa.outstanding_balance,
                        sa.status
                    FROM public.student_accounts sa
                    LEFT JOIN public.applications a
                        ON a.student_number =
                           sa.student_number
                    ORDER BY
                        a.last_name,
                        a.first_name,
                        sa.student_number
                    """
                )
            ).mappings().all()

            title = (
                "Student Balances Report"
            )

        elif report_code == (
            "programme-revenue"
        ):
            rows = connection.execute(
                text(
                    """
                    SELECT
                        COALESCE(
                            a.course_name,
                            'Unspecified'
                        ) AS programme,
                        COUNT(*) AS students,
                        COALESCE(
                            SUM(
                                sa.registration_fee
                                + sa.tuition_fee
                                + sa.other_charges
                            ),
                            0
                        ) AS billed,
                        COALESCE(
                            SUM(
                                sa.payments_total
                            ),
                            0
                        ) AS collected,
                        COALESCE(
                            SUM(
                                sa.outstanding_balance
                            ),
                            0
                        ) AS outstanding
                    FROM public.student_accounts sa
                    LEFT JOIN public.applications a
                        ON a.student_number =
                           sa.student_number
                    GROUP BY
                        COALESCE(
                            a.course_name,
                            'Unspecified'
                        )
                    ORDER BY programme
                    """
                )
            ).mappings().all()

            title = (
                "Programme Revenue Report"
            )

        else:
            raise ValueError(
                "Unknown finance report. "
                "Use monthly-income, "
                "outstanding-fees, "
                "collection-rate, sponsors, "
                "student-balances or "
                "programme-revenue."
            )

    return {
        "report_code": (
            report_code
        ),
        "title": title,
        "rows": [
            dict(
                row
            )
            for row in rows
        ],
    }


def _lookup_document_owner(
    *,
    kind: str,
    identifier: str | None,
    student_number: str | None,
) -> tuple[str, str | None]:
    if student_number:
        return (
            _clean_student_number(
                student_number
            ),
            identifier,
        )

    table_map = {
        "invoice": (
            "invoices",
            "invoice_number",
        ),
        "receipt": (
            "receipts",
            "receipt_number",
        ),
        "payment_plan": (
            "payment_plans",
            "id",
        ),
    }

    if kind not in table_map:
        raise ValueError(
            "Student number is required."
        )

    table_name, column_name = (
        table_map[
            kind
        ]
    )

    with engine.connect() as connection:
        if column_name == "id":
            row = connection.execute(
                text(
                    f"""
                    SELECT student_number
                    FROM public.{table_name}
                    WHERE id = CAST(
                        :identifier AS uuid
                    )
                    LIMIT 1
                    """
                ),
                {
                    "identifier": identifier
                },
            ).mappings().first()
        else:
            row = connection.execute(
                text(
                    f"""
                    SELECT student_number
                    FROM public.{table_name}
                    WHERE {column_name} =
                        :identifier
                    LIMIT 1
                    """
                ),
                {
                    "identifier": identifier
                },
            ).mappings().first()

    if not row:
        raise ValueError(
            "Finance document record "
            "not found."
        )

    return (
        row[
            "student_number"
        ],
        identifier,
    )


def generate_finance_document(
    *,
    kind: str,
    identifier: str | None = None,
    student_number: str | None = None,
) -> Path:
    from app.services import (
        finance_document_service,
    )

    function_map = {
        "invoice": (
            finance_document_service
            .generate_student_invoice
        ),
        "receipt": (
            finance_document_service
            .generate_student_receipt
        ),
        "statement": (
            finance_document_service
            .generate_student_statement
        ),
        "payment_plan": (
            finance_document_service
            .generate_student_payment_plan
        ),
    }

    if kind not in function_map:
        raise ValueError(
            "Unknown finance document type."
        )

    resolved_student, identifier = (
        _lookup_document_owner(
            kind=kind,
            identifier=identifier,
            student_number=(
                student_number
            ),
        )
    )

    function = function_map[
        kind
    ]

    signature = inspect.signature(
        function
    )

    kwargs = {}

    for parameter_name in (
        signature.parameters
    ):
        lower = (
            parameter_name.lower()
        )

        if lower in {
            "student_number",
            "studentnumber",
            "snum",
        }:
            kwargs[
                parameter_name
            ] = resolved_student

        elif (
            kind == "invoice"
            and "invoice"
            in lower
        ):
            kwargs[
                parameter_name
            ] = identifier

        elif (
            kind == "receipt"
            and "receipt"
            in lower
        ):
            kwargs[
                parameter_name
            ] = identifier

        elif (
            kind == "payment_plan"
            and (
                "payment_plan"
                in lower
                or "plan_id"
                in lower
            )
        ):
            kwargs[
                parameter_name
            ] = identifier

    result = function(
        **kwargs
    )

    if isinstance(
        result,
        dict,
    ):
        candidate = (
            result.get(
                "pdf_path"
            )
            or result.get(
                "path"
            )
            or result.get(
                "file_path"
            )
        )
    else:
        candidate = result

    if not candidate:
        raise RuntimeError(
            "Finance PDF generator did "
            "not return a file path."
        )

    path = Path(
        str(
            candidate
        )
    )

    if not path.exists():
        raise RuntimeError(
            "Generated finance PDF file "
            "was not found."
        )

    return path

# CANONICAL FINANCE OVERRIDES V1
# Transactional staff finance now uses the same finance_* tables
# as PayFast and student finance documents. Sponsor management
# stays on sponsors/student_sponsor_allocations because there is
# no duplicate finance_* sponsor family.

from app.services.staff_finance_canonical import (
    _lookup_document_owner as _canonical_lookup_document_owner,
    apply_credit as _canonical_apply_credit,
    create_charge as _canonical_create_charge,
    create_payment_plan as _canonical_create_payment_plan,
    create_statement as _canonical_create_statement,
    generate_finance_document as _canonical_generate_finance_document,
    get_finance_dashboard as _canonical_get_finance_dashboard,
    get_latest_payment_plan as _canonical_get_latest_payment_plan,
    get_student_finance as _canonical_get_student_finance,
    list_statements as _canonical_list_statements,
    list_student_invoices as _canonical_list_student_invoices,
    list_student_payments as _canonical_list_student_payments,
    list_student_receipts as _canonical_list_student_receipts,
    recalculate_student_account as _canonical_recalculate_student_account,
    record_payment as _canonical_record_payment,
    reverse_payment as _canonical_reverse_payment,
    run_finance_report as _canonical_run_finance_report,
    search_finance_students as _canonical_search_finance_students,
)

recalculate_student_account = _canonical_recalculate_student_account
get_finance_dashboard = _canonical_get_finance_dashboard
search_finance_students = _canonical_search_finance_students
get_student_finance = _canonical_get_student_finance
create_charge = _canonical_create_charge
list_student_payments = _canonical_list_student_payments
record_payment = _canonical_record_payment
reverse_payment = _canonical_reverse_payment
apply_credit = _canonical_apply_credit
list_student_invoices = _canonical_list_student_invoices
list_student_receipts = _canonical_list_student_receipts
get_latest_payment_plan = _canonical_get_latest_payment_plan
create_payment_plan = _canonical_create_payment_plan
create_statement = _canonical_create_statement
list_statements = _canonical_list_statements
run_finance_report = _canonical_run_finance_report
_lookup_document_owner = _canonical_lookup_document_owner
generate_finance_document = _canonical_generate_finance_document
