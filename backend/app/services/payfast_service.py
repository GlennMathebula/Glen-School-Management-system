import hashlib
import socket
from collections import OrderedDict
from datetime import date
from decimal import Decimal
from urllib.parse import quote_plus

import httpx
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.services.course_finance_service import (
    ensure_student_finance_account,
)

# ============================================================
# CONFIG
# ============================================================

PAYFAST_SANDBOX = (
    settings.payfast_sandbox
)

PAYFAST_MERCHANT_ID = (
    settings.payfast_merchant_id
    or ""
)

PAYFAST_MERCHANT_KEY = (
    settings.payfast_merchant_key
    or ""
)

PAYFAST_PASSPHRASE = (
    settings.payfast_passphrase
    or ""
)

PAYFAST_RETURN_URL = (
    settings.payfast_return_url
)

PAYFAST_CANCEL_URL = (
    settings.payfast_cancel_url
)

PAYFAST_NOTIFY_URL = (
    settings.payfast_notify_url
)


if PAYFAST_SANDBOX:

    PAYFAST_PAYMENT_URL = (
        "https://sandbox.payfast.co.za/eng/process"
    )

    PAYFAST_VALIDATE_URL = (
        "https://sandbox.payfast.co.za/eng/query/validate"
    )

else:

    PAYFAST_PAYMENT_URL = (
        "https://www.payfast.co.za/eng/process"
    )

    PAYFAST_VALIDATE_URL = (
        "https://www.payfast.co.za/eng/query/validate"
    )
# ============================================================
# CONFIG CHECK
# ============================================================

def require_payfast_config() -> None:

    missing = []

    if not PAYFAST_MERCHANT_ID:
        missing.append(
            "PAYFAST_MERCHANT_ID"
        )

    if not PAYFAST_MERCHANT_KEY:
        missing.append(
            "PAYFAST_MERCHANT_KEY"
        )

    if missing:

        raise ValueError(
            "Missing PayFast settings: "
            + ", ".join(
                missing
            )
        )


# ============================================================
# PAYFAST URL ENCODING
# ============================================================

def payfast_encode(
    value,
) -> str:

    encoded = quote_plus(
        str(value).strip(),
        safe="",
    )

    # urllib already uses uppercase hexadecimal escapes.
    return encoded


# ============================================================
# SIGNATURE
# ============================================================

def generate_payfast_signature(
    data: OrderedDict | dict,
    passphrase: str | None = None,
) -> str:

    parts = []

    for key, value in data.items():

        if key == "signature":
            continue

        if value is None:
            continue

        value = str(
            value
        ).strip()

        if value == "":
            continue

        parts.append(
            
                f"{key}="
                f"{payfast_encode(value)}"
            
        )

    parameter_string = "&".join(
        parts
    )

    if passphrase:

        parameter_string += (
            "&passphrase="
            + payfast_encode(
                passphrase
            )
        )

    return hashlib.md5(
        parameter_string.encode(
            "utf-8"
        )
    ).hexdigest()


# ============================================================
# GET FINANCE DATA
# ============================================================

def get_student_payment_context(
    student_number: str,
) -> dict:

    query = text(
        """
        SELECT
            r.student_number,
            r.funding_type,

            a.first_name,
            a.last_name,
            a.email,

            fa.id AS finance_account_id,

            fi.id AS invoice_id,
            fi.invoice_number,
            fi.total_amount

        FROM public.registrations r

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.finance_accounts fa
            ON fa.registration_id = r.id

        LEFT JOIN LATERAL
        (
            SELECT
                id,
                invoice_number,
                total_amount

            FROM public.finance_invoices

            WHERE
                finance_account_id = fa.id
                AND status <> 'Cancelled'

            ORDER BY
                invoice_date,
                created_at

            LIMIT 1
        ) fi ON true

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

        context = dict(
            row
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
                        context[
                            "finance_account_id"
                        ]
                    ),
                },
            )
            .scalar_one()
        )

    invoice_total = Decimal(
        str(
            context.get(
                "total_amount"
            )
            or 0
        )
    )

    total_paid = Decimal(
        str(
            total_paid
        )
    )

    outstanding = (
        invoice_total
        - total_paid
    )

    if outstanding < 0:

        outstanding = Decimal(
            "0.00"
        )

    context[
        "outstanding_balance"
    ] = outstanding.quantize(
        Decimal("0.01")
    )

    return context


# ============================================================
# FUNDING RULE
# ============================================================

def get_funding_rule(
    funding_type: str | None,
) -> dict:

    if not funding_type:

        return {
            "student_is_payer": True,
            "allow_pay_later": True,
            "payfast_enabled": True,
        }

    query = text(
        """
        SELECT
            student_is_payer,
            allow_pay_later,
            payfast_enabled

        FROM public.finance_funding_rules

        WHERE
            LOWER(funding_type)
            = LOWER(:funding_type)

            AND is_active = true

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "funding_type": (
                        funding_type
                    ),
                },
            )
            .mappings()
            .first()
        )

    if row:

        return dict(
            row
        )

    # Safe default until CFO configures the funding type.
    return {
        "student_is_payer": True,
        "allow_pay_later": True,
        "payfast_enabled": True,
    }


# ============================================================
# CREATE PAYFAST TRANSACTION
# ============================================================

def start_payfast_payment(
    student_number: str,
    requested_amount: Decimal | None = None,
) -> dict:

    require_payfast_config()

    try:

        context = (
            get_student_payment_context(
                student_number
            )
        )

    except ValueError:

        ensure_student_finance_account(
            student_number,
            created_by="SYSTEM",
        )

        context = (
            get_student_payment_context(
                student_number
            )
        )

    rule = get_funding_rule(
        context.get(
            "funding_type"
        )
    )

    if not rule[
        "payfast_enabled"
    ]:

        raise ValueError(
            
                "PayFast payment is disabled "
                "for this funding type."
            
        )

    outstanding = (
        context[
            "outstanding_balance"
        ]
    )

    if outstanding <= 0:

        raise ValueError(
            "There is no outstanding balance."
        )

    if requested_amount is None:

        amount = outstanding

    else:

        amount = Decimal(
            str(
                requested_amount
            )
        ).quantize(
            Decimal("0.01")
        )

    if amount < Decimal(
        "5.00"
    ):

        raise ValueError(
            "PayFast payments must be at least R5.00."
        )

    if amount > outstanding:

        raise ValueError(
            
                "Payment amount cannot exceed "
                "the outstanding balance."
            
        )

    with engine.begin() as connection:

        payment_reference = (
            connection.execute(
                text(
                    """
                    SELECT
                        public.next_finance_payment_reference(
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

        merchant_payment_id = (
            payment_reference
        )

        item_name = (
            "Glen Moniques Student Fees "
            f"{context['student_number']}"
        )

        connection.execute(
            text(
                """
                INSERT INTO
                    public.finance_payfast_transactions
                (
                    finance_account_id,
                    invoice_id,
                    merchant_payment_id,
                    amount,
                    item_name,
                    status,
                    payer_email
                )

                VALUES
                (
                    CAST(
                        :finance_account_id
                        AS uuid
                    ),

                    CAST(
                        :invoice_id
                        AS uuid
                    ),

                    :merchant_payment_id,
                    :amount,
                    :item_name,
                    'Initiated',
                    :payer_email
                )
                """
            ),
            {
                "finance_account_id": str(
                    context[
                        "finance_account_id"
                    ]
                ),

                "invoice_id": (
                    str(
                        context[
                            "invoice_id"
                        ]
                    )
                    if context.get(
                        "invoice_id"
                    )
                    else None
                ),

                "merchant_payment_id": (
                    merchant_payment_id
                ),

                "amount": (
                    amount
                ),

                "item_name": (
                    item_name
                ),

                "payer_email": (
                    context.get(
                        "email"
                    )
                ),
            },
        )

    fields = OrderedDict()

    fields[
        "merchant_id"
    ] = PAYFAST_MERCHANT_ID

    fields[
        "merchant_key"
    ] = PAYFAST_MERCHANT_KEY

    fields[
        "return_url"
    ] = PAYFAST_RETURN_URL

    fields[
        "cancel_url"
    ] = PAYFAST_CANCEL_URL

    fields[
        "notify_url"
    ] = PAYFAST_NOTIFY_URL

    fields[
        "name_first"
    ] = (
        context.get(
            "first_name"
        )
        or ""
    )

    fields[
        "name_last"
    ] = (
        context.get(
            "last_name"
        )
        or ""
    )

    fields[
        "email_address"
    ] = (
        context.get(
            "email"
        )
        or ""
    )

    fields[
        "m_payment_id"
    ] = merchant_payment_id

    fields[
        "amount"
    ] = (
        f"{amount:.2f}"
    )

    fields[
        "item_name"
    ] = item_name

    signature = (
        generate_payfast_signature(
            fields,
            PAYFAST_PASSPHRASE
            or None,
        )
    )

    fields[
        "signature"
    ] = signature

    return {
        "payment_url": (
            PAYFAST_PAYMENT_URL
        ),

        "fields": dict(
            fields
        ),

        "merchant_payment_id": (
            merchant_payment_id
        ),

        "amount": (
            amount
        ),

        "sandbox": (
            PAYFAST_SANDBOX
        ),
    }


# ============================================================
# VERIFY ITN SIGNATURE
# ============================================================

def verify_itn_signature(
    form_data: OrderedDict,
) -> bool:

    supplied_signature = (
        form_data.get(
            "signature"
        )
        or ""
    )

    expected_signature = (
        generate_payfast_signature(
            form_data,
            PAYFAST_PASSPHRASE
            or None,
        )
    )

    return (
        supplied_signature.lower()
        == expected_signature.lower()
    )


# ============================================================
# VERIFY PAYFAST SOURCE IP
# ============================================================

def get_payfast_ips() -> set[str]:

    hosts = {
        "www.payfast.co.za",
        "w1w.payfast.co.za",
        "w2w.payfast.co.za",
        "sandbox.payfast.co.za",
    }

    ips = set()

    for host in hosts:

        try:

            _name, _aliases, addresses = (
                socket.gethostbyname_ex(
                    host
                )
            )

            ips.update(
                addresses
            )

        except socket.gaierror:

            continue

    return ips


def verify_payfast_source(
    client_ip: str | None,
) -> bool:

    if not client_ip:

        return False

    return (
        client_ip
        in get_payfast_ips()
    )


# ============================================================
# SERVER CONFIRMATION
# ============================================================

async def verify_payfast_server(
    form_data: OrderedDict,
) -> bool:

    validation_data = OrderedDict(
        (
            key,
            value,
        )
        for key, value in form_data.items()
        if key != "signature"
    )

    async with httpx.AsyncClient(
        timeout=20.0,
    ) as client:

        response = await client.post(
            PAYFAST_VALIDATE_URL,
            data=validation_data,
        )

    return (
        response.status_code == 200
        and response.text.strip()
        == "VALID"
    )


# ============================================================
# GET PAYFAST TRANSACTION
# ============================================================

def get_payfast_transaction(
    merchant_payment_id: str,
) -> dict | None:

    query = text(
        """
        SELECT *

        FROM
            public.finance_payfast_transactions

        WHERE
            merchant_payment_id
            = :merchant_payment_id

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = (
            connection.execute(
                query,
                {
                    "merchant_payment_id": (
                        merchant_payment_id
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
# PROCESS VERIFIED ITN
# ============================================================

def process_verified_itn(
    form_data: OrderedDict,
    signature_verified: bool,
    source_verified: bool,
    server_verified: bool,
) -> dict:

    merchant_payment_id = (
        form_data.get(
            "m_payment_id"
        )
    )

    if not merchant_payment_id:

        raise ValueError(
            "PayFast ITN has no m_payment_id."
        )

    transaction = (
        get_payfast_transaction(
            merchant_payment_id
        )
    )

    if not transaction:

        raise ValueError(
            "PayFast transaction not found."
        )

    expected_amount = Decimal(
        str(
            transaction[
                "amount"
            ]
        )
    ).quantize(
        Decimal("0.01")
    )

    received_amount = Decimal(
        str(
            form_data.get(
                "amount_gross"
            )
            or "0"
        )
    ).quantize(
        Decimal("0.01")
    )

    amount_verified = (
        abs(
            expected_amount
            - received_amount
        )
        <= Decimal("0.01")
    )

    payment_status = (
        form_data.get(
            "payment_status"
        )
        or ""
    ).upper()

    is_complete = (
        payment_status
        == "COMPLETE"
        and signature_verified
        and source_verified
        and amount_verified
        and server_verified
    )

    pf_payment_id = (
        form_data.get(
            "pf_payment_id"
        )
    )

    with engine.begin() as connection:

        connection.execute(
            text(
                """
                UPDATE
                    public.finance_payfast_transactions

                SET
                    payfast_payment_id
                        = :payfast_payment_id,

                    status
                        = :status,

                    payment_method
                        = :payment_method,

                    payer_email
                        = COALESCE(
                            :payer_email,
                            payer_email
                        ),

                    signature_verified
                        = :signature_verified,

                    source_verified
                        = :source_verified,

                    amount_verified
                        = :amount_verified,

                    raw_itn_payload
                        = CAST(
                            :raw_itn_payload
                            AS jsonb
                        ),

                    completed_at
                        = CASE
                            WHEN :status = 'Complete'
                            THEN now()
                            ELSE completed_at
                          END,

                    updated_at = now()

                WHERE
                    id = CAST(
                        :transaction_id
                        AS uuid
                    )
                """
            ),
            {
                "payfast_payment_id": (
                    pf_payment_id
                ),

                "status": (
                    "Complete"
                    if is_complete
                    else "Failed"
                ),

                "payment_method": (
                    form_data.get(
                        "payment_method"
                    )
                    or "PayFast"
                ),

                "payer_email": (
                    form_data.get(
                        "email_address"
                    )
                ),

                "signature_verified": (
                    signature_verified
                ),

                "source_verified": (
                    source_verified
                ),

                "amount_verified": (
                    amount_verified
                ),

                "raw_itn_payload": (
                    __import__(
                        "json"
                    ).dumps(
                        dict(
                            form_data
                        )
                    )
                ),

                "transaction_id": str(
                    transaction[
                        "id"
                    ]
                ),
            },
        )

        if not is_complete:

            return {
                "completed": False,
                "merchant_payment_id": (
                    merchant_payment_id
                ),
                "signature_verified": (
                    signature_verified
                ),
                "source_verified": (
                    source_verified
                ),
                "amount_verified": (
                    amount_verified
                ),
                "server_verified": (
                    server_verified
                ),
            }

        existing_payment = (
            connection.execute(
                text(
                    """
                    SELECT id

                    FROM
                        public.finance_payments

                    WHERE
                        external_reference
                        = :external_reference

                    LIMIT 1
                    """
                ),
                {
                    "external_reference": (
                        pf_payment_id
                        or merchant_payment_id
                    ),
                },
            )
            .mappings()
            .first()
        )

        if existing_payment:

            payment_id = str(
                existing_payment[
                    "id"
                ]
            )

        else:

            payment_reference = (
                connection.execute(
                    text(
                        """
                        SELECT
                            public.next_finance_payment_reference(
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

            payment = (
                connection.execute(
                    text(
                        """
                        INSERT INTO
                            public.finance_payments
                        (
                            finance_account_id,
                            payment_reference,
                            payment_date,
                            amount,
                            payment_method,
                            external_reference,
                            status,
                            notes,
                            recorded_by
                        )

                        VALUES
                        (
                            CAST(
                                :finance_account_id
                                AS uuid
                            ),
                            :payment_reference,
                            CURRENT_DATE,
                            :amount,
                            'PayFast',
                            :external_reference,
                            'Completed',
                            :notes,
                            'PAYFAST'
                        )

                        RETURNING id
                        """
                    ),
                    {
                        "finance_account_id": str(
                            transaction[
                                "finance_account_id"
                            ]
                        ),

                        "payment_reference": (
                            payment_reference
                        ),

                        "amount": (
                            received_amount
                        ),

                        "external_reference": (
                            pf_payment_id
                            or merchant_payment_id
                        ),

                        "notes": (
                            "Verified PayFast payment."
                        ),
                    },
                )
                .mappings()
                .one()
            )

            payment_id = str(
                payment[
                    "id"
                ]
            )

        existing_receipt = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        receipt_number

                    FROM
                        public.finance_receipts

                    WHERE
                        payment_id
                        = CAST(
                            :payment_id
                            AS uuid
                        )

                    LIMIT 1
                    """
                ),
                {
                    "payment_id": (
                        payment_id
                    ),
                },
            )
            .mappings()
            .first()
        )

        if existing_receipt:

            receipt_number = (
                existing_receipt[
                    "receipt_number"
                ]
            )

        else:

            receipt_number = (
                connection.execute(
                    text(
                        """
                        SELECT
                            public.next_finance_receipt_number(
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

            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.finance_receipts
                    (
                        payment_id,
                        receipt_number,
                        issued_by
                    )

                    VALUES
                    (
                        CAST(
                            :payment_id
                            AS uuid
                        ),
                        :receipt_number,
                        'SYSTEM'
                    )
                    """
                ),
                {
                    "payment_id": (
                        payment_id
                    ),

                    "receipt_number": (
                        receipt_number
                    ),
                },
            )

        if transaction.get(
            "invoice_id"
        ):

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
                            transaction[
                                "finance_account_id"
                            ]
                        ),
                    },
                )
                .scalar_one()
            )

            invoice_total = (
                connection.execute(
                    text(
                        """
                        SELECT total_amount

                        FROM public.finance_invoices

                        WHERE
                            id = CAST(
                                :invoice_id
                                AS uuid
                            )
                        """
                    ),
                    {
                        "invoice_id": str(
                            transaction[
                                "invoice_id"
                            ]
                        ),
                    },
                )
                .scalar_one()
            )

            total_paid = Decimal(
                str(
                    total_paid
                )
            )

            invoice_total = Decimal(
                str(
                    invoice_total
                )
            )

            if total_paid >= invoice_total:

                invoice_status = (
                    "Paid"
                )

            elif total_paid > 0:

                invoice_status = (
                    "Partially Paid"
                )

            else:

                invoice_status = (
                    "Issued"
                )

            connection.execute(
                text(
                    """
                    UPDATE
                        public.finance_invoices

                    SET
                        status = :status,
                        updated_at = now()

                    WHERE
                        id = CAST(
                            :invoice_id
                            AS uuid
                        )
                    """
                ),
                {
                    "status": (
                        invoice_status
                    ),

                    "invoice_id": str(
                        transaction[
                            "invoice_id"
                        ]
                    ),
                },
            )

    return {
        "completed": True,
        "merchant_payment_id": (
            merchant_payment_id
        ),
        "payfast_payment_id": (
            pf_payment_id
        ),
        "receipt_number": (
            receipt_number
        ),
        "amount": float(
            received_amount
        ),
    }