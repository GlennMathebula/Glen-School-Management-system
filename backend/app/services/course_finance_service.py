from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.database import engine

# ============================================================
# HELPERS
# ============================================================

def money(
    value,
) -> Decimal:

    if value is None:
        return Decimal("0.00")

    return Decimal(
        str(value)
    ).quantize(
        Decimal("0.01")
    )


# ============================================================
# REGISTRATION
# ============================================================

def get_registration(
    student_number: str,
) -> dict | None:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.registration_date,
            r.registration_status,
            r.funding_type,
            r.cycle,

            a.first_name,
            a.middle_name,
            a.last_name,
            a.email,

            c.course_name,
            c.nqf_level,
            c.credits

        FROM public.registrations r

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

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

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# GLOBAL FINANCE SETTING
# ============================================================

def get_finance_setting(
    setting_key: str,
) -> Decimal:

    query = text(
        """
        SELECT setting_value

        FROM public.finance_settings

        WHERE
            setting_key = :setting_key
            AND is_active = true

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        value = connection.execute(
            query,
            {
                "setting_key": (
                    setting_key
                ),
            },
        ).scalar_one_or_none()

    return money(
        value
    )


# ============================================================
# COURSE CONFIG
# ============================================================

def get_course_finance_config(
    course_code: str,
) -> dict | None:

    today = date.today()

    query = text(
        """
        SELECT
            id,
            course_code,
            tuition_fee,
            ppe_required,
            ppe_fee,
            is_active,
            effective_from,
            effective_to

        FROM public.course_finance_config

        WHERE
            course_code = :course_code
            AND is_active = true

            AND (
                effective_from IS NULL
                OR effective_from <= :today
            )

            AND (
                effective_to IS NULL
                OR effective_to >= :today
            )

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "course_code": (
                        course_code
                    ),
                    "today": today,
                },
            )
            .mappings()
            .first()
        )

    return (
        dict(row)
        if row
        else None
    )


# ============================================================
# ADDITIONAL FEES
# ============================================================

def get_course_additional_fees(
    course_code: str,
) -> list[dict]:

    today = date.today()

    query = text(
        """
        SELECT
            id,
            fee_name,
            fee_code,
            amount,
            is_mandatory,
            notes

        FROM public.course_additional_fees

        WHERE
            course_code = :course_code
            AND is_active = true

            AND (
                effective_from IS NULL
                OR effective_from <= :today
            )

            AND (
                effective_to IS NULL
                OR effective_to >= :today
            )

        ORDER BY
            fee_name
        """
    )

    with engine.connect() as connection:

        rows = (
            connection.execute(
                query,
                {
                    "course_code": (
                        course_code
                    ),
                    "today": today,
                },
            )
            .mappings()
            .all()
        )

    return [
        dict(row)
        for row in rows
    ]


# ============================================================
# BUILD COURSE FEE SCHEDULE
# ============================================================

def build_course_fee_schedule(
    course_code: str,
) -> dict:

    config = (
        get_course_finance_config(
            course_code
        )
    )

    if not config:

        raise ValueError(
            
                "Finance has not yet been configured "
                f"for course {course_code}."
            
        )

    registration_fee = (
        get_finance_setting(
            "REGISTRATION_FEE"
        )
    )

    tuition_fee = money(
        config[
            "tuition_fee"
        ]
    )

    ppe_required = bool(
        config[
            "ppe_required"
        ]
    )

    ppe_fee = (
        money(
            config[
                "ppe_fee"
            ]
        )
        if ppe_required
        else Decimal("0.00")
    )

    additional_fees = (
        get_course_additional_fees(
            course_code
        )
    )

    invoice_items = [
        {
            "description": (
                "Tuition Fee"
            ),
            "quantity": Decimal("1.00"),
            "unit_price": tuition_fee,
            "line_total": tuition_fee,
            "fee_type": "TUITION",
        },
        {
            "description": (
                "Registration Fee"
            ),
            "quantity": Decimal("1.00"),
            "unit_price": registration_fee,
            "line_total": registration_fee,
            "fee_type": "REGISTRATION",
        },
    ]

    if ppe_required and ppe_fee > 0:

        invoice_items.append(
            {
                "description": (
                    "Personal Protective Equipment (PPE)"
                ),
                "quantity": Decimal("1.00"),
                "unit_price": ppe_fee,
                "line_total": ppe_fee,
                "fee_type": "PPE",
            }
        )

    mandatory_additional_total = (
        Decimal("0.00")
    )

    optional_fees = []

    for fee in additional_fees:

        fee_amount = money(
            fee[
                "amount"
            ]
        )

        if fee[
            "is_mandatory"
        ]:

            mandatory_additional_total += (
                fee_amount
            )

            invoice_items.append(
                {
                    "description": (
                        fee[
                            "fee_name"
                        ]
                    ),
                    "quantity": Decimal("1.00"),
                    "unit_price": fee_amount,
                    "line_total": fee_amount,
                    "fee_type": (
                        fee.get(
                            "fee_code"
                        )
                        or "ADDITIONAL"
                    ),
                }
            )

        else:

            optional_fees.append(
                {
                    "fee_id": str(
                        fee[
                            "id"
                        ]
                    ),
                    "fee_name": (
                        fee[
                            "fee_name"
                        ]
                    ),
                    "fee_code": (
                        fee[
                            "fee_code"
                        ]
                    ),
                    "amount": float(
                        fee_amount
                    ),
                    "notes": (
                        fee[
                            "notes"
                        ]
                    ),
                }
            )

    other_fees = (
        registration_fee
        + ppe_fee
        + mandatory_additional_total
    )

    total_amount = (
        tuition_fee
        + other_fees
    )

    return {
        "course_code": (
            course_code
        ),

        "tuition_fee": (
            tuition_fee
        ),

        "registration_fee": (
            registration_fee
        ),

        "ppe_required": (
            ppe_required
        ),

        "ppe_fee": (
            ppe_fee
        ),

        "other_fees": (
            other_fees
        ),

        "total_amount": (
            total_amount
        ),

        "invoice_items": (
            invoice_items
        ),

        "optional_fees": (
            optional_fees
        ),
    }


# ============================================================
# CREATE FINANCE ACCOUNT + INITIAL INVOICE
# ============================================================

def ensure_student_finance_account(
    student_number: str,
    created_by: str = "SYSTEM",
) -> dict:

    registration = (
        get_registration(
            student_number
        )
    )

    if not registration:

        raise ValueError(
            "Student registration not found."
        )

    fee_schedule = (
        build_course_fee_schedule(
            registration[
                "course_code"
            ]
        )
    )

    with engine.begin() as connection:

        existing_account = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        tuition_fee,
                        other_fees,
                        funding_type,
                        account_status

                    FROM public.finance_accounts

                    WHERE
                        registration_id
                        = CAST(
                            :registration_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "registration_id": str(
                        registration[
                            "registration_id"
                        ]
                    ),
                },
            )
            .mappings()
            .first()
        )

        if existing_account:

            return {
                "created": False,
                "finance_account_id": str(
                    existing_account[
                        "id"
                    ]
                ),
                "student_number": (
                    student_number
                ),
            }

        account = (
            connection.execute(
                text(
                    """
                    INSERT INTO public.finance_accounts
                    (
                        registration_id,
                        tuition_fee,
                        other_fees,
                        funding_type,
                        account_status
                    )

                    VALUES
                    (
                        CAST(
                            :registration_id
                            AS uuid
                        ),
                        :tuition_fee,
                        :other_fees,
                        :funding_type,
                        'Active'
                    )

                    RETURNING id
                    """
                ),
                {
                    "registration_id": str(
                        registration[
                            "registration_id"
                        ]
                    ),
                    "tuition_fee": (
                        fee_schedule[
                            "tuition_fee"
                        ]
                    ),
                    "other_fees": (
                        fee_schedule[
                            "other_fees"
                        ]
                    ),
                    "funding_type": (
                        registration[
                            "funding_type"
                        ]
                    ),
                },
            )
            .mappings()
            .one()
        )

        finance_account_id = str(
            account[
                "id"
            ]
        )

        invoice_number = (
            connection.execute(
                text(
                    """
                    SELECT
                        public.next_finance_invoice_number(
                            :target_year
                        )
                    """
                ),
                {
                    "target_year": (
                        date.today().year
                    ),
                },
            )
            .scalar_one()
        )

        invoice = (
            connection.execute(
                text(
                    """
                    INSERT INTO public.finance_invoices
                    (
                        finance_account_id,
                        invoice_number,
                        invoice_date,
                        due_date,
                        subtotal,
                        discount_amount,
                        total_amount,
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
                        :invoice_number,
                        CURRENT_DATE,
                        NULL,
                        :subtotal,
                        0,
                        :total_amount,
                        'Issued',
                        :notes,
                        :created_by
                    )

                    RETURNING id
                    """
                ),
                {
                    "finance_account_id": (
                        finance_account_id
                    ),
                    "invoice_number": (
                        invoice_number
                    ),
                    "subtotal": (
                        fee_schedule[
                            "total_amount"
                        ]
                    ),
                    "total_amount": (
                        fee_schedule[
                            "total_amount"
                        ]
                    ),
                    "notes": (
                        "Initial course fee invoice."
                    ),
                    "created_by": (
                        created_by
                    ),
                },
            )
            .mappings()
            .one()
        )

        invoice_id = str(
            invoice[
                "id"
            ]
        )

        for item in fee_schedule[
            "invoice_items"
        ]:

            connection.execute(
                text(
                    """
                    INSERT INTO public.finance_invoice_items
                    (
                        invoice_id,
                        description,
                        quantity,
                        unit_price,
                        line_total
                    )

                    VALUES
                    (
                        CAST(
                            :invoice_id
                            AS uuid
                        ),
                        :description,
                        :quantity,
                        :unit_price,
                        :line_total
                    )
                    """
                ),
                {
                    "invoice_id": (
                        invoice_id
                    ),
                    "description": (
                        item[
                            "description"
                        ]
                    ),
                    "quantity": (
                        item[
                            "quantity"
                        ]
                    ),
                    "unit_price": (
                        item[
                            "unit_price"
                        ]
                    ),
                    "line_total": (
                        item[
                            "line_total"
                        ]
                    ),
                },
            )

    return {
        "created": True,
        "student_number": (
            student_number
        ),
        "finance_account_id": (
            finance_account_id
        ),
        "invoice_id": (
            invoice_id
        ),
        "invoice_number": (
            invoice_number
        ),
        "total_amount": float(
            fee_schedule[
                "total_amount"
            ]
        ),
    }