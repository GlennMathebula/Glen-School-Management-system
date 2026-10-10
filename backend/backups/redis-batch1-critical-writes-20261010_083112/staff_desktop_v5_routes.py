from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from app.database import engine
from app.services.academic_management_service import (
    get_cycle_courses,
    set_cycle_course_status,
)
from app.services.staff_auth_service import hash_secret
from app.services.staff_audit_service import create_staff_audit_log
from app.services.staff_permission_service import require_permission
from app.staff_admin_guard import require_admin_staff
from app.services.student_card_service import (
    generate_student_card_document,
    get_student_card_data,
)


router = APIRouter(
    prefix="/api/staff/desktop-v5",
    tags=["Staff Desktop V5 Operations"],
)


APPROVED_ROLES = {
    "ADMIN",
    "PRINCIPAL",
    "HR",
    "CFO",
    "FINANCIAL_OFFICER",
    "FACILITATOR",
    "ASSESSOR",
    "MODERATOR",
}


def _clean(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _uuid(value, label):
    try:
        return str(UUID(str(value)))
    except Exception as error:
        raise ValueError(f"Invalid {label}.") from error


def _audit(
    *,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    description: str,
    after_data: dict | None = None,
):
    try:
        create_staff_audit_log(
            actor_staff_code=actor,
            action_code=action,
            module_code="STAFF_DESKTOP_V5",
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            before_data=None,
            after_data=after_data,
            metadata={},
        )
    except Exception as error:
        print(f"WARNING: V5 audit failed: {error}")


def _next_employee_number(connection) -> str:
    year = date.today().year

    rows = connection.execute(
        text(
            """
            SELECT employee_number
            FROM public.employees
            WHERE employee_number LIKE :prefix
            """
        ),
        {"prefix": f"EMP{year}%"},
    ).scalars().all()

    highest = 0

    for value in rows:
        raw = str(value or "")
        tail = raw.replace(
            f"EMP{year}",
            "",
            1,
        )

        if tail.isdigit():
            highest = max(
                highest,
                int(tail),
            )

    return f"EMP{year}{highest + 1:03d}"


class StaffMemberCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(default=None, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    phone_number: str | None = Field(default=None, max_length=50)
    national_id: str | None = Field(default=None, max_length=50)
    job_title: str = Field(min_length=1, max_length=200)
    department: str | None = Field(default=None, max_length=150)
    employment_type: str | None = Field(default=None, max_length=80)
    start_date: date | None = None
    staff_code: str = Field(min_length=3, max_length=30)
    role_code: str = Field(min_length=2, max_length=50)
    temporary_password: str = Field(min_length=8, max_length=255)
    temporary_pin: str = Field(pattern=r"^\d{5}$")


@router.post("/staff-members")
def create_staff_member(
    payload: StaffMemberCreate,
    current_staff: dict = Depends(
        require_permission("MANAGE_STAFF_ACCOUNTS")
    ),
):
    staff_code = payload.staff_code.strip().upper()
    role_code = payload.role_code.strip().upper()
    email = payload.email.strip().lower()

    if role_code not in APPROVED_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Invalid Glen Moniques staff role.",
        )

    try:
        with engine.begin() as connection:
            role = connection.execute(
                text(
                    """
                    SELECT role_code
                    FROM public.staff_roles
                    WHERE role_code = :role_code
                    LIMIT 1
                    """
                ),
                {"role_code": role_code},
            ).scalar()

            if not role:
                raise ValueError(
                    "Staff role was not found."
                )

            duplicate_account = connection.execute(
                text(
                    """
                    SELECT 1
                    FROM public.staff_accounts
                    WHERE upper(staff_code) = :staff_code
                    LIMIT 1
                    """
                ),
                {
                    "staff_code": staff_code,
                },
            ).first()

            if duplicate_account:
                raise ValueError(
                    "A staff account already exists for this staff code."
                )

            duplicate_employee = connection.execute(
                text(
                    """
                    SELECT employee_number
                    FROM public.employees
                    WHERE lower(email) = :email
                    LIMIT 1
                    """
                ),
                {
                    "email": email,
                },
            ).scalar()

            if duplicate_employee:
                raise ValueError(
                    "An employee with this email already exists. "
                    "Use Existing Employee Account instead."
                )

            employee_number = _next_employee_number(
                connection
            )

            employee = connection.execute(
                text(
                    """
                    INSERT INTO public.employees (
                        employee_number,
                        first_name,
                        middle_name,
                        last_name,
                        national_id,
                        email,
                        phone_number,
                        job_title,
                        department,
                        employment_type,
                        employment_status,
                        start_date,
                        requires_system_access,
                        created_by
                    )
                    VALUES (
                        :employee_number,
                        :first_name,
                        :middle_name,
                        :last_name,
                        :national_id,
                        :email,
                        :phone_number,
                        :job_title,
                        :department,
                        :employment_type,
                        'Active',
                        :start_date,
                        TRUE,
                        :actor
                    )
                    RETURNING *
                    """
                ),
                {
                    "employee_number": employee_number,
                    "first_name": payload.first_name.strip(),
                    "middle_name": _clean(payload.middle_name),
                    "last_name": payload.last_name.strip(),
                    "national_id": _clean(payload.national_id),
                    "email": email,
                    "phone_number": _clean(payload.phone_number),
                    "job_title": payload.job_title.strip(),
                    "department": _clean(payload.department),
                    "employment_type": _clean(payload.employment_type),
                    "start_date": payload.start_date,
                    "actor": current_staff["staff_code"],
                },
            ).mappings().one()

            account = connection.execute(
                text(
                    """
                    INSERT INTO public.staff_accounts (
                        employee_id,
                        staff_code,
                        role_code,
                        password_hash,
                        pin_hash,
                        must_change_password,
                        must_change_pin,
                        failed_login_attempts,
                        is_active,
                        credentials_issued_at
                    )
                    VALUES (
                        :employee_id,
                        :staff_code,
                        :role_code,
                        :password_hash,
                        :pin_hash,
                        TRUE,
                        TRUE,
                        0,
                        TRUE,
                        NOW()
                    )
                    RETURNING
                        id,
                        employee_id,
                        staff_code,
                        role_code,
                        is_active,
                        must_change_password,
                        must_change_pin,
                        credentials_issued_at
                    """
                ),
                {
                    "employee_id": employee["id"],
                    "staff_code": staff_code,
                    "role_code": role_code,
                    "password_hash": hash_secret(
                        payload.temporary_password
                    ),
                    "pin_hash": hash_secret(
                        payload.temporary_pin
                    ),
                },
            ).mappings().one()

        record = {
            "employee": dict(employee),
            "staff_account": dict(account),
        }

        _audit(
            actor=current_staff["staff_code"],
            action="STAFF_MEMBER_CREATED",
            entity_type="STAFF_ACCOUNT",
            entity_id=staff_code,
            description="Employee and staff account created.",
            after_data=record,
        )

        return {
            "success": True,
            **record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


class CycleCourseSet(BaseModel):
    cycle_code: str
    course_code: str
    is_active: bool = True


@router.get("/cycle-courses")
def cycle_courses_safe(
    cycle_code: str = Query(...),
    current_staff: dict = Depends(
        require_permission("MANAGE_ACADEMIC_STRUCTURE")
    ),
):
    try:
        records = get_cycle_courses(
            cycle_code=cycle_code
        )

        return {
            "success": True,
            "cycle_code": cycle_code,
            "count": len(records),
            "courses": records,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.post("/cycle-course-status")
def set_cycle_course_safe(
    payload: CycleCourseSet,
    current_staff: dict = Depends(
        require_permission("MANAGE_ACADEMIC_STRUCTURE")
    ),
):
    try:
        record = set_cycle_course_status(
            actor_staff_code=current_staff["staff_code"],
            cycle_code=payload.cycle_code,
            course_code=payload.course_code,
            is_active=payload.is_active,
        )

        return {
            "success": True,
            "cycle_course": record,
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get("/registration-options")
def registration_options(
    cycle_code: str | None = None,
    course_code: str | None = None,
    assessment_type: str | None = None,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    clauses = [
        "r.registration_status NOT IN ('Cancelled','Withdrawn')"
    ]
    params = {}

    if _clean(cycle_code):
        clauses.append(
            "r.cycle = CAST(:cycle_code AS varchar)"
        )
        params["cycle_code"] = _clean(cycle_code)

    if _clean(course_code):
        clauses.append(
            "r.course_code = CAST(:course_code AS varchar)"
        )
        params["course_code"] = _clean(course_code)

    if _clean(assessment_type):
        clauses.append(
            "c.assessment_type = CAST(:assessment_type AS varchar)"
        )
        params["assessment_type"] = _clean(
            assessment_type
        )

    sql = f"""
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.cycle AS cycle_code,
            r.registration_status,
            r.eisa_eligible,
            c.course_name,
            c.assessment_type,
            CONCAT_WS(
                ' ',
                a.first_name,
                a.middle_name,
                a.last_name
            ) AS learner_name
        FROM public.registrations r
        JOIN public.applications a
            ON a.id = r.application_id
        JOIN public.courses c
            ON c.course_code = r.course_code
        WHERE {" AND ".join(clauses)}
        ORDER BY
            a.last_name,
            a.first_name,
            r.student_number
    """

    with engine.connect() as connection:
        rows = connection.execute(
            text(sql),
            params,
        ).mappings().all()

    return {
        "success": True,
        "registrations": [
            dict(row)
            for row in rows
        ],
    }


@router.get("/assessment-options/{registration_id}")
def assessment_options(
    registration_id: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    registration_id = _uuid(
        registration_id,
        "registration ID",
    )

    with engine.connect() as connection:
        marks = connection.execute(
            text(
                """
                SELECT
                    mk.id,
                    m.module_code,
                    m.module_name,
                    mk.attempt_number,
                    mk.mark,
                    mk.result,
                    mk.status
                FROM public.marks mk
                JOIN public.module_registrations mr
                    ON mr.id = mk.module_registration_id
                JOIN public.modules m
                    ON m.id = mr.module_id
                WHERE mr.registration_id =
                    CAST(:registration_id AS uuid)
                ORDER BY m.module_code, mk.attempt_number DESC
                """
            ),
            {"registration_id": registration_id},
        ).mappings().all()

        summatives = connection.execute(
            text(
                """
                SELECT
                    id,
                    assessment_type,
                    attempt_number,
                    mark,
                    result,
                    status,
                    assessment_date
                FROM public.summative_assessments
                WHERE registration_id =
                    CAST(:registration_id AS uuid)
                ORDER BY
                    assessment_type,
                    attempt_number DESC
                """
            ),
            {"registration_id": registration_id},
        ).mappings().all()

    return {
        "success": True,
        "marks": [dict(row) for row in marks],
        "summatives": [dict(row) for row in summatives],
    }


@router.get("/class-modules")
def class_modules(
    class_code: str = Query(...),
    current_staff: dict = Depends(
        require_permission("MANAGE_LEARNING_RESOURCES")
    ),
):
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    m.id AS module_id,
                    m.module_code,
                    m.module_name,
                    m.module_type,
                    m.course_code
                FROM public.classes cl
                JOIN public.modules m
                    ON m.course_code = cl.course_code
                WHERE cl.class_code = :class_code
                ORDER BY
                    CASE
                        WHEN m.module_type='KM' THEN 1
                        WHEN m.module_type='PM' THEN 2
                        WHEN m.module_type='WM' THEN 3
                        ELSE 4
                    END,
                    m.module_code
                """
            ),
            {"class_code": class_code},
        ).mappings().all()

    return {
        "success": True,
        "modules": [dict(row) for row in rows],
    }


class CalendarDateCreate(BaseModel):
    calendar_date: date
    day_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_training_day: bool = True


class CalendarDateUpdate(BaseModel):
    day_type: str | None = None
    description: str | None = None
    is_training_day: bool | None = None


require_calendar = require_permission(
    "MANAGE_ACADEMIC_CALENDAR"
)


@router.get("/academic-calendar")
def academic_calendar_list(
    calendar_year: int | None = None,
    current_staff: dict = Depends(
        require_calendar
    ),
):
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.academic_calendar_dates
                WHERE (
                    CAST(:calendar_year AS integer) IS NULL
                    OR calendar_year =
                       CAST(:calendar_year AS integer)
                )
                ORDER BY calendar_date
                """
            ),
            {"calendar_year": calendar_year},
        ).mappings().all()

    return {
        "success": True,
        "dates": [dict(row) for row in rows],
    }


@router.post("/academic-calendar")
def academic_calendar_create(
    payload: CalendarDateCreate,
    current_staff: dict = Depends(
        require_calendar
    ),
):
    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.academic_calendar_dates (
                    calendar_date,
                    day_type,
                    description,
                    is_training_day,
                    source,
                    source_reference,
                    is_manual_override
                )
                VALUES (
                    :calendar_date,
                    :day_type,
                    :description,
                    :is_training_day,
                    'Staff Desktop',
                    :source_reference,
                    TRUE
                )
                ON CONFLICT (calendar_date)
                DO UPDATE SET
day_type=EXCLUDED.day_type,
                    description=EXCLUDED.description,
                    is_training_day=EXCLUDED.is_training_day,
                    source='Staff Desktop',
                    source_reference=EXCLUDED.source_reference,
                    is_manual_override=TRUE,
                    updated_at=NOW()
                RETURNING *
                """
            ),
            {
                "calendar_date": payload.calendar_date,
                "day_type": payload.day_type,
                "description": _clean(payload.description),
                "is_training_day": payload.is_training_day,
                "source_reference": current_staff["staff_code"],
            },
        ).mappings().one()

    return {
        "success": True,
        "date": dict(row),
    }


@router.patch("/academic-calendar/{calendar_id}")
def academic_calendar_update(
    calendar_id: str,
    payload: CalendarDateUpdate,
    current_staff: dict = Depends(
        require_calendar
    ),
):
    calendar_id = _uuid(
        calendar_id,
        "calendar ID",
    )

    updates = payload.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No calendar changes supplied.",
        )

    sets = []
    params = {
        "calendar_id": calendar_id,
    }

    for key in (
        "day_type",
        "description",
        "is_training_day",
    ):
        if key in updates:
            sets.append(
                f"{key} = :{key}"
            )
            params[key] = updates[key]

    sets.extend(
        [
            "source = 'Staff Desktop'",
            "source_reference = :actor",
            "is_manual_override = TRUE",
            "updated_at = NOW()",
        ]
    )

    params["actor"] = current_staff[
        "staff_code"
    ]

    with engine.begin() as connection:
        row = connection.execute(
            text(
                f"""
                UPDATE public.academic_calendar_dates
                SET {", ".join(sets)}
                WHERE id =
                    CAST(:calendar_id AS uuid)
                RETURNING *
                """
            ),
            params,
        ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Academic calendar record not found.",
        )

    return {
        "success": True,
        "date": dict(row),
    }


@router.delete("/academic-calendar/{calendar_id}")
def academic_calendar_delete(
    calendar_id: str,
    current_staff: dict = Depends(
        require_calendar
    ),
):
    del current_staff

    calendar_id = _uuid(
        calendar_id,
        "calendar ID",
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                DELETE FROM public.academic_calendar_dates
                WHERE id =
                    CAST(:calendar_id AS uuid)
                RETURNING id
                """
            ),
            {"calendar_id": calendar_id},
        ).first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Academic calendar record not found.",
        )

    return {
        "success": True,
    }


class CourseFinanceConfigSet(BaseModel):
    tuition_fee: Decimal = Field(ge=0)
    ppe_required: bool = False
    ppe_fee: Decimal = Field(default=0, ge=0)
    is_active: bool = True
    effective_from: date | None = None
    effective_to: date | None = None


class AdditionalFeeCreate(BaseModel):
    fee_name: str = Field(min_length=1, max_length=200)
    fee_code: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(ge=0)
    is_mandatory: bool = False
    is_active: bool = True
    effective_from: date | None = None
    effective_to: date | None = None
    notes: str | None = None


class FundingRuleUpdate(BaseModel):
    student_is_payer: bool
    allow_pay_later: bool
    payfast_enabled: bool
    notes: str | None = None
    is_active: bool = True


require_finance_setup = require_permission(
    "MANAGE_INVOICES"
)


@router.get("/finance-setup")
def finance_setup(
    current_staff: dict = Depends(
        require_finance_setup
    ),
):
    del current_staff

    with engine.connect() as connection:
        courses = connection.execute(
            text(
                """
                SELECT
                    c.course_code,
                    c.course_name,
                    c.qualification_type,
                    c.assessment_type,
                    c.status AS course_status,
                    f.id AS finance_config_id,
                    f.tuition_fee,
                    f.ppe_required,
                    f.ppe_fee,
                    f.is_active AS finance_active,
                    f.effective_from,
                    f.effective_to
                FROM public.courses c
                LEFT JOIN public.course_finance_config f
                    ON f.course_code = c.course_code
                ORDER BY c.course_name
                """
            )
        ).mappings().all()

        fees = connection.execute(
            text(
                """
                SELECT *
                FROM public.course_additional_fees
                ORDER BY course_code, fee_name
                """
            )
        ).mappings().all()

        rules = connection.execute(
            text(
                """
                SELECT *
                FROM public.finance_funding_rules
                ORDER BY funding_type
                """
            )
        ).mappings().all()

    return {
        "success": True,
        "courses": [dict(row) for row in courses],
        "additional_fees": [dict(row) for row in fees],
        "funding_rules": [dict(row) for row in rules],
    }


@router.put("/finance-setup/courses/{course_code}")
def finance_course_set(
    course_code: str,
    payload: CourseFinanceConfigSet,
    current_staff: dict = Depends(
        require_finance_setup
    ),
):
    del current_staff

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.course_finance_config (
                    course_code,
                    tuition_fee,
                    ppe_required,
                    ppe_fee,
                    is_active,
                    effective_from,
                    effective_to
                )
                VALUES (
                    :course_code,
                    :tuition_fee,
                    :ppe_required,
                    :ppe_fee,
                    :is_active,
                    :effective_from,
                    :effective_to
                )
                ON CONFLICT (course_code)
                DO UPDATE SET
                    tuition_fee=EXCLUDED.tuition_fee,
                    ppe_required=EXCLUDED.ppe_required,
                    ppe_fee=EXCLUDED.ppe_fee,
                    is_active=EXCLUDED.is_active,
                    effective_from=EXCLUDED.effective_from,
                    effective_to=EXCLUDED.effective_to,
                    updated_at=NOW()
                RETURNING *
                """
            ),
            {
                "course_code": course_code,
                **payload.model_dump(),
            },
        ).mappings().one()

    return {
        "success": True,
        "config": dict(row),
    }


@router.post("/finance-setup/courses/{course_code}/fees")
def finance_fee_create(
    course_code: str,
    payload: AdditionalFeeCreate,
    current_staff: dict = Depends(
        require_finance_setup
    ),
):
    del current_staff

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.course_additional_fees (
                    course_code,
                    fee_name,
                    fee_code,
                    amount,
                    is_mandatory,
                    is_active,
                    effective_from,
                    effective_to,
                    notes
                )
                VALUES (
                    :course_code,
                    :fee_name,
                    :fee_code,
                    :amount,
                    :is_mandatory,
                    :is_active,
                    :effective_from,
                    :effective_to,
                    :notes
                )
                RETURNING *
                """
            ),
            {
                "course_code": course_code,
                **payload.model_dump(),
            },
        ).mappings().one()

    return {
        "success": True,
        "fee": dict(row),
    }


@router.put("/finance-setup/funding-rules/{funding_type}")
def funding_rule_set(
    funding_type: str,
    payload: FundingRuleUpdate,
    current_staff: dict = Depends(
        require_finance_setup
    ),
):
    del current_staff

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.finance_funding_rules (
                    funding_type,
                    student_is_payer,
                    allow_pay_later,
                    payfast_enabled,
                    notes,
                    is_active
                )
                VALUES (
                    :funding_type,
                    :student_is_payer,
                    :allow_pay_later,
                    :payfast_enabled,
                    :notes,
                    :is_active
                )
                ON CONFLICT (funding_type)
                DO UPDATE SET
                    student_is_payer=EXCLUDED.student_is_payer,
                    allow_pay_later=EXCLUDED.allow_pay_later,
                    payfast_enabled=EXCLUDED.payfast_enabled,
                    notes=EXCLUDED.notes,
                    is_active=EXCLUDED.is_active,
                    updated_at=NOW()
                RETURNING *
                """
            ),
            {
                "funding_type": funding_type,
                **payload.model_dump(),
            },
        ).mappings().one()

    return {
        "success": True,
        "rule": dict(row),
    }


class FisaSittingCreate(BaseModel):
    course_code: str
    cycle_code: str | None = None
    assessment_date: date
    reporting_time: str | None = None
    start_time: str
    end_time: str
    venue: str
    assessment_centre: str | None = None
    instructions: str | None = None
    status: str = "Draft"


class FisaCandidateCreate(BaseModel):
    registration_id: str
    seat_number: int | None = Field(default=None, gt=0)
    admission_status: str = "Admitted"
    attendance_status: str = "Pending"
    notes: str | None = None


class FisaSittingStatusUpdate(BaseModel):
    status: str


class FisaCandidateUpdate(BaseModel):
    seat_number: int | None = Field(default=None, gt=0)
    admission_status: str | None = None
    attendance_status: str | None = None
    notes: str | None = None


@router.get("/fisa-sittings")
def fisa_sittings(
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fs.*,
                    c.course_name,
                    COUNT(fsc.id) AS candidate_count
                FROM public.fisa_sittings fs
                JOIN public.courses c
                    ON c.course_code = fs.course_code
                LEFT JOIN public.fisa_sitting_candidates fsc
                    ON fsc.sitting_id = fs.id
                GROUP BY fs.id, c.course_name
                ORDER BY fs.assessment_date DESC, fs.start_time
                """
            )
        ).mappings().all()

    return {
        "success": True,
        "sittings": [dict(row) for row in rows],
    }


@router.post("/fisa-sittings")
def fisa_sitting_create(
    payload: FisaSittingCreate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    course_code = payload.course_code.strip().upper()

    with engine.begin() as connection:
        course = connection.execute(
            text(
                """
                SELECT course_code
                FROM public.courses
                WHERE course_code = :course_code
                LIMIT 1
                """
            ),
            {"course_code": course_code},
        ).scalar()

        if not course:
            raise HTTPException(
                status_code=400,
                detail="Course not found.",
            )

        reference = (
            "FISA-"
            + datetime.now().strftime("%Y%m%d%H%M%S%f")
        )

        row = connection.execute(
            text(
                """
                INSERT INTO public.fisa_sittings (
                    sitting_reference,
                    course_code,
                    cycle_code,
                    assessment_date,
                    reporting_time,
                    start_time,
                    end_time,
                    venue,
                    assessment_centre,
                    instructions,
                    status,
                    created_by,
                    published_at,
                    completed_at
                )
                VALUES (
                    :reference,
                    :course_code,
                    :cycle_code,
                    :assessment_date,
                    CAST(:reporting_time AS time),
                    CAST(:start_time AS time),
                    CAST(:end_time AS time),
                    :venue,
                    :assessment_centre,
                    :instructions,
                    CAST(:status AS varchar),
                    :actor,
                    CASE
                        WHEN CAST(:status AS varchar)='Published'
                        THEN NOW()
                        ELSE NULL
                    END,
                    CASE
                        WHEN CAST(:status AS varchar)='Completed'
                        THEN NOW()
                        ELSE NULL
                    END
                )
                RETURNING *
                """
            ),
            {
                "reference": reference,
                "course_code": course_code,
                "cycle_code": _clean(payload.cycle_code),
                "assessment_date": payload.assessment_date,
                "reporting_time": _clean(payload.reporting_time),
                "start_time": payload.start_time,
                "end_time": payload.end_time,
                "venue": payload.venue,
                "assessment_centre": _clean(payload.assessment_centre),
                "instructions": _clean(payload.instructions),
                "status": payload.status,
                "actor": current_staff["staff_code"],
            },
        ).mappings().one()

    return {
        "success": True,
        "sitting": dict(row),
    }


@router.get("/fisa-sittings/{sitting_id}/candidates")
def fisa_candidates(
    sitting_id: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    sitting_id = _uuid(
        sitting_id,
        "FISA sitting ID",
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fsc.*,
                    r.student_number,
                    r.course_code,
                    r.cycle AS cycle_code,
                    CONCAT_WS(
                        ' ',
                        a.first_name,
                        a.middle_name,
                        a.last_name
                    ) AS learner_name
                FROM public.fisa_sitting_candidates fsc
                JOIN public.registrations r
                    ON r.id = fsc.registration_id
                JOIN public.applications a
                    ON a.id = r.application_id
                WHERE fsc.sitting_id =
                    CAST(:sitting_id AS uuid)
                ORDER BY fsc.seat_number NULLS LAST, learner_name
                """
            ),
            {"sitting_id": sitting_id},
        ).mappings().all()

    return {
        "success": True,
        "candidates": [dict(row) for row in rows],
    }


@router.post("/fisa-sittings/{sitting_id}/candidates")
def fisa_candidate_add(
    sitting_id: str,
    payload: FisaCandidateCreate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    sitting_id = _uuid(
        sitting_id,
        "FISA sitting ID",
    )

    registration_id = _uuid(
        payload.registration_id,
        "registration ID",
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                INSERT INTO public.fisa_sitting_candidates (
                    sitting_id,
                    registration_id,
                    seat_number,
                    admission_status,
                    attendance_status,
                    notes
                )
                VALUES (
                    CAST(:sitting_id AS uuid),
                    CAST(:registration_id AS uuid),
                    :seat_number,
                    CAST(:admission_status AS varchar),
                    CAST(:attendance_status AS varchar),
                    :notes
                )
                ON CONFLICT (
                    sitting_id,
                    registration_id
                )
                DO UPDATE SET
                    seat_number=EXCLUDED.seat_number,
                    admission_status=EXCLUDED.admission_status,
                    attendance_status=EXCLUDED.attendance_status,
                    notes=EXCLUDED.notes,
                    updated_at=NOW()
                RETURNING *
                """
            ),
            {
                "sitting_id": sitting_id,
                "registration_id": registration_id,
                "seat_number": payload.seat_number,
                "admission_status": payload.admission_status,
                "attendance_status": payload.attendance_status,
                "notes": _clean(payload.notes),
            },
        ).mappings().one()

    return {
        "success": True,
        "candidate": dict(row),
    }




@router.patch("/fisa-sittings/{sitting_id}/status")
def fisa_sitting_status(
    sitting_id: str,
    payload: FisaSittingStatusUpdate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    sitting_id = _uuid(
        sitting_id,
        "FISA sitting ID",
    )

    status = payload.status.strip()

    if status not in {
        "Draft",
        "Published",
        "Completed",
        "Cancelled",
    }:
        raise HTTPException(
            status_code=400,
            detail="Invalid FISA sitting status.",
        )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.fisa_sittings
                SET
                    status=CAST(:status AS varchar),
                    published_at=CASE
                        WHEN CAST(:status AS varchar)='Published'
                        THEN COALESCE(published_at,NOW())
                        ELSE published_at
                    END,
                    completed_at=CASE
                        WHEN CAST(:status AS varchar)='Completed'
                        THEN COALESCE(completed_at,NOW())
                        ELSE completed_at
                    END,
                    updated_at=NOW()
                WHERE id=CAST(:sitting_id AS uuid)
                RETURNING *
                """
            ),
            {
                "sitting_id": sitting_id,
                "status": status,
            },
        ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="FISA sitting not found.",
        )

    return {
        "success": True,
        "sitting": dict(row),
    }


@router.patch("/fisa-candidates/{candidate_id}")
def fisa_candidate_update(
    candidate_id: str,
    payload: FisaCandidateUpdate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    candidate_id = _uuid(
        candidate_id,
        "FISA candidate ID",
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.fisa_sitting_candidates
                SET
                    seat_number=COALESCE(
                        :seat_number,
                        seat_number
                    ),
                    admission_status=COALESCE(
                        CAST(:admission_status AS varchar),
                        admission_status
                    ),
                    attendance_status=COALESCE(
                        CAST(:attendance_status AS varchar),
                        attendance_status
                    ),
                    notes=COALESCE(
                        :notes,
                        notes
                    ),
                    updated_at=NOW()
                WHERE id=CAST(:candidate_id AS uuid)
                RETURNING *
                """
            ),
            {
                "candidate_id": candidate_id,
                "seat_number": payload.seat_number,
                "admission_status": _clean(
                    payload.admission_status
                ),
                "attendance_status": _clean(
                    payload.attendance_status
                ),
                "notes": _clean(
                    payload.notes
                ),
            },
        ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="FISA candidate not found.",
        )

    return {
        "success": True,
        "candidate": dict(row),
    }


class EisaResultCapture(BaseModel):
    attempt_number: int = Field(default=1, gt=0)
    mark: Decimal | None = Field(default=None, ge=0, le=100)
    result: str
    assessment_date: date
    status: str = "Draft"


@router.get("/eisa-results")
def eisa_results(
    current_staff: dict = Depends(
        require_permission("CAPTURE_EISA")
    ),
):
    del current_staff

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    r.id AS registration_id,
                    r.student_number,
                    r.course_code,
                    r.cycle AS cycle_code,
                    r.eisa_eligible,
                    c.course_name,
                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    sa.id AS assessment_id,
                    sa.attempt_number,
                    sa.mark,
                    sa.result,
                    sa.status,
                    sa.assessment_date
                FROM public.registrations r
                JOIN public.applications a
                    ON a.id = r.application_id
                JOIN public.courses c
                    ON c.course_code = r.course_code
                LEFT JOIN LATERAL (
                    SELECT *
                    FROM public.summative_assessments x
                    WHERE
                        x.registration_id = r.id
                        AND x.assessment_type='EISA'
                    ORDER BY x.attempt_number DESC
                    LIMIT 1
                ) sa ON TRUE
                WHERE c.assessment_type='FISA_PLUS_EISA'
                ORDER BY
                    a.last_name,
                    a.first_name,
                    r.student_number
                """
            )
        ).mappings().all()

    return {
        "success": True,
        "learners": [dict(row) for row in rows],
    }


@router.post("/eisa-results/{student_number}")
def eisa_result_capture(
    student_number: str,
    payload: EisaResultCapture,
    current_staff: dict = Depends(
        require_permission("CAPTURE_EISA")
    ),
):
    status = payload.status.strip()

    if status not in {
        "Draft",
        "Published",
    }:
        raise HTTPException(
            status_code=400,
            detail="EISA result status must be Draft or Published.",
        )

    with engine.begin() as connection:
        registration = connection.execute(
            text(
                """
                SELECT
                    r.id,
                    r.eisa_eligible,
                    c.assessment_type
                FROM public.registrations r
                JOIN public.courses c
                    ON c.course_code = r.course_code
                WHERE r.student_number = :student_number
                LIMIT 1
                """
            ),
            {"student_number": student_number},
        ).mappings().first()

        if not registration:
            raise HTTPException(
                status_code=404,
                detail="Registration not found.",
            )

        if (
            registration["assessment_type"]
            != "FISA_PLUS_EISA"
        ):
            raise HTTPException(
                status_code=400,
                detail="Learner is not on a FISA + EISA programme.",
            )

        if not registration["eisa_eligible"]:
            raise HTTPException(
                status_code=400,
                detail="Learner is not marked EISA eligible.",
            )

        row = connection.execute(
            text(
                """
                INSERT INTO public.summative_assessments (
                    registration_id,
                    assessment_type,
                    attempt_number,
                    mark,
                    assessment_date,
                    result,
                    status,
                    assessor_code,
                    moderator_code,
                    return_reason
                )
                VALUES (
                    :registration_id,
                    'EISA',
                    :attempt_number,
                    :mark,
                    :assessment_date,
                    :result,
                    CAST(:status AS varchar),
                    CAST(:staff_code AS varchar),
                    CASE
                        WHEN CAST(:status AS varchar)='Published'
                        THEN CAST(:staff_code AS varchar)
                        ELSE NULL
                    END,
                    NULL
                )
                ON CONFLICT (
                    registration_id,
                    assessment_type,
                    attempt_number
                )
                DO UPDATE SET
                    mark=EXCLUDED.mark,
                    assessment_date=EXCLUDED.assessment_date,
                    result=EXCLUDED.result,
                    status=EXCLUDED.status,
                    assessor_code=EXCLUDED.assessor_code,
                    moderator_code=EXCLUDED.moderator_code,
                    return_reason=NULL,
                    updated_at=NOW()
                RETURNING *
                """
            ),
            {
                "registration_id": registration["id"],
                "attempt_number": payload.attempt_number,
                "mark": payload.mark,
                "assessment_date": payload.assessment_date,
                "result": payload.result.strip(),
                "status": status,
                "staff_code": current_staff["staff_code"],
            },
        ).mappings().one()

    return {
        "success": True,
        "assessment": dict(row),
    }


@router.post("/eisa-results/{assessment_id}/publish")
def eisa_result_publish(
    assessment_id: str,
    current_staff: dict = Depends(
        require_permission("PUBLISH_EISA")
    ),
):
    assessment_id = _uuid(
        assessment_id,
        "EISA assessment ID",
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                """
                UPDATE public.summative_assessments
                SET
                    status='Published',
                    moderator_code=CAST(:staff_code AS varchar),
                    return_reason=NULL,
                    updated_at=NOW()
                WHERE
                    id=CAST(:assessment_id AS uuid)
                    AND assessment_type='EISA'
                RETURNING *
                """
            ),
            {
                "assessment_id": assessment_id,
                "staff_code": current_staff["staff_code"],
            },
        ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="EISA assessment was not found.",
        )

    return {
        "success": True,
        "assessment": dict(row),
    }


@router.get("/student-cards/{student_number}")
def admin_student_card(
    student_number: str,
    current_staff: dict = Depends(
        require_permission("MANAGE_STUDENT_RECORDS")
    ),
):
    del current_staff

    try:
        return {
            "success": True,
            "card": get_student_card_data(
                student_number
            ),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@router.get("/student-cards/{student_number}/pdf")
def admin_student_card_pdf(
    student_number: str,
    current_staff: dict = Depends(
        require_permission("MANAGE_STUDENT_RECORDS")
    ),
):
    del current_staff

    try:
        pdf_path = Path(
            generate_student_card_document(
                student_number
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if not pdf_path.exists():
        raise HTTPException(
            status_code=500,
            detail="Student card PDF could not be located.",
        )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{student_number}_Student_Card.pdf",
    )


# V5.2 ACADEMIC CALENDAR RANGE

from datetime import timedelta as _V52Timedelta


class AcademicCalendarRangeCreate(BaseModel):
    from_date: date
    to_date: date
    day_type: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_training_day: bool = True
    weekdays_only: bool = True
    overwrite_existing: bool = True


@router.post("/academic-calendar/range")
def academic_calendar_create_range(
    payload: AcademicCalendarRangeCreate,
    current_staff: dict = Depends(
        require_calendar
    ),
):
    allowed_day_types = {
        "Training Day",
        "Weekend",
        "Public Holiday",
        "School Holiday",
        "Special School Holiday",
        "Institution Closure",
        "Make-up Day",
    }

    if payload.day_type not in allowed_day_types:
        raise HTTPException(
            status_code=400,
            detail="Invalid academic calendar day type.",
        )

    if payload.to_date < payload.from_date:
        raise HTTPException(
            status_code=400,
            detail="To Date cannot be earlier than From Date.",
        )

    total_days = (
        payload.to_date - payload.from_date
    ).days + 1

    if total_days > 1096:
        raise HTTPException(
            status_code=400,
            detail=(
                "A single calendar range cannot exceed "
                "three years."
            ),
        )

    dates = []
    cursor = payload.from_date

    while cursor <= payload.to_date:
        if (
            not payload.weekdays_only
            or cursor.weekday() < 5
        ):
            dates.append(cursor)

        cursor += _V52Timedelta(
            days=1
        )

    inserted = 0
    updated = 0
    skipped = 0

    with engine.begin() as connection:
        for calendar_date in dates:
            existing = connection.execute(
                text(
                    """
                    SELECT id
                    FROM public.academic_calendar_dates
                    WHERE calendar_date = :calendar_date
                    LIMIT 1
                    """
                ),
                {
                    "calendar_date": (
                        calendar_date
                    ),
                },
            ).scalar()

            if (
                existing
                and not payload.overwrite_existing
            ):
                skipped += 1
                continue

            connection.execute(
                text(
                    """
                    INSERT INTO public.academic_calendar_dates (
                        calendar_date,
                        day_type,
                        description,
                        is_training_day,
                        source,
                        source_reference,
                        is_manual_override
                    )
                    VALUES (
                        :calendar_date,
                        :day_type,
                        :description,
                        :is_training_day,
                        'Staff Desktop',
                        :source_reference,
                        TRUE
                    )
                    ON CONFLICT (calendar_date)
                    DO UPDATE SET
day_type=EXCLUDED.day_type,
                        description=EXCLUDED.description,
                        is_training_day=EXCLUDED.is_training_day,
                        source='Staff Desktop',
                        source_reference=EXCLUDED.source_reference,
                        is_manual_override=TRUE,
                        updated_at=NOW()
                    """
                ),
                {
                    "calendar_date": (
                        calendar_date
                    ),
                    "day_type": (
                        payload.day_type
                    ),
                    "description": _clean(
                        payload.description
                    ),
                    "is_training_day": (
                        payload.is_training_day
                    ),
                    "source_reference": (
                        current_staff[
                            "staff_code"
                        ]
                    ),
                },
            )

            if existing:
                updated += 1
            else:
                inserted += 1

    return {
        "success": True,
        "from_date": (
            payload.from_date
        ),
        "to_date": (
            payload.to_date
        ),
        "day_type": (
            payload.day_type
        ),
        "weekdays_only": (
            payload.weekdays_only
        ),
        "total_calendar_days": (
            total_days
        ),
        "selected_dates": (
            len(
                dates
            )
        ),
        "inserted": (
            inserted
        ),
        "updated": (
            updated
        ),
        "skipped": (
            skipped
        ),
    }


# ============================================================
# V5.4.1 FISA ROOM / AUTO-SEATING
# ============================================================

from math import ceil as _v54_ceil


class FisaExamRoomCreate(BaseModel):
    assessment_centre: str = Field(min_length=1, max_length=200)
    venue_name: str = Field(min_length=1, max_length=200)
    classroom_name: str = Field(min_length=1, max_length=200)
    room_code: str = Field(min_length=1, max_length=100)
    capacity: int = Field(gt=0, le=1000)
    sort_order: int = Field(default=100, ge=1, le=9999)
    is_active: bool = True
    notes: str | None = None


class FisaExamRoomUpdate(BaseModel):
    assessment_centre: str | None = Field(default=None, max_length=200)
    venue_name: str | None = Field(default=None, max_length=200)
    classroom_name: str | None = Field(default=None, max_length=200)
    room_code: str | None = Field(default=None, max_length=100)
    capacity: int | None = Field(default=None, gt=0, le=1000)
    sort_order: int | None = Field(default=None, ge=1, le=9999)
    is_active: bool | None = None
    notes: str | None = None


class FisaAutoSittingCreate(BaseModel):
    course_code: str = Field(min_length=1, max_length=100)
    cycle_code: str = Field(min_length=1, max_length=100)
    assessment_date: date
    reporting_time: str | None = None
    start_time: str
    end_time: str
    assessment_centre: str = Field(min_length=1, max_length=200)
    instructions: str | None = None
    status: str = "Draft"
    female_min_percentage: Decimal = Field(
        default=Decimal("55"),
        ge=Decimal("0"),
        le=Decimal("100"),
    )


def _v54_fisa_learners(
    connection,
    *,
    course_code: str,
    cycle_code: str,
) -> list[dict]:
    rows = connection.execute(
        text(
            """
            SELECT
                r.id AS registration_id,
                r.student_number,
                r.course_code,
                r.cycle AS cycle_code,
                r.registration_status,
                a.first_name,
                a.middle_name,
                a.last_name,
                a.gender_code
            FROM public.registrations r
            JOIN public.applications a
                ON a.id = r.application_id
            WHERE
                r.course_code =
                    CAST(:course_code AS varchar)
                AND r.cycle =
                    CAST(:cycle_code AS varchar)
                AND r.registration_status IN (
                    'Registered',
                    'In Progress'
                )
                AND NOT EXISTS (
                    SELECT 1
                    FROM public.summative_assessments sa
                    WHERE
                        sa.registration_id = r.id
                        AND sa.assessment_type = 'FISA'
                        AND sa.status = 'Published'
                        AND upper(
                            COALESCE(sa.result, '')
                        ) IN (
                            'C',
                            'COMPETENT',
                            'PASS',
                            'PASSED'
                        )
                )
            ORDER BY
                a.last_name,
                a.first_name,
                r.student_number
            """
        ),
        {
            "course_code": course_code,
            "cycle_code": cycle_code,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


def _v54_available_rooms(
    connection,
    *,
    assessment_centre: str,
    assessment_date: date,
    start_time: str,
    end_time: str,
    exclude_sitting_id: str | None = None,
) -> list[dict]:
    rows = connection.execute(
        text(
            """
            SELECT
                er.id,
                er.assessment_centre,
                er.venue_name,
                er.classroom_name,
                er.room_code,
                er.capacity,
                er.sort_order,
                er.is_active,
                er.notes
            FROM public.fisa_exam_rooms er
            WHERE
                er.is_active = TRUE
                AND lower(er.assessment_centre) =
                    lower(
                        CAST(
                            :assessment_centre
                            AS varchar
                        )
                    )
                AND NOT EXISTS (
                    SELECT 1
                    FROM public.fisa_sitting_rooms fsr
                    JOIN public.fisa_sittings fs
                        ON fs.id = fsr.sitting_id
                    WHERE
                        fsr.exam_room_id = er.id
                        AND fs.assessment_date =
                            :assessment_date
                        AND fs.status IN (
                            'Draft',
                            'Published'
                        )
                        AND (
                            CAST(:exclude_sitting_id AS uuid)
                                IS NULL
                            OR fs.id <>
                                CAST(
                                    :exclude_sitting_id
                                    AS uuid
                                )
                        )
                        AND COALESCE(
                            fs.start_time,
                            TIME '00:00'
                        ) < CAST(:end_time AS time)
                        AND COALESCE(
                            fs.end_time,
                            TIME '23:59'
                        ) > CAST(:start_time AS time)
                )
            ORDER BY
                er.capacity DESC,
                er.sort_order,
                er.room_code
            """
        ),
        {
            "assessment_centre": assessment_centre,
            "assessment_date": assessment_date,
            "start_time": start_time,
            "end_time": end_time,
            "exclude_sitting_id": exclude_sitting_id,
        },
    ).mappings().all()

    return [
        dict(row)
        for row in rows
    ]


def _v54_optimized_room_counts(
    *,
    selected_rooms: list[dict],
    total_learners: int,
    female_min_percentage: Decimal,
) -> list[int] | None:
    """
    Distribute learners across the selected rooms so that:
    - every selected room is used,
    - no room exceeds its configured capacity,
    - the sum of per-room female minima is as small as possible,
    - ties prefer a more balanced room distribution.

    This avoids the rounding problem caused by blindly filling the
    first classroom to capacity. Example: 10 learners in two 6-seat
    rooms at 55% should be 5 + 5 (3 + 3 females), not 6 + 4
    (4 + 3 females).
    """

    if total_learners <= 0:
        return []

    if not selected_rooms:
        return None

    capacities = [
        int(
            room["capacity"]
        )
        for room in selected_rooms
    ]

    room_count = len(
        capacities
    )

    if total_learners < room_count:
        return None

    if sum(capacities) < total_learners:
        return None

    # DP state:
    # assigned learner count ->
    # (female_required, balance_score, distribution)
    #
    # balance_score is the sum of squares. For a fixed total,
    # minimizing it favours an even distribution.
    dp = {
        0: (
            0,
            0,
            [],
        )
    }

    for index, capacity in enumerate(
        capacities
    ):
        next_dp = {}

        rooms_left = (
            room_count
            - index
            - 1
        )

        remaining_capacity = sum(
            capacities[
                index + 1:
            ]
        )

        for assigned, state in dp.items():
            female_required_so_far, balance_so_far, counts = state

            # Every selected classroom must receive at least
            # one learner.
            min_here = 1

            max_here = min(
                capacity,
                total_learners
                - assigned
                - rooms_left,
            )

            if max_here < min_here:
                continue

            for count_here in range(
                min_here,
                max_here + 1,
            ):
                new_assigned = (
                    assigned
                    + count_here
                )

                learners_left = (
                    total_learners
                    - new_assigned
                )

                # Enough learners must remain to use every
                # remaining selected classroom.
                if learners_left < rooms_left:
                    continue

                # Remaining classrooms must have enough seats.
                if (
                    learners_left
                    > remaining_capacity
                ):
                    continue

                female_here = int(
                    _v54_ceil(
                        count_here
                        * float(
                            female_min_percentage
                        )
                        / 100.0
                    )
                )

                candidate = (
                    female_required_so_far
                    + female_here,
                    balance_so_far
                    + (
                        count_here
                        * count_here
                    ),
                    counts
                    + [
                        count_here
                    ],
                )

                current = next_dp.get(
                    new_assigned
                )

                if (
                    current is None
                    or candidate[0] < current[0]
                    or (
                        candidate[0]
                        == current[0]
                        and candidate[1]
                        < current[1]
                    )
                ):
                    next_dp[
                        new_assigned
                    ] = candidate

        dp = next_dp

    final = dp.get(
        total_learners
    )

    if not final:
        return None

    return final[2]


def _v54_build_room_plan(
    *,
    learners: list[dict],
    rooms: list[dict],
    female_min_percentage: Decimal,
) -> dict:
    total = len(learners)

    females = [
        row
        for row in learners
        if str(
            row.get("gender_code") or ""
        ).strip().upper() == "F"
    ]

    non_females = [
        row
        for row in learners
        if str(
            row.get("gender_code") or ""
        ).strip().upper() != "F"
    ]

    total_capacity = sum(
        int(
            room["capacity"]
        )
        for room in rooms
    )

    # Select the smallest number of classrooms needed to seat
    # the cohort. The available-room query already orders rooms
    # by capacity and configured priority.
    selected_base = []
    running_capacity = 0

    for room in rooms:
        if running_capacity >= total:
            break

        selected_base.append(
            room
        )

        running_capacity += int(
            room["capacity"]
        )

    capacity_ok = (
        total > 0
        and running_capacity >= total
    )

    selected = []

    if capacity_ok:
        planned_counts = (
            _v54_optimized_room_counts(
                selected_rooms=selected_base,
                total_learners=total,
                female_min_percentage=(
                    female_min_percentage
                ),
            )
        )

        if planned_counts is None:
            capacity_ok = False
            planned_counts = []

        for room, planned_count in zip(
            selected_base,
            planned_counts,
        ):
            selected.append(
                {
                    **room,
                    "planned_count": (
                        planned_count
                    ),
                    "female_required": int(
                        _v54_ceil(
                            planned_count
                            * float(
                                female_min_percentage
                            )
                            / 100.0
                        )
                    ),
                }
            )

    selected_capacity = sum(
        int(
            room["capacity"]
        )
        for room in selected
    )

    female_required = sum(
        room["female_required"]
        for room in selected
    )

    female_ok = (
        capacity_ok
        and len(females)
        >= female_required
    )

    if total:
        female_percentage = round(
            100.0
            * len(females)
            / total,
            2,
        )
    else:
        female_percentage = 0.0

    plan = {
        "eligible_total": total,
        "female_total": len(females),
        "non_female_total": len(
            non_females
        ),
        "female_percentage": (
            female_percentage
        ),
        "female_min_percentage": float(
            female_min_percentage
        ),
        "female_required": (
            female_required
        ),
        "female_shortage": max(
            0,
            female_required
            - len(females),
        ),
        "available_room_count": len(
            rooms
        ),
        "available_capacity": (
            total_capacity
        ),
        "selected_room_count": len(
            selected
        ),
        "selected_capacity": (
            selected_capacity
        ),
        "capacity_ok": capacity_ok,
        "female_quota_ok": female_ok,
        "feasible": (
            total > 0
            and capacity_ok
            and female_ok
        ),
        "rooms": selected,
    }

    return plan


def _v54_allocate_candidates(
    *,
    learners: list[dict],
    room_rows: list[dict],
    female_min_percentage: Decimal,
) -> list[dict]:
    female_pool = [
        row
        for row in learners
        if str(
            row.get("gender_code") or ""
        ).strip().upper() == "F"
    ]

    other_pool = [
        row
        for row in learners
        if str(
            row.get("gender_code") or ""
        ).strip().upper() != "F"
    ]

    room_allocations = []

    for room in room_rows:
        planned_count = int(
            room["planned_count"]
        )

        required = int(
            _v54_ceil(
                planned_count
                * float(
                    female_min_percentage
                )
                / 100.0
            )
        )

        required_females = []

        for _ in range(required):
            if not female_pool:
                raise ValueError(
                    "Female allocation pool was exhausted "
                    "before the 55% classroom rule was met."
                )

            required_females.append(
                female_pool.pop(0)
            )

        room_allocations.append(
            {
                **room,
                "assigned": required_females,
                "remaining": (
                    planned_count
                    - len(
                        required_females
                    )
                ),
            }
        )

    for room in room_allocations:
        while (
            room["remaining"] > 0
            and other_pool
        ):
            room["assigned"].append(
                other_pool.pop(0)
            )
            room["remaining"] -= 1

    for room in room_allocations:
        while (
            room["remaining"] > 0
            and female_pool
        ):
            room["assigned"].append(
                female_pool.pop(0)
            )
            room["remaining"] -= 1

    if (
        female_pool
        or other_pool
        or any(
            room["remaining"] > 0
            for room in room_allocations
        )
    ):
        raise ValueError(
            "Automatic candidate allocation could not "
            "fill the selected classrooms."
        )

    result = []
    global_seat = 1

    for room in room_allocations:
        local_seat = 1

        for learner in room["assigned"]:
            result.append(
                {
                    **learner,
                    "room_id": room["room_id"],
                    "exam_room_id": room["id"],
                    "room_code": room["room_code"],
                    "classroom_name": (
                        room["classroom_name"]
                    ),
                    "venue_name": (
                        room["venue_name"]
                    ),
                    "seat_number": global_seat,
                    "room_seat_number": local_seat,
                }
            )

            global_seat += 1
            local_seat += 1

    return result


@router.get("/fisa-rooms")
def v54_fisa_rooms(
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT *
                FROM public.fisa_exam_rooms
                ORDER BY
                    assessment_centre,
                    sort_order,
                    room_code
                """
            )
        ).mappings().all()

    return {
        "success": True,
        "rooms": [
            dict(row)
            for row in rows
        ],
    }


@router.post("/fisa-rooms")
def v54_fisa_room_create(
    payload: FisaExamRoomCreate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    with engine.begin() as connection:
        try:
            row = connection.execute(
                text(
                    """
                    INSERT INTO public.fisa_exam_rooms (
                        assessment_centre,
                        venue_name,
                        classroom_name,
                        room_code,
                        capacity,
                        sort_order,
                        is_active,
                        notes,
                        created_by
                    )
                    VALUES (
                        :assessment_centre,
                        :venue_name,
                        :classroom_name,
                        upper(:room_code),
                        :capacity,
                        :sort_order,
                        :is_active,
                        :notes,
                        :created_by
                    )
                    RETURNING *
                    """
                ),
                {
                    **payload.model_dump(),
                    "created_by": (
                        current_staff[
                            "staff_code"
                        ]
                    ),
                },
            ).mappings().one()
        except Exception as error:
            if (
                "duplicate"
                in str(error).lower()
                or "unique"
                in str(error).lower()
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "A classroom with this room code "
                        "already exists."
                    ),
                ) from error

            raise

    return {
        "success": True,
        "room": dict(row),
    }


@router.patch("/fisa-rooms/{room_id}")
def v54_fisa_room_update(
    room_id: str,
    payload: FisaExamRoomUpdate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    room_id = _uuid(
        room_id,
        "FISA room ID",
    )

    updates = payload.model_dump(
        exclude_unset=True
    )

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No classroom changes supplied.",
        )

    allowed = {
        "assessment_centre",
        "venue_name",
        "classroom_name",
        "room_code",
        "capacity",
        "sort_order",
        "is_active",
        "notes",
    }

    sets = []
    params = {
        "room_id": room_id,
    }

    for key, value in updates.items():
        if key not in allowed:
            continue

        if key == "room_code":
            sets.append(
                "room_code = upper(:room_code)"
            )
        else:
            sets.append(
                f"{key} = :{key}"
            )

        params[key] = value

    sets.append(
        "updated_at = NOW()"
    )

    with engine.begin() as connection:
        row = connection.execute(
            text(
                f"""
                UPDATE public.fisa_exam_rooms
                SET {", ".join(sets)}
                WHERE id =
                    CAST(:room_id AS uuid)
                RETURNING *
                """
            ),
            params,
        ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="FISA classroom was not found.",
        )

    return {
        "success": True,
        "room": dict(row),
    }


@router.get("/fisa-auto-plan")
def v54_fisa_auto_plan(
    course_code: str,
    cycle_code: str,
    assessment_centre: str,
    assessment_date: date,
    start_time: str,
    end_time: str,
    female_min_percentage: Decimal = Decimal("55"),
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    if female_min_percentage < 0 or female_min_percentage > 100:
        raise HTTPException(
            status_code=400,
            detail="Female minimum percentage must be between 0 and 100.",
        )

    with engine.connect() as connection:
        learners = _v54_fisa_learners(
            connection,
            course_code=course_code.strip().upper(),
            cycle_code=cycle_code.strip(),
        )

        rooms = _v54_available_rooms(
            connection,
            assessment_centre=assessment_centre.strip(),
            assessment_date=assessment_date,
            start_time=start_time,
            end_time=end_time,
        )

    plan = _v54_build_room_plan(
        learners=learners,
        rooms=rooms,
        female_min_percentage=(
            female_min_percentage
        ),
    )

    return {
        "success": True,
        "plan": plan,
    }


@router.post("/fisa-sittings/auto-create")
def v54_fisa_sitting_auto_create(
    payload: FisaAutoSittingCreate,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    status = payload.status.strip()

    if status not in {
        "Draft",
        "Published",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Auto-created FISA sittings must start "
                "as Draft or Published."
            ),
        )

    course_code = payload.course_code.strip().upper()
    cycle_code = payload.cycle_code.strip()
    assessment_centre = payload.assessment_centre.strip()

    with engine.begin() as connection:
        course = connection.execute(
            text(
                """
                SELECT course_code, course_name
                FROM public.courses
                WHERE course_code =
                    CAST(:course_code AS varchar)
                LIMIT 1
                """
            ),
            {
                "course_code": course_code,
            },
        ).mappings().first()

        if not course:
            raise HTTPException(
                status_code=400,
                detail="Course not found.",
            )

        cycle = connection.execute(
            text(
                """
                SELECT cycle_code
                FROM public.cycles
                WHERE cycle_code =
                    CAST(:cycle_code AS varchar)
                LIMIT 1
                """
            ),
            {
                "cycle_code": cycle_code,
            },
        ).scalar()

        if not cycle:
            raise HTTPException(
                status_code=400,
                detail="Cycle not found.",
            )

        learners = _v54_fisa_learners(
            connection,
            course_code=course_code,
            cycle_code=cycle_code,
        )

        rooms = _v54_available_rooms(
            connection,
            assessment_centre=assessment_centre,
            assessment_date=payload.assessment_date,
            start_time=payload.start_time,
            end_time=payload.end_time,
        )

        plan = _v54_build_room_plan(
            learners=learners,
            rooms=rooms,
            female_min_percentage=(
                payload.female_min_percentage
            ),
        )

        if plan["eligible_total"] == 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No FISA-outstanding learners were found "
                    "for this course and cycle."
                ),
            )

        if not plan["capacity_ok"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The configured classrooms do not have "
                    "enough available seats. "
                    f"Need {plan['eligible_total']} seats; "
                    f"available {plan['available_capacity']}."
                ),
            )

        if not plan["female_quota_ok"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The 55% female classroom rule cannot be met "
                    "with the current learner cohort. "
                    f"Female learners available: "
                    f"{plan['female_total']}; "
                    f"minimum required across the selected "
                    f"classrooms: {plan['female_required']}; "
                    f"shortage: {plan['female_shortage']}."
                ),
            )

        reference = (
            "FISA-"
            + datetime.now().strftime(
                "%Y%m%d%H%M%S%f"
            )
        )

        venue_summary = ", ".join(
            (
                f"{room['venue_name']} - "
                f"{room['classroom_name']}"
            )
            for room in plan["rooms"]
        )

        sitting = connection.execute(
            text(
                """
                INSERT INTO public.fisa_sittings (
                    sitting_reference,
                    course_code,
                    cycle_code,
                    assessment_date,
                    reporting_time,
                    start_time,
                    end_time,
                    venue,
                    assessment_centre,
                    instructions,
                    status,
                    created_by,
                    published_at,
                    female_min_percentage,
                    auto_allocate_rooms,
                    allocation_status
                )
                VALUES (
                    :reference,
                    :course_code,
                    :cycle_code,
                    :assessment_date,
                    CAST(:reporting_time AS time),
                    CAST(:start_time AS time),
                    CAST(:end_time AS time),
                    :venue,
                    :assessment_centre,
                    :instructions,
                    CAST(:status AS varchar),
                    :created_by,
                    CASE
                        WHEN CAST(:status AS varchar)
                            = 'Published'
                        THEN NOW()
                        ELSE NULL
                    END,
                    :female_min_percentage,
                    TRUE,
                    'Allocated'
                )
                RETURNING *
                """
            ),
            {
                "reference": reference,
                "course_code": course_code,
                "cycle_code": cycle_code,
                "assessment_date": (
                    payload.assessment_date
                ),
                "reporting_time": (
                    _clean(
                        payload.reporting_time
                    )
                ),
                "start_time": (
                    payload.start_time
                ),
                "end_time": (
                    payload.end_time
                ),
                "venue": venue_summary,
                "assessment_centre": (
                    assessment_centre
                ),
                "instructions": (
                    _clean(
                        payload.instructions
                    )
                ),
                "status": status,
                "created_by": (
                    current_staff[
                        "staff_code"
                    ]
                ),
                "female_min_percentage": (
                    payload.female_min_percentage
                ),
            },
        ).mappings().one()

        room_rows = []

        for index, room in enumerate(
            plan["rooms"],
            start=1,
        ):
            sitting_room = connection.execute(
                text(
                    """
                    INSERT INTO public.fisa_sitting_rooms (
                        sitting_id,
                        exam_room_id,
                        capacity_snapshot,
                        allocation_order
                    )
                    VALUES (
                        :sitting_id,
                        :exam_room_id,
                        :capacity_snapshot,
                        :allocation_order
                    )
                    RETURNING id
                    """
                ),
                {
                    "sitting_id": sitting["id"],
                    "exam_room_id": room["id"],
                    "capacity_snapshot": (
                        room["capacity"]
                    ),
                    "allocation_order": index,
                },
            ).scalar_one()

            room_rows.append(
                {
                    **room,
                    "room_id": sitting_room,
                }
            )

        allocations = _v54_allocate_candidates(
            learners=learners,
            room_rows=room_rows,
            female_min_percentage=(
                payload.female_min_percentage
            ),
        )

        for learner in allocations:
            connection.execute(
                text(
                    """
                    INSERT INTO
                        public.fisa_sitting_candidates (
                            sitting_id,
                            registration_id,
                            sitting_room_id,
                            seat_number,
                            room_seat_number,
                            admission_status,
                            attendance_status,
                            notes
                        )
                    VALUES (
                        :sitting_id,
                        :registration_id,
                        :sitting_room_id,
                        :seat_number,
                        :room_seat_number,
                        'Admitted',
                        'Pending',
                        NULL
                    )
                    """
                ),
                {
                    "sitting_id": (
                        sitting["id"]
                    ),
                    "registration_id": (
                        learner[
                            "registration_id"
                        ]
                    ),
                    "sitting_room_id": (
                        learner["room_id"]
                    ),
                    "seat_number": (
                        learner["seat_number"]
                    ),
                    "room_seat_number": (
                        learner[
                            "room_seat_number"
                        ]
                    ),
                },
            )

    return {
        "success": True,
        "sitting": dict(sitting),
        "plan": plan,
        "allocated_candidates": (
            len(
                allocations
            )
        ),
    }


@router.get(
    "/fisa-sittings/{sitting_id}/room-summary"
)
def v54_fisa_room_summary(
    sitting_id: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    sitting_id = _uuid(
        sitting_id,
        "FISA sitting ID",
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fsr.id AS sitting_room_id,
                    er.id AS exam_room_id,
                    er.assessment_centre,
                    er.venue_name,
                    er.classroom_name,
                    er.room_code,
                    fsr.capacity_snapshot AS capacity,
                    fsr.allocation_order,
                    COUNT(fsc.id) AS assigned_count,
                    COUNT(fsc.id) FILTER (
                        WHERE upper(
                            COALESCE(
                                a.gender_code,
                                ''
                            )
                        ) = 'F'
                    ) AS female_count,
                    COUNT(fsc.id) FILTER (
                        WHERE upper(
                            COALESCE(
                                a.gender_code,
                                ''
                            )
                        ) <> 'F'
                    ) AS non_female_count,
                    ROUND(
                        CASE
                            WHEN COUNT(fsc.id) = 0
                            THEN 0
                            ELSE (
                                100.0
                                * COUNT(fsc.id) FILTER (
                                    WHERE upper(
                                        COALESCE(
                                            a.gender_code,
                                            ''
                                        )
                                    ) = 'F'
                                )
                                / COUNT(fsc.id)
                            )
                        END,
                        2
                    ) AS female_percentage,
                    GREATEST(
                        fsr.capacity_snapshot
                            - COUNT(fsc.id),
                        0
                    ) AS seats_remaining,
                    fs.female_min_percentage
                FROM public.fisa_sitting_rooms fsr
                JOIN public.fisa_exam_rooms er
                    ON er.id = fsr.exam_room_id
                JOIN public.fisa_sittings fs
                    ON fs.id = fsr.sitting_id
                LEFT JOIN
                    public.fisa_sitting_candidates fsc
                    ON fsc.sitting_room_id =
                        fsr.id
                LEFT JOIN public.registrations r
                    ON r.id = fsc.registration_id
                LEFT JOIN public.applications a
                    ON a.id = r.application_id
                WHERE fsr.sitting_id =
                    CAST(:sitting_id AS uuid)
                GROUP BY
                    fsr.id,
                    er.id,
                    er.assessment_centre,
                    er.venue_name,
                    er.classroom_name,
                    er.room_code,
                    fsr.capacity_snapshot,
                    fsr.allocation_order,
                    fs.female_min_percentage
                ORDER BY
                    fsr.allocation_order,
                    er.room_code
                """
            ),
            {
                "sitting_id": sitting_id,
            },
        ).mappings().all()

    result = []

    for row in rows:
        item = dict(row)

        item["female_quota_met"] = (
            float(
                item[
                    "female_percentage"
                ] or 0
            )
            >= float(
                item[
                    "female_min_percentage"
                ] or 55
            )
        )

        result.append(item)

    return {
        "success": True,
        "rooms": result,
    }


@router.get(
    "/fisa-sittings/{sitting_id}/allocated-candidates"
)
def v54_fisa_allocated_candidates(
    sitting_id: str,
    current_staff: dict = Depends(
        require_admin_staff
    ),
):
    del current_staff

    sitting_id = _uuid(
        sitting_id,
        "FISA sitting ID",
    )

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    fsc.id,
                    fsc.seat_number,
                    fsc.room_seat_number,
                    fsc.admission_status,
                    fsc.attendance_status,
                    fsc.notes,
                    r.id AS registration_id,
                    r.student_number,
                    r.course_code,
                    r.cycle AS cycle_code,
                    a.gender_code,
                    CONCAT_WS(
                        ' ',
                        a.first_name,
                        a.middle_name,
                        a.last_name
                    ) AS learner_name,
                    er.assessment_centre,
                    er.venue_name,
                    er.classroom_name,
                    er.room_code
                FROM
                    public.fisa_sitting_candidates fsc
                JOIN public.registrations r
                    ON r.id =
                        fsc.registration_id
                JOIN public.applications a
                    ON a.id =
                        r.application_id
                LEFT JOIN
                    public.fisa_sitting_rooms fsr
                    ON fsr.id =
                        fsc.sitting_room_id
                LEFT JOIN public.fisa_exam_rooms er
                    ON er.id =
                        fsr.exam_room_id
                WHERE fsc.sitting_id =
                    CAST(:sitting_id AS uuid)
                ORDER BY
                    fsr.allocation_order,
                    fsc.room_seat_number,
                    fsc.seat_number
                """
            ),
            {
                "sitting_id": sitting_id,
            },
        ).mappings().all()

    return {
        "success": True,
        "candidates": [
            dict(row)
            for row in rows
        ],
    }


# ============================================================
# V5.5 CLASS MODERATOR ASSIGNMENT
# ============================================================

class AcademicStaffAssignmentV55(BaseModel):
    facilitator_code: str | None = None
    assessor_code: str | None = None
    moderator_code: str | None = None


def _v55_staff_has_role(
    connection,
    *,
    staff_code: str,
    role_code: str,
) -> bool:
    found = connection.execute(
        text(
            """
            SELECT 1
            FROM public.staff_accounts sa
            JOIN public.employees e
                ON e.id = sa.employee_id
            WHERE
                upper(sa.staff_code) =
                    upper(CAST(:staff_code AS varchar))
                AND sa.is_active = TRUE
                AND e.employment_status = 'Active'
                AND (
                    sa.role_code =
                        CAST(:role_code AS varchar)
                    OR EXISTS (
                        SELECT 1
                        FROM public.staff_account_roles sar
                        WHERE
                            upper(sar.staff_code) =
                                upper(sa.staff_code)
                            AND sar.role_code =
                                CAST(:role_code AS varchar)
                            AND sar.is_active = TRUE
                    )
                )
            LIMIT 1
            """
        ),
        {
            "staff_code": staff_code,
            "role_code": role_code,
        },
    ).first()

    return bool(found)


@router.get("/academic-staff-options")
def v55_academic_staff_options(
    current_staff: dict = Depends(
        require_permission("MANAGE_ACADEMIC_STRUCTURE")
    ),
):
    del current_staff

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    sa.staff_code,
                    sa.role_code AS primary_role,
                    e.employee_number,
                    e.first_name,
                    e.middle_name,
                    e.last_name,
                    e.job_title,
                    e.department,

                    (
                        sa.role_code = 'FACILITATOR'
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code = sa.staff_code
                                AND sar.role_code = 'FACILITATOR'
                                AND sar.is_active = TRUE
                        )
                    ) AS can_facilitate,

                    (
                        sa.role_code = 'ASSESSOR'
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code = sa.staff_code
                                AND sar.role_code = 'ASSESSOR'
                                AND sar.is_active = TRUE
                        )
                    ) AS can_assess,

                    (
                        sa.role_code = 'MODERATOR'
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code = sa.staff_code
                                AND sar.role_code = 'MODERATOR'
                                AND sar.is_active = TRUE
                        )
                    ) AS can_moderate

                FROM public.staff_accounts sa
                JOIN public.employees e
                    ON e.id = sa.employee_id
                WHERE
                    sa.is_active = TRUE
                    AND e.employment_status = 'Active'
                    AND (
                        sa.role_code IN (
                            'FACILITATOR',
                            'ASSESSOR',
                            'MODERATOR'
                        )
                        OR EXISTS (
                            SELECT 1
                            FROM public.staff_account_roles sar
                            WHERE
                                sar.staff_code = sa.staff_code
                                AND sar.is_active = TRUE
                                AND sar.role_code IN (
                                    'FACILITATOR',
                                    'ASSESSOR',
                                    'MODERATOR'
                                )
                        )
                    )
                ORDER BY
                    e.last_name,
                    e.first_name,
                    sa.staff_code
                """
            )
        ).mappings().all()

    return {
        "success": True,
        "count": len(rows),
        "staff": [dict(row) for row in rows],
    }


@router.get("/academic-classes")
def v55_academic_classes(
    current_staff: dict = Depends(
        require_permission("MANAGE_ACADEMIC_STRUCTURE")
    ),
):
    del current_staff

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT
                    cl.id,
                    cl.class_code,
                    cl.class_name,
                    cl.course_code,
                    c.course_name,
                    cl.cycle_code,
                    cy.cycle_name,
                    cl.class_group,

                    cl.facilitator_code,
                    CONCAT_WS(
                        ' ',
                        ef.first_name,
                        ef.middle_name,
                        ef.last_name
                    ) AS facilitator_name,

                    cl.assessor_code,
                    CONCAT_WS(
                        ' ',
                        ea.first_name,
                        ea.middle_name,
                        ea.last_name
                    ) AS assessor_name,

                    cl.moderator_code,
                    CONCAT_WS(
                        ' ',
                        em.first_name,
                        em.middle_name,
                        em.last_name
                    ) AS moderator_name,

                    cl.status,
                    cl.created_at,
                    cl.updated_at,

                    COUNT(DISTINCT ce.id) FILTER (
                        WHERE ce.status = 'Active'
                    ) AS active_learner_count

                FROM public.classes cl
                JOIN public.courses c
                    ON c.course_code = cl.course_code
                LEFT JOIN public.cycles cy
                    ON cy.cycle_code = cl.cycle_code

                LEFT JOIN public.staff_accounts saf
                    ON saf.staff_code = cl.facilitator_code
                LEFT JOIN public.employees ef
                    ON ef.id = saf.employee_id

                LEFT JOIN public.staff_accounts saa
                    ON saa.staff_code = cl.assessor_code
                LEFT JOIN public.employees ea
                    ON ea.id = saa.employee_id

                LEFT JOIN public.staff_accounts sam
                    ON sam.staff_code = cl.moderator_code
                LEFT JOIN public.employees em
                    ON em.id = sam.employee_id

                LEFT JOIN public.class_enrolments ce
                    ON ce.class_id = cl.id

                GROUP BY
                    cl.id,
                    c.course_name,
                    cy.cycle_name,
                    ef.first_name,
                    ef.middle_name,
                    ef.last_name,
                    ea.first_name,
                    ea.middle_name,
                    ea.last_name,
                    em.first_name,
                    em.middle_name,
                    em.last_name

                ORDER BY
                    cl.cycle_code DESC,
                    c.course_name,
                    cl.class_code
                """
            )
        ).mappings().all()

    return {
        "success": True,
        "count": len(rows),
        "classes": [dict(row) for row in rows],
    }


@router.put("/classes/{class_code}/academic-staff")
def v55_assign_academic_staff(
    class_code: str,
    payload: AcademicStaffAssignmentV55,
    current_staff: dict = Depends(
        require_permission("MANAGE_ACADEMIC_STRUCTURE")
    ),
):
    facilitator_code = _clean(payload.facilitator_code)
    assessor_code = _clean(payload.assessor_code)
    moderator_code = _clean(payload.moderator_code)

    if (
        assessor_code
        and moderator_code
        and assessor_code.upper() == moderator_code.upper()
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "The Assessor and Moderator must be different "
                "staff members."
            ),
        )

    with engine.begin() as connection:
        current = connection.execute(
            text(
                """
                SELECT *
                FROM public.classes
                WHERE class_code = CAST(:class_code AS varchar)
                LIMIT 1
                """
            ),
            {"class_code": class_code},
        ).mappings().first()

        if not current:
            raise HTTPException(
                status_code=404,
                detail="Class not found.",
            )

        checks = (
            (facilitator_code, "FACILITATOR", "facilitator"),
            (assessor_code, "ASSESSOR", "assessor"),
            (moderator_code, "MODERATOR", "moderator"),
        )

        for code, role, label in checks:
            if (
                code
                and not _v55_staff_has_role(
                    connection,
                    staff_code=code,
                    role_code=role,
                )
            ):
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Selected {label} does not have an "
                        f"active {role.title()} role."
                    ),
                )

        row = connection.execute(
            text(
                """
                UPDATE public.classes
                SET
                    facilitator_code =
                        CAST(:facilitator_code AS varchar),
                    assessor_code =
                        CAST(:assessor_code AS varchar),
                    moderator_code =
                        CAST(:moderator_code AS varchar),
                    updated_at = NOW()
                WHERE class_code =
                    CAST(:class_code AS varchar)
                RETURNING *
                """
            ),
            {
                "class_code": class_code,
                "facilitator_code": facilitator_code,
                "assessor_code": assessor_code,
                "moderator_code": moderator_code,
            },
        ).mappings().one()

    record = dict(row)

    _audit(
        actor=current_staff["staff_code"],
        action="CLASS_ACADEMIC_STAFF_ASSIGNED",
        entity_type="CLASS",
        entity_id=str(record["id"]),
        description=(
            "Facilitator, Assessor and Moderator assignment updated."
        ),
        after_data=record,
    )

    return {
        "success": True,
        "message": "Academic staff assignment updated.",
        "class": record,
    }
