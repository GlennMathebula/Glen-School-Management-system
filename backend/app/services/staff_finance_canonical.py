from __future__ import annotations

import inspect
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from uuid import UUID, uuid4

from sqlalchemy import text

from app.database import engine
from app.services.course_finance_service import ensure_student_finance_account
from app.services.finance_document_service import (
    generate_student_invoice,
    generate_student_payment_plan,
    generate_student_receipt,
    generate_student_statement,
)
from app.services.staff_audit_service import create_staff_audit_log


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


def _money(value) -> Decimal:
    if value in (None, ""):
        return ZERO
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def _serial(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    return value


def _dict(row):
    if not row:
        return None
    return {key: _serial(value) for key, value in dict(row).items()}


def _rows(rows):
    return [_dict(row) for row in rows]


def _clean_student_number(value) -> str:
    value = str(value or "").strip().upper()
    if not value:
        raise ValueError("Student number is required.")
    return value


def _pick(args, kwargs, index, *names, default=None):
    for name in names:
        if name in kwargs:
            return kwargs[name]
    if index < len(args):
        return args[index]
    return default


def _actor(args, kwargs, index=0) -> str:
    value = _pick(
        args,
        kwargs,
        index,
        "actor_staff_code",
        "staff_code",
        "recorded_by",
        "created_by",
        default="SYSTEM",
    )
    return str(value or "SYSTEM").strip().upper()


def _audit(
    *,
    actor_staff_code,
    action_code,
    entity_type,
    entity_id,
    description,
    before_data=None,
    after_data=None,
    metadata=None,
):
    try:
        create_staff_audit_log(
            actor_staff_code=actor_staff_code,
            action_code=action_code,
            module_code="FINANCE",
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            before_data=before_data,
            after_data=after_data,
            metadata=metadata or {},
        )
    except Exception as error:
        print(f"WARNING: finance audit log failed: {error}")


def _registration(connection, student_number):
    return connection.execute(
        text(
            """
            SELECT
                r.id AS registration_id,
                r.student_number,
                r.course_code,
                r.cycle,
                r.funding_type,
                r.registration_status,
                r.registration_date,
                a.first_name,
                a.middle_name,
                a.last_name,
                a.email,
                a.cell_number
            FROM public.registrations r
            JOIN public.applications a
              ON a.id = r.application_id
            WHERE r.student_number = :student_number
            ORDER BY r.registration_date DESC, r.created_at DESC
            LIMIT 1
            """
        ),
        {"student_number": student_number},
    ).mappings().first()


def _ensure_account(student_number: str):
    student_number = _clean_student_number(student_number)

    try:
        result = ensure_student_finance_account(student_number)
        if result:
            return result
    except TypeError:
        pass

    with engine.begin() as connection:
        registration = _registration(connection, student_number)
        if not registration:
            raise ValueError("Student registration was not found.")

        row = connection.execute(
            text(
                """
                INSERT INTO public.finance_accounts (
                    registration_id,
                    tuition_fee,
                    other_fees,
                    funding_type,
                    account_status
                )
                VALUES (
                    :registration_id,
                    0,
                    0,
                    :funding_type,
                    'Active'
                )
                ON CONFLICT (registration_id)
                DO UPDATE SET updated_at = NOW()
                RETURNING *
                """
            ),
            {
                "registration_id": registration["registration_id"],
                "funding_type": registration["funding_type"],
            },
        ).mappings().first()

    return _dict(row)


def _identity(connection, student_number):
    return connection.execute(
        text(
            """
            SELECT
                fa.id AS finance_account_id,
                fa.registration_id,
                fa.tuition_fee,
                fa.other_fees,
                fa.funding_type,
                fa.account_status,
                r.student_number,
                r.course_code,
                r.cycle,
                r.registration_status,
                a.first_name,
                a.middle_name,
                a.last_name,
                a.email,
                a.cell_number
            FROM public.finance_accounts fa
            JOIN public.registrations r
              ON r.id = fa.registration_id
            JOIN public.applications a
              ON a.id = r.application_id
            WHERE r.student_number = :student_number
            ORDER BY r.registration_date DESC, fa.created_at DESC
            LIMIT 1
            """
        ),
        {"student_number": student_number},
    ).mappings().first()


def _summary(connection, account_id, student_number):
    charges = _money(
        connection.execute(
            text(
                """
                SELECT COALESCE(SUM(total_amount), 0)
                FROM public.finance_invoices
                WHERE finance_account_id = :account_id
                  AND lower(status) NOT IN ('cancelled','void','reversed')
                """
            ),
            {"account_id": account_id},
        ).scalar_one()
    )

    payments = _money(
        connection.execute(
            text(
                """
                SELECT COALESCE(SUM(amount), 0)
                FROM public.finance_payments
                WHERE finance_account_id = :account_id
                  AND lower(status) = 'completed'
                  AND COALESCE(is_reversed, FALSE) = FALSE
                """
            ),
            {"account_id": account_id},
        ).scalar_one()
    )

    sponsor = _money(
        connection.execute(
            text(
                """
                SELECT COALESCE(SUM(amount_covered), 0)
                FROM public.student_sponsor_allocations
                WHERE student_number = :student_number
                """
            ),
            {"student_number": student_number},
        ).scalar_one()
    )

    outstanding = max(ZERO, charges - payments - sponsor)

    return {
        "total_charges": charges,
        "total_payments": payments,
        "sponsor_covered": sponsor,
        "outstanding_balance": outstanding,
    }


def _next_reference(prefix):
    return f"{prefix}-{date.today().year}-{uuid4().hex[:8].upper()}"


def _invoke_generator(func, values):
    signature = inspect.signature(func)
    kwargs = {}

    aliases = {
        "student_number": {"student_number", "student_no"},
        "invoice_number": {"invoice_number", "invoice_no"},
        "receipt_number": {"receipt_number", "receipt_no"},
        "payment_plan_id": {"payment_plan_id", "plan_id"},
        "statement_year": {"statement_year", "year"},
        "statement_month": {"statement_month", "month"},
    }

    for name, param in signature.parameters.items():
        found = False

        if name in values:
            kwargs[name] = values[name]
            found = True
        else:
            for canonical, names in aliases.items():
                if name in names and canonical in values:
                    kwargs[name] = values[canonical]
                    found = True
                    break

        if (
            not found
            and param.default is inspect._empty
            and param.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        ):
            raise RuntimeError(
                f"Cannot call finance document generator; missing parameter {name}."
            )

    result = func(**kwargs)

    if isinstance(result, (str, Path)):
        return {"pdf_path": str(result)}
    if isinstance(result, dict):
        return result

    raise RuntimeError("Unsupported finance document generator result.")


def recalculate_student_account(student_number):
    student_number = _clean_student_number(student_number)
    _ensure_account(student_number)

    with engine.connect() as connection:
        identity = _identity(connection, student_number)
        if not identity:
            raise ValueError("Finance account was not found.")

        summary = _summary(
            connection,
            identity["finance_account_id"],
            student_number,
        )

    return {
        "student_number": student_number,
        "tuition_fee": float(_money(identity["tuition_fee"])),
        "other_charges": float(_money(identity["other_fees"])),
        "payments_total": float(summary["total_payments"]),
        "sponsor_amount_covered": float(summary["sponsor_covered"]),
        "outstanding_balance": float(summary["outstanding_balance"]),
        "status": identity["account_status"],
        "account_status": identity["account_status"],
    }


def get_finance_dashboard():
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                WITH charges AS (
                    SELECT
                        fa.id,
                        COALESCE(
                            SUM(
                                CASE
                                    WHEN lower(fi.status)
                                         NOT IN ('cancelled','void','reversed')
                                    THEN fi.total_amount
                                    ELSE 0
                                END
                            ),
                            0
                        ) AS billed
                    FROM public.finance_accounts fa
                    LEFT JOIN public.finance_invoices fi
                      ON fi.finance_account_id = fa.id
                    GROUP BY fa.id
                ),
                paid AS (
                    SELECT
                        finance_account_id,
                        COALESCE(SUM(amount), 0) AS amount
                    FROM public.finance_payments
                    WHERE lower(status) = 'completed'
                      AND COALESCE(is_reversed, FALSE) = FALSE
                    GROUP BY finance_account_id
                )
                SELECT
                    COUNT(*) AS total_accounts,
                    COALESCE(SUM(charges.billed), 0) AS total_charges,
                    COALESCE(SUM(COALESCE(paid.amount, 0)), 0) AS total_payments,
                    COALESCE(
                        SUM(
                            GREATEST(
                                0,
                                charges.billed - COALESCE(paid.amount, 0)
                            )
                        ),
                        0
                    ) AS outstanding_balance
                FROM charges
                LEFT JOIN paid
                  ON paid.finance_account_id = charges.id
                """
            )
        ).mappings().first()

        recent = connection.execute(
            text(
                """
                SELECT
                    fp.payment_reference AS payment_id,
                    r.student_number,
                    fp.amount,
                    fp.payment_method AS method,
                    fp.payment_date,
                    CASE
                        WHEN COALESCE(fp.is_reversed, FALSE)
                        THEN 'Reversed'
                        ELSE fp.status
                    END AS status
                FROM public.finance_payments fp
                JOIN public.finance_accounts fa
                  ON fa.id = fp.finance_account_id
                JOIN public.registrations r
                  ON r.id = fa.registration_id
                ORDER BY fp.created_at DESC
                LIMIT 10
                """
            )
        ).mappings().all()

    total_charges = _money(row["total_charges"])
    total_payments = _money(row["total_payments"])
    rate = ZERO if total_charges <= ZERO else (
        total_payments / total_charges * Decimal("100")
    ).quantize(CENT)

    return {
        "total_accounts": int(row["total_accounts"] or 0),
        "total_charges": float(total_charges),
        "total_payments": float(total_payments),
        "outstanding_balance": float(_money(row["outstanding_balance"])),
        "collection_rate": float(rate),
        "recent_payments": _rows(recent),
    }


def search_finance_students(*args, **kwargs):
    query = str(_pick(args, kwargs, 0, "query", "search", "q", default="") or "").strip()
    status = _pick(args, kwargs, 1, "status", "account_status", default=None)
    limit = int(_pick(args, kwargs, 2, "limit", default=50) or 50)
    limit = max(1, min(limit, 200))

    params = {"pattern": f"%{query}%", "limit": limit}
    status_sql = ""

    if status:
        status_sql = "AND lower(fa.account_status) = lower(:status)"
        params["status"] = str(status).strip()

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                f"""
                SELECT
                    r.student_number,
                    a.first_name,
                    a.last_name,
                    a.email,
                    r.course_code,
                    r.cycle,
                    fa.id AS finance_account_id,
                    fa.funding_type,
                    fa.account_status,
                    COALESCE(
                        (
                            SELECT SUM(fi.total_amount)
                            FROM public.finance_invoices fi
                            WHERE fi.finance_account_id = fa.id
                              AND lower(fi.status)
                                  NOT IN ('cancelled','void','reversed')
                        ),
                        0
                    ) AS total_charges,
                    COALESCE(
                        (
                            SELECT SUM(fp.amount)
                            FROM public.finance_payments fp
                            WHERE fp.finance_account_id = fa.id
                              AND lower(fp.status) = 'completed'
                              AND COALESCE(fp.is_reversed, FALSE) = FALSE
                        ),
                        0
                    ) AS payments_total
                FROM public.registrations r
                JOIN public.applications a
                  ON a.id = r.application_id
                LEFT JOIN public.finance_accounts fa
                  ON fa.registration_id = r.id
                WHERE (
                    :pattern = '%%'
                    OR r.student_number ILIKE :pattern
                    OR a.first_name ILIKE :pattern
                    OR a.last_name ILIKE :pattern
                    OR COALESCE(a.email, '') ILIKE :pattern
                )
                {status_sql}
                ORDER BY a.last_name, a.first_name, r.student_number
                LIMIT :limit
                """
            ),
            params,
        ).mappings().all()

    result = []
    for row in rows:
        item = _dict(row)
        charges = _money(item.get("total_charges"))
        payments = _money(item.get("payments_total"))
        item["outstanding_balance"] = float(max(ZERO, charges - payments))
        result.append(item)

    return result


def list_student_payments(student_number):
    student_number = _clean_student_number(student_number)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fp.id,
                    fp.payment_reference AS payment_id,
                    fp.payment_reference,
                    r.student_number,
                    fi.invoice_number,
                    fp.amount,
                    fp.payment_method AS method,
                    fp.payment_method,
                    fp.payment_date,
                    CASE
                        WHEN COALESCE(fp.is_reversed, FALSE)
                        THEN 'Reversed'
                        ELSE fp.status
                    END AS status,
                    fp.external_reference AS reference,
                    fp.external_reference,
                    fp.recorded_by,
                    fp.reversed_by,
                    fp.reversed_at,
                    fp.reversal_reason,
                    fp.created_at,
                    fp.updated_at
                FROM public.finance_payments fp
                JOIN public.finance_accounts fa
                  ON fa.id = fp.finance_account_id
                JOIN public.registrations r
                  ON r.id = fa.registration_id
                LEFT JOIN public.finance_invoices fi
                  ON fi.id = fp.invoice_id
                WHERE r.student_number = :student_number
                ORDER BY fp.payment_date DESC, fp.created_at DESC
                """
            ),
            {"student_number": student_number},
        ).mappings().all()

    return _rows(rows)


def list_student_invoices(student_number):
    student_number = _clean_student_number(student_number)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fi.id,
                    fi.invoice_number,
                    r.student_number,
                    fi.charge_type,
                    COALESCE(fi.description, fi.notes, 'Finance charge')
                        AS description,
                    fi.total_amount AS amount,
                    fi.subtotal,
                    fi.discount_amount,
                    fi.total_amount,
                    fi.invoice_date AS date_issued,
                    fi.invoice_date,
                    fi.due_date,
                    fi.status,
                    fi.notes,
                    fi.created_by,
                    fi.created_at,
                    fi.updated_at
                FROM public.finance_invoices fi
                JOIN public.finance_accounts fa
                  ON fa.id = fi.finance_account_id
                JOIN public.registrations r
                  ON r.id = fa.registration_id
                WHERE r.student_number = :student_number
                ORDER BY fi.invoice_date DESC, fi.created_at DESC
                """
            ),
            {"student_number": student_number},
        ).mappings().all()

    return _rows(rows)


def list_student_receipts(student_number):
    student_number = _clean_student_number(student_number)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fr.id,
                    fr.receipt_number,
                    r.student_number,
                    fp.payment_reference AS payment_id,
                    fp.payment_reference,
                    fp.amount,
                    fp.payment_date,
                    fr.pdf_path,
                    fr.issued_by AS created_by,
                    fr.issued_by,
                    fr.issued_at,
                    fr.created_at
                FROM public.finance_receipts fr
                JOIN public.finance_payments fp
                  ON fp.id = fr.payment_id
                JOIN public.finance_accounts fa
                  ON fa.id = fp.finance_account_id
                JOIN public.registrations r
                  ON r.id = fa.registration_id
                WHERE r.student_number = :student_number
                ORDER BY fr.issued_at DESC, fr.created_at DESC
                """
            ),
            {"student_number": student_number},
        ).mappings().all()

    return _rows(rows)


def get_latest_payment_plan(student_number):
    student_number = _clean_student_number(student_number)

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    fpp.id,
                    r.student_number,
                    COUNT(fppi.id) AS plan_months,
                    fpp.total_plan_amount AS total_fee,
                    0::numeric AS deposit,
                    COALESCE(AVG(fppi.amount_due), 0) AS monthly_instalment,
                    fpp.start_date,
                    MIN(fppi.due_date)
                        FILTER (WHERE lower(fppi.status) = 'pending')
                        AS next_due_date,
                    COUNT(fppi.id)
                        FILTER (WHERE lower(fppi.status) = 'pending')
                        AS remaining_months,
                    0::numeric AS interest_rate,
                    fpp.status,
                    fpp.plan_name,
                    fpp.notes,
                    fpp.created_by,
                    fpp.created_at,
                    fpp.updated_at
                FROM public.finance_payment_plans fpp
                JOIN public.finance_accounts fa
                  ON fa.id = fpp.finance_account_id
                JOIN public.registrations r
                  ON r.id = fa.registration_id
                LEFT JOIN public.finance_payment_plan_installments fppi
                  ON fppi.payment_plan_id = fpp.id
                WHERE r.student_number = :student_number
                GROUP BY fpp.id, r.student_number
                ORDER BY fpp.created_at DESC
                LIMIT 1
                """
            ),
            {"student_number": student_number},
        ).mappings().first()

    return _dict(row)


def list_statements(student_number):
    student_number = _clean_student_number(student_number)

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fsd.id,
                    COALESCE(
                        fsd.statement_number,
                        'STM-' || fsd.statement_year || '-'
                        || lpad(fsd.statement_month::text, 2, '0')
                        || '-' || r.student_number
                    ) AS statement_number,
                    r.student_number,
                    fsd.statement_year::text || '-'
                        || lpad(fsd.statement_month::text, 2, '0') AS period,
                    fsd.opening_balance,
                    fsd.total_charges AS charges,
                    fsd.total_payments AS payments,
                    fsd.credits,
                    fsd.sponsor_covered,
                    fsd.closing_balance,
                    fsd.amount_due,
                    fsd.pdf_path,
                    fsd.generated_by,
                    fsd.generated_at,
                    fsd.delivery_status,
                    fsd.sent_at,
                    fsd.created_at,
                    fsd.updated_at
                FROM public.finance_statement_deliveries fsd
                JOIN public.finance_accounts fa
                  ON fa.id = fsd.finance_account_id
                JOIN public.registrations r
                  ON r.id = fa.registration_id
                WHERE r.student_number = :student_number
                ORDER BY
                    fsd.statement_year DESC,
                    fsd.statement_month DESC,
                    fsd.created_at DESC
                """
            ),
            {"student_number": student_number},
        ).mappings().all()

    return _rows(rows)


def get_student_finance(student_number):
    student_number = _clean_student_number(student_number)
    _ensure_account(student_number)

    with engine.connect() as connection:
        identity = _identity(connection, student_number)
        if not identity:
            raise ValueError("Student finance account was not found.")

        summary = _summary(
            connection,
            identity["finance_account_id"],
            student_number,
        )

        sponsors = connection.execute(
            text(
                """
                SELECT
                    s.sponsor_id,
                    s.sponsor_name,
                    s.sponsor_type,
                    s.status,
                    ssa.amount_covered,
                    ssa.reference,
                    ssa.created_at
                FROM public.student_sponsor_allocations ssa
                JOIN public.sponsors s
                  ON s.sponsor_id = ssa.sponsor_id
                WHERE ssa.student_number = :student_number
                ORDER BY ssa.created_at DESC
                """
            ),
            {"student_number": student_number},
        ).mappings().all()

    return {
        "student": {
            "student_number": student_number,
            "first_name": identity["first_name"],
            "middle_name": identity["middle_name"],
            "last_name": identity["last_name"],
            "email": identity["email"],
            "cell_number": identity["cell_number"],
            "course_code": identity["course_code"],
            "cycle": identity["cycle"],
            "registration_status": identity["registration_status"],
        },
        "account": {
            "finance_account_id": str(identity["finance_account_id"]),
            "tuition_fee": float(_money(identity["tuition_fee"])),
            "other_fees": float(_money(identity["other_fees"])),
            "funding_type": identity["funding_type"],
            "account_status": identity["account_status"],
            "total_charges": float(summary["total_charges"]),
            "payments_total": float(summary["total_payments"]),
            "sponsor_amount_covered": float(summary["sponsor_covered"]),
            "outstanding_balance": float(summary["outstanding_balance"]),
        },
        "payments": list_student_payments(student_number),
        "invoices": list_student_invoices(student_number),
        "receipts": list_student_receipts(student_number),
        "payment_plan": get_latest_payment_plan(student_number),
        "sponsors": _rows(sponsors),
        "statements": list_statements(student_number),
    }


def create_charge(*args, **kwargs):
    actor = _actor(args, kwargs, 0)
    student_number = _clean_student_number(
        _pick(args, kwargs, 1, "student_number", "studentNumber")
    )
    charge_type = str(
        _pick(args, kwargs, 2, "charge_type", "chargeType", default="Other")
        or "Other"
    ).strip()
    amount = _money(_pick(args, kwargs, 3, "amount"))
    description = str(
        _pick(args, kwargs, 4, "description", default=charge_type) or charge_type
    ).strip()
    due_date = _pick(args, kwargs, 5, "due_date", "dueDate", default=None)

    if amount <= ZERO:
        raise ValueError("Charge amount must be greater than zero.")

    _ensure_account(student_number)
    invoice_number = _next_reference("INV")

    with engine.begin() as connection:
        identity = _identity(connection, student_number)
        if not identity:
            raise ValueError("Finance account was not found.")

        invoice = connection.execute(
            text(
                """
                INSERT INTO public.finance_invoices (
                    finance_account_id,
                    invoice_number,
                    invoice_date,
                    due_date,
                    subtotal,
                    discount_amount,
                    total_amount,
                    status,
                    notes,
                    created_by,
                    charge_type,
                    description
                )
                VALUES (
                    :account_id,
                    :invoice_number,
                    CURRENT_DATE,
                    :due_date,
                    :amount,
                    0,
                    :amount,
                    'Issued',
                    :description,
                    :actor,
                    :charge_type,
                    :description
                )
                RETURNING *
                """
            ),
            {
                "account_id": identity["finance_account_id"],
                "invoice_number": invoice_number,
                "due_date": due_date,
                "amount": amount,
                "description": description,
                "actor": actor,
                "charge_type": charge_type,
            },
        ).mappings().first()

        connection.execute(
            text(
                """
                INSERT INTO public.finance_invoice_items (
                    invoice_id,
                    description,
                    quantity,
                    unit_price,
                    line_total
                )
                VALUES (:invoice_id, :description, 1, :amount, :amount)
                """
            ),
            {
                "invoice_id": invoice["id"],
                "description": description,
                "amount": amount,
            },
        )

        if charge_type.lower() in {"tuition", "tuition fee"}:
            connection.execute(
                text(
                    """
                    UPDATE public.finance_accounts
                    SET tuition_fee = tuition_fee + :amount,
                        updated_at = NOW()
                    WHERE id = :account_id
                    """
                ),
                {"amount": amount, "account_id": identity["finance_account_id"]},
            )
        else:
            connection.execute(
                text(
                    """
                    UPDATE public.finance_accounts
                    SET other_fees = other_fees + :amount,
                        updated_at = NOW()
                    WHERE id = :account_id
                    """
                ),
                {"amount": amount, "account_id": identity["finance_account_id"]},
            )

    result = _dict(invoice)
    result["invoice_number"] = invoice_number

    _audit(
        actor_staff_code=actor,
        action_code="FINANCE_CHARGE_CREATED",
        entity_type="FINANCE_INVOICE",
        entity_id=invoice["id"],
        description=f"Finance charge created for {student_number}.",
        after_data=result,
        metadata={"student_number": student_number},
    )

    return result


def record_payment(*args, **kwargs):
    actor = _actor(args, kwargs, 0)
    student_number = _clean_student_number(
        _pick(args, kwargs, 1, "student_number", "studentNumber")
    )
    amount = _money(_pick(args, kwargs, 2, "amount"))
    method = str(
        _pick(args, kwargs, 3, "method", "payment_method", default="Other")
        or "Other"
    ).strip()
    reference = _pick(
        args, kwargs, 4, "reference", "external_reference", default=None
    )
    invoice_number = _pick(
        args, kwargs, 5, "invoice_number", "invoiceNumber", default=None
    )

    if amount <= ZERO:
        raise ValueError("Payment amount must be greater than zero.")

    _ensure_account(student_number)
    payment_reference = _next_reference("PAY")
    receipt_number = _next_reference("RCT")

    with engine.begin() as connection:
        identity = _identity(connection, student_number)
        if not identity:
            raise ValueError("Finance account was not found.")

        summary = _summary(
            connection,
            identity["finance_account_id"],
            student_number,
        )

        if amount > summary["outstanding_balance"]:
            raise ValueError(
                "Payment amount cannot exceed the outstanding balance."
            )

        invoice_id = None

        if invoice_number:
            found = connection.execute(
                text(
                    """
                    SELECT id
                    FROM public.finance_invoices
                    WHERE finance_account_id = :account_id
                      AND invoice_number = :invoice_number
                    LIMIT 1
                    """
                ),
                {
                    "account_id": identity["finance_account_id"],
                    "invoice_number": str(invoice_number).strip(),
                },
            ).first()
            if found:
                invoice_id = found[0]
        else:
            found = connection.execute(
                text(
                    """
                    SELECT id
                    FROM public.finance_invoices
                    WHERE finance_account_id = :account_id
                      AND lower(status)
                          NOT IN ('paid','cancelled','void','reversed')
                    ORDER BY invoice_date, created_at
                    LIMIT 1
                    """
                ),
                {"account_id": identity["finance_account_id"]},
            ).first()
            if found:
                invoice_id = found[0]

        payment = connection.execute(
            text(
                """
                INSERT INTO public.finance_payments (
                    finance_account_id,
                    invoice_id,
                    payment_reference,
                    payment_date,
                    amount,
                    payment_method,
                    external_reference,
                    status,
                    recorded_by,
                    is_reversed
                )
                VALUES (
                    :account_id,
                    :invoice_id,
                    :payment_reference,
                    CURRENT_DATE,
                    :amount,
                    :method,
                    :reference,
                    'Completed',
                    :actor,
                    FALSE
                )
                RETURNING *
                """
            ),
            {
                "account_id": identity["finance_account_id"],
                "invoice_id": invoice_id,
                "payment_reference": payment_reference,
                "amount": amount,
                "method": method,
                "reference": str(reference).strip() if reference else None,
                "actor": actor,
            },
        ).mappings().first()

        receipt = connection.execute(
            text(
                """
                INSERT INTO public.finance_receipts (
                    payment_id,
                    receipt_number,
                    issued_at,
                    issued_by
                )
                VALUES (:payment_id, :receipt_number, NOW(), :actor)
                RETURNING *
                """
            ),
            {
                "payment_id": payment["id"],
                "receipt_number": receipt_number,
                "actor": actor,
            },
        ).mappings().first()

        if invoice_id:
            total = _money(
                connection.execute(
                    text(
                        """
                        SELECT total_amount
                        FROM public.finance_invoices
                        WHERE id = :invoice_id
                        """
                    ),
                    {"invoice_id": invoice_id},
                ).scalar_one()
            )
            paid = _money(
                connection.execute(
                    text(
                        """
                        SELECT COALESCE(SUM(amount), 0)
                        FROM public.finance_payments
                        WHERE invoice_id = :invoice_id
                          AND lower(status) = 'completed'
                          AND COALESCE(is_reversed, FALSE) = FALSE
                        """
                    ),
                    {"invoice_id": invoice_id},
                ).scalar_one()
            )
            connection.execute(
                text(
                    """
                    UPDATE public.finance_invoices
                    SET status = :status,
                        updated_at = NOW()
                    WHERE id = :invoice_id
                    """
                ),
                {
                    "status": "Paid" if paid >= total else "Partially Paid",
                    "invoice_id": invoice_id,
                },
            )

    result = _dict(payment)
    result.update(
        {
            "payment_id": payment_reference,
            "payment_reference": payment_reference,
            "receipt_number": receipt_number,
            "receipt_id": str(receipt["id"]),
        }
    )

    _audit(
        actor_staff_code=actor,
        action_code="FINANCE_PAYMENT_RECORDED",
        entity_type="FINANCE_PAYMENT",
        entity_id=payment["id"],
        description=f"Payment recorded for {student_number}.",
        after_data=result,
        metadata={"student_number": student_number},
    )

    return result


def reverse_payment(*args, **kwargs):
    actor = _actor(args, kwargs, 0)
    payment_id = str(
        _pick(args, kwargs, 1, "payment_id", "payment_reference") or ""
    ).strip()
    reason = str(
        _pick(
            args,
            kwargs,
            2,
            "reason",
            "reversal_reason",
            default="Payment reversal",
        )
        or "Payment reversal"
    ).strip()

    if not payment_id:
        raise ValueError("Payment ID is required.")

    with engine.begin() as connection:
        before = connection.execute(
            text(
                """
                SELECT *
                FROM public.finance_payments
                WHERE payment_reference = :payment_id
                   OR id::text = :payment_id
                LIMIT 1
                """
            ),
            {"payment_id": payment_id},
        ).mappings().first()

        if not before:
            raise ValueError("Payment was not found.")
        if before["is_reversed"]:
            raise ValueError("Payment is already reversed.")

        row = connection.execute(
            text(
                """
                UPDATE public.finance_payments
                SET is_reversed = TRUE,
                    reversed_by = :actor,
                    reversed_at = NOW(),
                    reversal_reason = :reason,
                    notes = CONCAT_WS(
                        ' | ',
                        NULLIF(notes, ''),
                        'REVERSED: ' || :reason
                    ),
                    updated_at = NOW()
                WHERE id = :id
                RETURNING *
                """
            ),
            {
                "actor": actor,
                "reason": reason,
                "id": before["id"],
            },
        ).mappings().first()

        if before["invoice_id"]:
            connection.execute(
                text(
                    """
                    UPDATE public.finance_invoices
                    SET status = 'Issued',
                        updated_at = NOW()
                    WHERE id = :invoice_id
                    """
                ),
                {"invoice_id": before["invoice_id"]},
            )

    result = _dict(row)
    result["status"] = "Reversed"
    result["payment_id"] = row["payment_reference"]

    _audit(
        actor_staff_code=actor,
        action_code="FINANCE_PAYMENT_REVERSED",
        entity_type="FINANCE_PAYMENT",
        entity_id=row["id"],
        description="Finance payment reversed.",
        before_data=_dict(before),
        after_data=result,
    )

    return result


def apply_credit(*args, **kwargs):
    actor = _actor(args, kwargs, 0)
    student_number = _clean_student_number(
        _pick(args, kwargs, 1, "student_number", "studentNumber")
    )
    amount = _money(_pick(args, kwargs, 2, "amount"))
    reason = str(
        _pick(
            args,
            kwargs,
            3,
            "reason",
            "description",
            default="Credit adjustment",
        )
        or "Credit adjustment"
    ).strip()

    if amount <= ZERO:
        raise ValueError("Credit amount must be greater than zero.")

    _ensure_account(student_number)
    credit_number = _next_reference("CRN")

    with engine.begin() as connection:
        identity = _identity(connection, student_number)
        summary = _summary(
            connection,
            identity["finance_account_id"],
            student_number,
        )

        if amount > summary["outstanding_balance"]:
            raise ValueError("Credit cannot exceed the outstanding balance.")

        row = connection.execute(
            text(
                """
                INSERT INTO public.finance_invoices (
                    finance_account_id,
                    invoice_number,
                    invoice_date,
                    due_date,
                    subtotal,
                    discount_amount,
                    total_amount,
                    status,
                    notes,
                    created_by,
                    charge_type,
                    description
                )
                VALUES (
                    :account_id,
                    :invoice_number,
                    CURRENT_DATE,
                    CURRENT_DATE,
                    :negative_amount,
                    0,
                    :negative_amount,
                    'Issued',
                    :notes,
                    :actor,
                    'Credit',
                    :description
                )
                RETURNING *
                """
            ),
            {
                "account_id": identity["finance_account_id"],
                "invoice_number": credit_number,
                "negative_amount": -amount,
                "notes": "CREDIT ADJUSTMENT: " + reason,
                "actor": actor,
                "description": reason,
            },
        ).mappings().first()

    result = _dict(row)
    result["credit_amount"] = float(amount)
    return result


def create_payment_plan(*args, **kwargs):
    actor = _actor(args, kwargs, 0)
    student_number = _clean_student_number(
        _pick(args, kwargs, 1, "student_number", "studentNumber")
    )
    months = int(
        _pick(args, kwargs, 2, "plan_months", "months", default=0) or 0
    )
    deposit = _money(_pick(args, kwargs, 3, "deposit", default=0))
    interest = _money(
        _pick(args, kwargs, 4, "interest_rate", "interest", default=0)
    )
    start_date = _pick(
        args, kwargs, 5, "start_date", "startDate", default=date.today()
    )

    if months <= 0:
        raise ValueError("Plan months must be greater than zero.")

    _ensure_account(student_number)

    with engine.begin() as connection:
        identity = _identity(connection, student_number)
        summary = _summary(
            connection,
            identity["finance_account_id"],
            student_number,
        )

        outstanding = summary["outstanding_balance"]
        if outstanding <= ZERO:
            raise ValueError("Student has no outstanding balance.")

        financed = outstanding - deposit
        if financed <= ZERO:
            raise ValueError(
                "Deposit must be less than the outstanding balance."
            )

        if interest > ZERO:
            financed = (
                financed * (Decimal("1") + interest / Decimal("100"))
            ).quantize(CENT)

        monthly = (financed / Decimal(months)).quantize(CENT)

        plan = connection.execute(
            text(
                """
                INSERT INTO public.finance_payment_plans (
                    finance_account_id,
                    plan_name,
                    start_date,
                    end_date,
                    total_plan_amount,
                    status,
                    notes,
                    created_by
                )
                VALUES (
                    :account_id,
                    'Outstanding Balance Plan',
                    :start_date,
                    (
                        CAST(:start_date AS date)
                        + (:months || ' months')::interval
                    )::date,
                    :total_amount,
                    'Active',
                    :notes,
                    :actor
                )
                RETURNING *
                """
            ),
            {
                "account_id": identity["finance_account_id"],
                "start_date": start_date,
                "months": months,
                "total_amount": financed,
                "notes": f"Deposit: R{deposit}; Interest: {interest}%",
                "actor": actor,
            },
        ).mappings().first()

        remaining = financed

        for number in range(1, months + 1):
            installment = monthly if number < months else remaining

            connection.execute(
                text(
                    """
                    INSERT INTO public.finance_payment_plan_installments (
                        payment_plan_id,
                        installment_number,
                        due_date,
                        amount_due,
                        status
                    )
                    VALUES (
                        :plan_id,
                        :number,
                        (
                            CAST(:start_date AS date)
                            + (:number || ' months')::interval
                        )::date,
                        :amount_due,
                        'Pending'
                    )
                    """
                ),
                {
                    "plan_id": plan["id"],
                    "number": number,
                    "start_date": start_date,
                    "amount_due": installment,
                },
            )

            remaining = (remaining - installment).quantize(CENT)

    result = _dict(plan)
    result.update(
        {
            "student_number": student_number,
            "plan_months": months,
            "total_fee": float(financed),
            "deposit": float(deposit),
            "monthly_instalment": float(monthly),
            "monthlyInstalment": float(monthly),
            "remaining_months": months,
            "interest_rate": float(interest),
        }
    )
    return result


def create_statement(*args, **kwargs):
    actor = _actor(args, kwargs, 0)
    student_number = _clean_student_number(
        _pick(args, kwargs, 1, "student_number", "studentNumber")
    )
    period = _pick(args, kwargs, 2, "period", default=None)

    if period:
        try:
            parsed = datetime.strptime(str(period), "%Y-%m")
            year, month = parsed.year, parsed.month
        except ValueError:
            today = date.today()
            year, month = today.year, today.month
    else:
        today = date.today()
        year, month = today.year, today.month

    _ensure_account(student_number)

    document = _invoke_generator(
        generate_student_statement,
        {
            "student_number": student_number,
            "statement_year": year,
            "statement_month": month,
        },
    )

    pdf_path = document.get("pdf_path")

    with engine.begin() as connection:
        identity = _identity(connection, student_number)
        summary = _summary(
            connection,
            identity["finance_account_id"],
            student_number,
        )

        first_day = date(year, month, 1)
        next_month = (
            date(year + 1, 1, 1)
            if month == 12
            else date(year, month + 1, 1)
        )
        period_end = next_month - timedelta(days=1)
        statement_number = f"STM-{year}-{month:02d}-{student_number}"

        existing = connection.execute(
            text(
                """
                SELECT id
                FROM public.finance_statement_deliveries
                WHERE finance_account_id = :account_id
                  AND statement_year = :year
                  AND statement_month = :month
                ORDER BY created_at DESC
                LIMIT 1
                """
            ),
            {
                "account_id": identity["finance_account_id"],
                "year": year,
                "month": month,
            },
        ).first()

        params = {
            "account_id": identity["finance_account_id"],
            "year": year,
            "month": month,
            "period_start": first_day,
            "period_end": period_end,
            "charges": summary["total_charges"],
            "payments": summary["total_payments"],
            "closing": summary["outstanding_balance"],
            "sponsor": summary["sponsor_covered"],
            "amount_due": summary["outstanding_balance"],
            "pdf_path": pdf_path,
            "statement_number": statement_number,
            "actor": actor,
        }

        if existing:
            row = connection.execute(
                text(
                    """
                    UPDATE public.finance_statement_deliveries
                    SET period_start = :period_start,
                        period_end = :period_end,
                        total_charges = :charges,
                        total_payments = :payments,
                        closing_balance = :closing,
                        sponsor_covered = :sponsor,
                        amount_due = :amount_due,
                        pdf_path = :pdf_path,
                        statement_number = :statement_number,
                        generated_by = :actor,
                        generated_at = NOW(),
                        delivery_status = 'Generated',
                        updated_at = NOW()
                    WHERE id = :id
                    RETURNING *
                    """
                ),
                {**params, "id": existing[0]},
            ).mappings().first()
        else:
            row = connection.execute(
                text(
                    """
                    INSERT INTO public.finance_statement_deliveries (
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
                        delivery_status,
                        generated_at,
                        statement_number,
                        generated_by,
                        sponsor_covered,
                        amount_due
                    )
                    VALUES (
                        :account_id,
                        :year,
                        :month,
                        :period_start,
                        :period_end,
                        0,
                        :charges,
                        :payments,
                        :closing,
                        TRUE,
                        :pdf_path,
                        'Generated',
                        NOW(),
                        :statement_number,
                        :actor,
                        :sponsor,
                        :amount_due
                    )
                    RETURNING *
                    """
                ),
                params,
            ).mappings().first()

    result = _dict(row)
    result["student_number"] = student_number
    return result


def run_finance_report(*args, **kwargs):
    report_type = str(
        _pick(
            args,
            kwargs,
            0,
            "report_type",
            "report_code",
            "report",
            default="summary",
        )
        or "summary"
    ).strip().lower().replace("_", "-")

    if report_type in {
        "summary",
        "collection-rate",
        "collectionrate",
        "monthly-income",
        "monthlyincome",
    }:
        return {
            "report_type": report_type,
            "summary": get_finance_dashboard(),
        }

    if report_type in {
        "student-balances",
        "studentbalances",
        "outstanding-fees",
        "outstandingfees",
        "age-analysis",
        "ageanalysis",
    }:
        return {
            "report_type": report_type,
            "students": search_finance_students(query="", limit=200),
        }

    if report_type in {"sponsors", "sponsor-report", "sponsorreport"}:
        with engine.connect() as connection:
            rows = connection.execute(
                text("SELECT * FROM public.sponsors ORDER BY sponsor_name")
            ).mappings().all()
        return {"report_type": report_type, "sponsors": _rows(rows)}

    return {
        "report_type": report_type,
        "summary": get_finance_dashboard(),
    }


def _lookup_document_owner(*args, **kwargs):
    document_type = str(
        _pick(args, kwargs, 0, "document_type", "kind", default="") or ""
    ).strip().lower()
    reference = str(
        _pick(
            args,
            kwargs,
            1,
            "reference",
            "identifier",
            "document_id",
            default="",
        )
        or ""
    ).strip()

    sql = None

    if document_type == "invoice":
        sql = """
            SELECT r.student_number
            FROM public.finance_invoices fi
            JOIN public.finance_accounts fa ON fa.id = fi.finance_account_id
            JOIN public.registrations r ON r.id = fa.registration_id
            WHERE fi.invoice_number = :reference
            LIMIT 1
        """
    elif document_type == "receipt":
        sql = """
            SELECT r.student_number
            FROM public.finance_receipts fr
            JOIN public.finance_payments fp ON fp.id = fr.payment_id
            JOIN public.finance_accounts fa ON fa.id = fp.finance_account_id
            JOIN public.registrations r ON r.id = fa.registration_id
            WHERE fr.receipt_number = :reference
            LIMIT 1
        """
    elif document_type in {"payment-plan", "payment_plan", "plan"}:
        sql = """
            SELECT r.student_number
            FROM public.finance_payment_plans fpp
            JOIN public.finance_accounts fa ON fa.id = fpp.finance_account_id
            JOIN public.registrations r ON r.id = fa.registration_id
            WHERE fpp.id::text = :reference
            LIMIT 1
        """

    if not sql:
        return None

    with engine.connect() as connection:
        row = connection.execute(
            text(sql),
            {"reference": reference},
        ).first()

    return row[0] if row else None


def generate_finance_document(*args, **kwargs):
    document_type = str(
        _pick(args, kwargs, 0, "document_type", "kind", default="") or ""
    ).strip().lower()
    reference = _pick(
        args,
        kwargs,
        1,
        "reference",
        "identifier",
        "document_id",
        default=None,
    )
    student_number = _pick(
        args,
        kwargs,
        2,
        "student_number",
        "studentNumber",
        default=None,
    )

    if (
        not student_number
        and reference
        and document_type
        in {"invoice", "receipt", "payment-plan", "payment_plan", "plan"}
    ):
        student_number = _lookup_document_owner(document_type, reference)

    if student_number:
        student_number = _clean_student_number(student_number)

    if document_type == "invoice":
        return _invoke_generator(
            generate_student_invoice,
            {
                "student_number": student_number,
                "invoice_number": str(reference),
            },
        )

    if document_type == "receipt":
        return _invoke_generator(
            generate_student_receipt,
            {
                "student_number": student_number,
                "receipt_number": str(reference),
            },
        )

    if document_type in {"payment-plan", "payment_plan", "plan"}:
        return _invoke_generator(
            generate_student_payment_plan,
            {
                "student_number": student_number,
                "payment_plan_id": str(reference),
            },
        )

    if document_type == "statement":
        if not student_number:
            student_number = _clean_student_number(reference)
        today = date.today()
        return _invoke_generator(
            generate_student_statement,
            {
                "student_number": student_number,
                "statement_year": today.year,
                "statement_month": today.month,
            },
        )

    raise ValueError("Unsupported finance document type.")
