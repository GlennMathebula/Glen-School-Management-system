from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.services.application_service import (
    change_application_status,
)
from app.services.registration_service import (
    generate_student_enrolment_form,
    get_registration,
    register_student,
)
from app.services.staff_audit_service import (
    create_staff_audit_log,
)


APPLICATION_STATUSES = {
    "Pending",
    "Accepted",
    "Rejected",
    "Outstanding Documents",
}

DOCUMENT_REVIEW_ACTIONS = {
    "Approved",
    "Rejected",
    "Resubmission Required",
}


def _clean(value):
    if value is None:
        return None

    if isinstance(value, str):
        value = value.strip()
        return value or None

    return value


def _json_safe(value):
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            _json_safe(item)
            for item in value
        ]

    if isinstance(
        value,
        (
            UUID,
            Decimal,
            datetime,
            date,
        ),
    ):
        return str(value)

    return value


def _audit(
    *,
    actor: str,
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
            actor_staff_code=actor,
            action_code=action_code,
            module_code="ADMISSIONS",
            entity_type=entity_type,
            entity_id=str(entity_id),
            description=description,
            before_data=_json_safe(before_data),
            after_data=_json_safe(after_data),
            metadata=_json_safe(metadata or {}),
        )
    except Exception as error:
        print(
            "WARNING: Admissions action succeeded "
            f"but audit logging failed: {error}"
        )


def _application(
    student_number: str,
) -> dict:
    student_number = student_number.strip()

    if not student_number:
        raise ValueError(
            "Student number is required."
        )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    a.*,
                    c.course_code,
                    c.course_name AS current_course_name,
                    c.qualification_type,
                    c.assessment_type,
                    c.status AS course_status
                FROM public.applications a
                LEFT JOIN public.courses c
                    ON c.course_code = a.qualification_id
                WHERE a.student_number = :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": student_number,
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "Application not found."
        )

    return dict(row)


def list_applications(
    *,
    status: str | None = None,
    course_code: str | None = None,
    cycle_code: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    status = _clean(status)
    course_code = _clean(course_code)
    cycle_code = _clean(cycle_code)
    search = _clean(search)

    if status and status not in APPLICATION_STATUSES:
        raise ValueError("Invalid application status.")

    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    filters = []
    params = {"limit": limit, "offset": offset}

    if status:
        filters.append("a.app_status = :status")
        params["status"] = status

    if course_code:
        filters.append("a.qualification_id = :course_code")
        params["course_code"] = course_code

    if cycle_code:
        filters.append("a.application_cycle = :cycle_code")
        params["cycle_code"] = cycle_code

    if search:
        filters.append(
            "(a.student_number ILIKE :search "
            "OR a.first_name ILIKE :search "
            "OR a.last_name ILIKE :search "
            "OR a.email ILIKE :search "
            "OR a.national_id ILIKE :search)"
        )
        params["search"] = f"%{search}%"

    where_sql = ""

    if filters:
        where_sql = "WHERE " + "\nAND ".join(filters)

    with engine.connect() as connection:
        total = connection.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM public.applications a
                {where_sql}
                """
            ),
            params,
        ).scalar_one()

        rows = connection.execute(
            text(
                f"""
                SELECT
                    a.id,
                    a.student_number,
                    a.first_name,
                    a.middle_name,
                    a.last_name,
                    a.email,
                    a.cell_number,
                    a.national_id,
                    a.qualification_id AS course_code,
                    COALESCE(c.course_name, a.course_name) AS course_name,
                    a.application_cycle AS cycle_code,
                    a.app_status,
                    a.outstanding_documents,
                    a.sponsor_name,
                    a.created_at,
                    a.updated_at,
                    r.id AS registration_id,
                    r.registration_status,
                    sa.account_status
                FROM public.applications a
                LEFT JOIN public.courses c
                    ON c.course_code = a.qualification_id
                LEFT JOIN public.registrations r
                    ON r.application_id = a.id
                LEFT JOIN public.student_accounts sa
                    ON sa.student_number = a.student_number
                {where_sql}
                ORDER BY a.created_at DESC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            params,
        ).mappings().all()

    return {
        "count": len(rows),
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "applications": [dict(row) for row in rows],
    }

def get_document_checklist(
    student_number: str,
) -> dict:
    application = _application(
        student_number
    )

    course_code = application.get(
        "qualification_id"
    )

    with engine.connect() as connection:
        requirements = connection.execute(
            text(
                """
                SELECT
                    id,
                    course_code,
                    document_type,
                    document_label,
                    instructions,
                    trigger_stage,
                    is_required,
                    is_active
                FROM public.course_document_requirements
                WHERE
                    course_code = :course_code
                    AND is_active = true
                ORDER BY
                    CASE trigger_stage
                        WHEN 'Application' THEN 1
                        WHEN 'Registration' THEN 2
                        ELSE 3
                    END,
                    document_label
                """
            ),
            {
                "course_code": course_code,
            },
        ).mappings().all()

        current_documents = connection.execute(
            text(
                """
                SELECT DISTINCT ON (
                    document_type
                )
                    id,
                    request_id,
                    document_type,
                    document_label,
                    original_filename,
                    storage_bucket,
                    storage_path,
                    mime_type,
                    file_size_bytes,
                    version_number,
                    is_current,
                    review_status,
                    reviewed_by,
                    reviewed_at,
                    review_notes,
                    uploaded_at
                FROM public.student_documents
                WHERE
                    student_number = :student_number
                    AND is_current = true
                ORDER BY
                    document_type,
                    version_number DESC,
                    uploaded_at DESC
                """
            ),
            {
                "student_number": student_number,
            },
        ).mappings().all()

        requests = connection.execute(
            text(
                """
                SELECT
                    id,
                    course_code,
                    document_type,
                    document_label,
                    reason,
                    instructions,
                    request_source,
                    is_required,
                    due_date,
                    status,
                    requested_by,
                    requested_at,
                    reviewed_by,
                    reviewed_at,
                    review_notes,
                    created_at,
                    updated_at
                FROM public.student_document_requests
                WHERE
                    student_number = :student_number
                    AND status <> 'Cancelled'
                ORDER BY requested_at DESC
                """
            ),
            {
                "student_number": student_number,
            },
        ).mappings().all()

    docs_by_type = {
        row["document_type"]: dict(row)
        for row in current_documents
    }

    request_by_type = {}

    for row in requests:
        document_type = row["document_type"]

        if document_type not in request_by_type:
            request_by_type[
                document_type
            ] = dict(row)

    checklist = []
    blocking_items = []

    for requirement_row in requirements:
        requirement = dict(
            requirement_row
        )

        document = docs_by_type.get(
            requirement["document_type"]
        )

        request = request_by_type.get(
            requirement["document_type"]
        )

        stage = requirement.get(
            "trigger_stage"
        )

        auto_blocking_stage = stage in {
            "Application",
            "Registration",
        }

        blocking = bool(
            requirement.get(
                "is_required"
            )
            and auto_blocking_stage
            and (
                not document
                or document.get(
                    "review_status"
                )
                != "Approved"
            )
        )

        if blocking:
            blocking_items.append(
                requirement[
                    "document_label"
                ]
            )

        checklist.append(
            {
                "source": (
                    "Course Requirement"
                ),
                "document_type": (
                    requirement[
                        "document_type"
                    ]
                ),
                "document_label": (
                    requirement[
                        "document_label"
                    ]
                ),
                "trigger_stage": stage,
                "is_required": (
                    requirement[
                        "is_required"
                    ]
                ),
                "blocking_acceptance": (
                    blocking
                ),
                "requirement": requirement,
                "request": request,
                "document": document,
            }
        )

    requirement_types = {
        item["document_type"]
        for item in checklist
    }

    for request_row in requests:
        request = dict(
            request_row
        )

        if (
            request["document_type"]
            in requirement_types
        ):
            continue

        document = docs_by_type.get(
            request["document_type"]
        )

        blocking = bool(
            request.get(
                "is_required"
            )
            and request.get(
                "status"
            )
            not in {
                "Approved",
                "Cancelled",
            }
        )

        if blocking:
            blocking_items.append(
                request[
                    "document_label"
                ]
            )

        checklist.append(
            {
                "source": (
                    request.get(
                        "request_source"
                    )
                    or "Manual"
                ),
                "document_type": (
                    request[
                        "document_type"
                    ]
                ),
                "document_label": (
                    request[
                        "document_label"
                    ]
                ),
                "trigger_stage": (
                    "On Request"
                ),
                "is_required": (
                    request[
                        "is_required"
                    ]
                ),
                "blocking_acceptance": (
                    blocking
                ),
                "requirement": None,
                "request": request,
                "document": document,
            }
        )

    blocking_items = list(
        dict.fromkeys(
            blocking_items
        )
    )

    return {
        "student_number": student_number,
        "course_code": course_code,
        "documents_complete": (
            len(blocking_items) == 0
        ),
        "blocking_documents": (
            blocking_items
        ),
        "checklist": checklist,
    }


def get_application_detail(
    student_number: str,
) -> dict:
    application = _application(
        student_number
    )

    checklist = get_document_checklist(
        student_number
    )

    with engine.connect() as connection:
        registration = connection.execute(
            text(
                """
                SELECT
                    r.*,
                    c.course_name
                FROM public.registrations r
                LEFT JOIN public.courses c
                    ON c.course_code = r.course_code
                WHERE
                    r.student_number = :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": student_number,
            },
        ).mappings().first()

        account = connection.execute(
            text(
                """
                SELECT
                    id,
                    student_number,
                    must_change_password,
                    pin_created,
                    account_status,
                    failed_login_attempts,
                    locked_until,
                    last_login_at,
                    created_at,
                    updated_at
                FROM public.student_accounts
                WHERE
                    student_number = :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": student_number,
            },
        ).mappings().first()

        history = connection.execute(
            text(
                """
                SELECT
                    id,
                    actor_staff_code,
                    action_code,
                    description,
                    before_data,
                    after_data,
                    metadata,
                    created_at
                FROM public.staff_audit_logs
                WHERE
                    module_code = 'ADMISSIONS'
                    AND entity_type = 'APPLICATION'
                    AND entity_id = :application_id
                ORDER BY created_at DESC
                LIMIT 100
                """
            ),
            {
                "application_id": str(
                    application["id"]
                ),
            },
        ).mappings().all()

    return {
        "application": application,
        "document_checklist": checklist,
        "registration": (
            dict(registration)
            if registration
            else None
        ),
        "student_account": (
            dict(account)
            if account
            else None
        ),
        "admissions_history": [
            dict(row)
            for row in history
        ],
    }


def review_document(
    document_id: str,
    *,
    action: str,
    review_notes: str | None,
    actor: str,
) -> dict:
    action = action.strip()

    if action not in DOCUMENT_REVIEW_ACTIONS:
        raise ValueError(
            "Invalid document review action."
        )

    review_notes = _clean(
        review_notes
    )

    with engine.connect() as connection:
        existing = connection.execute(
            text(
                """
                SELECT *
                FROM public.student_documents
                WHERE id = CAST(:document_id AS uuid)
                LIMIT 1
                """
            ),
            {
                "document_id": document_id,
            },
        ).mappings().first()

    if not existing:
        raise ValueError(
            "Student document not found."
        )

    existing = dict(existing)

    resolved_request_id = (
        str(existing["request_id"])
        if existing.get("request_id")
        else None
    )

    if not resolved_request_id:
        with engine.connect() as connection:
            matching_request = connection.execute(
                text(
                    """
                    SELECT id
                    FROM public.student_document_requests
                    WHERE
                        student_number = :student_number
                        AND document_type = :document_type
                        AND status IN (
                            'Requested',
                            'Submitted',
                            'Rejected',
                            'Resubmission Required'
                        )
                    ORDER BY requested_at DESC
                    LIMIT 1
                    """
                ),
                {
                    "student_number": (
                        existing["student_number"]
                    ),
                    "document_type": (
                        existing["document_type"]
                    ),
                },
            ).mappings().first()

        if matching_request:
            resolved_request_id = str(
                matching_request["id"]
            )

    document_review_status = (
        "Approved"
        if action == "Approved"
        else "Rejected"
    )

    request_status = action

    try:
        with engine.begin() as connection:
            updated_document = connection.execute(
                text(
                    """
                    UPDATE public.student_documents
                    SET
                        review_status = :review_status,
                        reviewed_by = :reviewed_by,
                        reviewed_at = now(),
                        review_notes = :review_notes,
                        updated_at = now()
                    WHERE id = CAST(:document_id AS uuid)
                    RETURNING *
                    """
                ),
                {
                    "review_status": (
                        document_review_status
                    ),
                    "reviewed_by": actor,
                    "review_notes": (
                        review_notes
                    ),
                    "document_id": (
                        document_id
                    ),
                },
            ).mappings().one()

            review = connection.execute(
                text(
                    """
                    INSERT INTO public.student_document_reviews (
                        document_id,
                        request_id,
                        student_number,
                        action,
                        review_notes,
                        reviewed_by
                    )
                    VALUES (
                        CAST(:document_id AS uuid),
                        CAST(:request_id AS uuid),
                        :student_number,
                        :action,
                        :review_notes,
                        :reviewed_by
                    )
                    RETURNING *
                    """
                ),
                {
                    "document_id": (
                        document_id
                    ),
                    "request_id": (
                        resolved_request_id
                    ),
                    "student_number": (
                        existing[
                            "student_number"
                        ]
                    ),
                    "action": action,
                    "review_notes": (
                        review_notes
                    ),
                    "reviewed_by": actor,
                },
            ).mappings().one()

            if resolved_request_id:
                connection.execute(
                    text(
                        """
                        UPDATE public.student_document_requests
                        SET
                            status = :status,
                            reviewed_by = :reviewed_by,
                            reviewed_at = now(),
                            review_notes = :review_notes,
                            updated_at = now()
                        WHERE id = CAST(:request_id AS uuid)
                        """
                    ),
                    {
                        "status": (
                            request_status
                        ),
                        "reviewed_by": (
                            actor
                        ),
                        "review_notes": (
                            review_notes
                        ),
                        "request_id": (
                            resolved_request_id
                        ),
                    },
                )

    except IntegrityError as error:
        raise ValueError(
            "The document review could not "
            "be recorded."
        ) from error

    updated_document = dict(
        updated_document
    )

    review = dict(
        review
    )

    _audit(
        actor=actor,
        action_code=(
            "APPLICATION_DOCUMENT_REVIEWED"
        ),
        entity_type="APPLICATION",
        entity_id=str(
            _application(
                existing[
                    "student_number"
                ]
            )["id"]
        ),
        description=(
            "Applicant document reviewed."
        ),
        before_data=existing,
        after_data=updated_document,
        metadata={
            "document_id": (
                document_id
            ),
            "review_action": (
                action
            ),
            "review_id": str(
                review["id"]
            ),
        },
    )

    return {
        "document": updated_document,
        "review": review,
    }


def request_outstanding_documents(
    student_number: str,
    *,
    documents: list[dict],
    actor: str,
) -> dict:
    application = _application(
        student_number
    )

    with engine.connect() as connection:
        registration = connection.execute(
            text(
                """
                SELECT id
                FROM public.registrations
                WHERE student_number = :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                ),
            },
        ).first()

    if registration:
        raise ValueError(
            "Outstanding application documents "
            "cannot be requested after registration."
        )

    cleaned = []

    for item in documents:
        document_type = _clean(
            item.get(
                "document_type"
            )
        )
        document_label = _clean(
            item.get(
                "document_label"
            )
        )

        if not document_type:
            raise ValueError(
                "document_type is required."
            )

        if not document_label:
            raise ValueError(
                "document_label is required."
            )

        cleaned.append(
            {
                "document_type": (
                    document_type
                ),
                "document_label": (
                    document_label
                ),
                "reason": _clean(
                    item.get(
                        "reason"
                    )
                ),
                "instructions": _clean(
                    item.get(
                        "instructions"
                    )
                ),
                "due_date": (
                    item.get(
                        "due_date"
                    )
                ),
                "is_required": bool(
                    item.get(
                        "is_required",
                        True,
                    )
                ),
            }
        )

    if not cleaned:
        raise ValueError(
            "At least one outstanding "
            "document is required."
        )

    created_requests = []

    with engine.begin() as connection:
        for item in cleaned:
            current = connection.execute(
                text(
                    """
                    SELECT id
                    FROM public.student_document_requests
                    WHERE
                        student_number = :student_number
                        AND document_type = :document_type
                        AND status <> 'Cancelled'
                    ORDER BY requested_at DESC
                    LIMIT 1
                    """
                ),
                {
                    "student_number": (
                        student_number
                    ),
                    "document_type": (
                        item[
                            "document_type"
                        ]
                    ),
                },
            ).mappings().first()

            if current:
                row = connection.execute(
                    text(
                        """
                        UPDATE public.student_document_requests
                        SET
                            course_code = :course_code,
                            document_label = :document_label,
                            reason = :reason,
                            instructions = :instructions,
                            request_source = 'Manual',
                            is_required = :is_required,
                            due_date = :due_date,
                            status = 'Requested',
                            requested_by = :requested_by,
                            requested_at = now(),
                            reviewed_by = NULL,
                            reviewed_at = NULL,
                            review_notes = NULL,
                            updated_at = now()
                        WHERE id = CAST(:id AS uuid)
                        RETURNING *
                        """
                    ),
                    {
                        "id": str(
                            current["id"]
                        ),
                        "course_code": (
                            application.get(
                                "qualification_id"
                            )
                        ),
                        "document_label": (
                            item[
                                "document_label"
                            ]
                        ),
                        "reason": (
                            item[
                                "reason"
                            ]
                        ),
                        "instructions": (
                            item[
                                "instructions"
                            ]
                        ),
                        "is_required": (
                            item[
                                "is_required"
                            ]
                        ),
                        "due_date": (
                            item[
                                "due_date"
                            ]
                        ),
                        "requested_by": (
                            actor
                        ),
                    },
                ).mappings().one()
            else:
                row = connection.execute(
                    text(
                        """
                        INSERT INTO public.student_document_requests (
                            student_number,
                            course_code,
                            document_type,
                            document_label,
                            reason,
                            instructions,
                            request_source,
                            is_required,
                            due_date,
                            status,
                            requested_by
                        )
                        VALUES (
                            :student_number,
                            :course_code,
                            :document_type,
                            :document_label,
                            :reason,
                            :instructions,
                            'Manual',
                            :is_required,
                            :due_date,
                            'Requested',
                            :requested_by
                        )
                        RETURNING *
                        """
                    ),
                    {
                        "student_number": (
                            student_number
                        ),
                        "course_code": (
                            application.get(
                                "qualification_id"
                            )
                        ),
                        "document_type": (
                            item[
                                "document_type"
                            ]
                        ),
                        "document_label": (
                            item[
                                "document_label"
                            ]
                        ),
                        "reason": (
                            item[
                                "reason"
                            ]
                        ),
                        "instructions": (
                            item[
                                "instructions"
                            ]
                        ),
                        "is_required": (
                            item[
                                "is_required"
                            ]
                        ),
                        "due_date": (
                            item[
                                "due_date"
                            ]
                        ),
                        "requested_by": (
                            actor
                        ),
                    },
                ).mappings().one()

            created_requests.append(
                dict(row)
            )

    status_result = (
        change_application_status(
            student_number,
            "Outstanding Documents",
            [
                item[
                    "document_label"
                ]
                for item in cleaned
            ],
        )
    )

    _audit(
        actor=actor,
        action_code=(
            "APPLICATION_OUTSTANDING_DOCUMENTS_REQUESTED"
        ),
        entity_type="APPLICATION",
        entity_id=str(
            application["id"]
        ),
        description=(
            "Application placed in "
            "Outstanding Documents status."
        ),
        before_data=application,
        after_data={
            "app_status": (
                "Outstanding Documents"
            ),
            "requests": (
                created_requests
            ),
        },
        metadata={
            "status_result": (
                status_result
            ),
        },
    )

    return {
        "status": status_result,
        "requests": (
            created_requests
        ),
        "document_checklist": (
            get_document_checklist(
                student_number
            )
        ),
    }


def _resolve_registration_defaults(
    application: dict,
    *,
    funding_type: str | None,
    cycle_code: str | None,
    program_start_date: date | None,
    expected_completion_date: date | None,
) -> dict:
    course_code = application.get(
        "qualification_id"
    )

    if not course_code:
        raise ValueError(
            "The application does not have "
            "a qualification selected."
        )

    with engine.connect() as connection:
        course = connection.execute(
            text(
                """
                SELECT *
                FROM public.courses
                WHERE course_code = :course_code
                LIMIT 1
                """
            ),
            {
                "course_code": (
                    course_code
                ),
            },
        ).mappings().first()

    if not course:
        raise ValueError(
            "The selected course does not exist."
        )

    course = dict(
        course
    )

    if course.get(
        "status"
    ) != "Active":
        raise ValueError(
            "The selected course is not active."
        )

    resolved_cycle = (
        _clean(cycle_code)
        or _clean(
            application.get(
                "application_cycle"
            )
        )
        or _clean(
            course.get(
                "cycle"
            )
        )
    )

    cycle = None

    with engine.connect() as connection:
        if resolved_cycle:
            cycle = connection.execute(
                text(
                    """
                    SELECT
                        cy.*,
                        COALESCE(
                            cc.is_active,
                            false
                        ) AS course_offered
                    FROM public.cycles cy
                    LEFT JOIN public.cycle_courses cc
                        ON cc.cycle_id = cy.id
                       AND cc.course_code = :course_code
                    WHERE
                        cy.cycle_code = :cycle_code
                    LIMIT 1
                    """
                ),
                {
                    "course_code": (
                        course_code
                    ),
                    "cycle_code": (
                        resolved_cycle
                    ),
                },
            ).mappings().first()
        else:
            rows = connection.execute(
                text(
                    """
                    SELECT
                        cy.*,
                        cc.is_active AS course_offered
                    FROM public.cycles cy
                    JOIN public.cycle_courses cc
                        ON cc.cycle_id = cy.id
                    WHERE
                        cc.course_code = :course_code
                        AND cc.is_active = true
                        AND cy.status IN (
                            'Active',
                            'Draft'
                        )
                    ORDER BY
                        CASE cy.status
                            WHEN 'Active' THEN 1
                            ELSE 2
                        END,
                        cy.program_start_date
                    """
                ),
                {
                    "course_code": (
                        course_code
                    ),
                },
            ).mappings().all()

            if len(rows) == 1:
                cycle = rows[0]
                resolved_cycle = (
                    cycle[
                        "cycle_code"
                    ]
                )
            elif len(rows) > 1:
                raise ValueError(
                    "More than one cycle is "
                    "available for this course. "
                    "Select the cycle before acceptance."
                )

    if resolved_cycle:
        if not cycle:
            raise ValueError(
                "The selected cycle does not exist."
            )

        cycle = dict(
            cycle
        )

        if not cycle.get(
            "course_offered"
        ):
            raise ValueError(
                "The selected course is not active "
                "in the selected cycle."
            )

        if cycle.get(
            "status"
        ) not in {
            "Active",
            "Draft",
        }:
            raise ValueError(
                "The selected cycle is closed "
                "or archived."
            )

    resolved_start = (
        program_start_date
        or (
            cycle.get(
                "program_start_date"
            )
            if cycle
            else None
        )
    )

    resolved_completion = (
        expected_completion_date
        or (
            cycle.get(
                "expected_completion_date"
            )
            if cycle
            else None
        )
        or application.get(
            "expected_completion"
        )
    )

    if not resolved_start:
        raise ValueError(
            "Programme start date is required. "
            "Set it on the cycle or provide it "
            "when accepting the application."
        )

    if (
        resolved_completion
        and resolved_completion
        < resolved_start
    ):
        raise ValueError(
            "Expected completion date cannot "
            "be before the programme start date."
        )

    resolved_funding = _clean(
        funding_type
    )

    if not resolved_funding:
        resolved_funding = (
            "SETA Funded"
            if application.get(
                "sponsor_name"
            )
            else "Self-Funded"
        )

    with engine.connect() as connection:
        module_count = connection.execute(
            text(
                """
                SELECT COUNT(*)
                FROM public.modules
                WHERE
                    course_code = :course_code
                    AND status = 'Active'
                """
            ),
            {
                "course_code": (
                    course_code
                ),
            },
        ).scalar_one()

    if int(
        module_count
    ) == 0:
        raise ValueError(
            "No active modules are configured "
            "for the selected course."
        )

    return {
        "course_code": (
            course_code
        ),
        "course": course,
        "cycle_code": (
            resolved_cycle
        ),
        "cycle": (
            dict(cycle)
            if cycle
            else None
        ),
        "program_start_date": (
            resolved_start
        ),
        "expected_completion_date": (
            resolved_completion
        ),
        "funding_type": (
            resolved_funding
        ),
    }


def accept_application(
    student_number: str,
    *,
    funding_type: str | None,
    cycle_code: str | None,
    program_start_date: date | None,
    expected_completion_date: date | None,
    enforce_documents: bool,
    actor: str,
) -> dict:
    application = _application(
        student_number
    )

    with engine.connect() as connection:
        existing_registration = (
            connection.execute(
                text(
                    """
                    SELECT *
                    FROM public.registrations
                    WHERE
                        student_number = :student_number
                    LIMIT 1
                    """
                ),
                {
                    "student_number": (
                        student_number
                    ),
                },
            ).mappings().first()
        )

    if existing_registration:
        if application.get(
            "app_status"
        ) != "Accepted":
            raise ValueError(
                "A registration already exists, "
                "so the application outcome cannot "
                "be changed through Admissions."
            )

        return {
            "already_processed": True,
            "application": application,
            "registration": (
                get_registration(
                    student_number
                )
            ),
        }

    checklist = get_document_checklist(
        student_number
    )

    if (
        enforce_documents
        and not checklist[
            "documents_complete"
        ]
    ):
        missing = ", ".join(
            checklist[
                "blocking_documents"
            ]
        )

        raise ValueError(
            "Application cannot be accepted "
            "while required documents are "
            f"outstanding: {missing}"
        )

    defaults = (
        _resolve_registration_defaults(
            application,
            funding_type=funding_type,
            cycle_code=cycle_code,
            program_start_date=(
                program_start_date
            ),
            expected_completion_date=(
                expected_completion_date
            ),
        )
    )

    status_result = (
        change_application_status(
            student_number,
            "Accepted",
        )
    )

    try:
        registration_result = (
            register_student(
                student_number=(
                    student_number
                ),
                funding_type=defaults[
                    "funding_type"
                ],
                cycle=defaults[
                    "cycle_code"
                ],
                program_start_date=defaults[
                    "program_start_date"
                ],
                expected_completion_date=(
                    defaults[
                        "expected_completion_date"
                    ]
                ),
            )
        )
    except Exception as error:
        _audit(
            actor=actor,
            action_code=(
                "APPLICATION_ACCEPTED_REGISTRATION_FAILED"
            ),
            entity_type="APPLICATION",
            entity_id=str(
                application[
                    "id"
                ]
            ),
            description=(
                "Application accepted, but "
                "automatic registration failed."
            ),
            before_data=application,
            after_data={
                "app_status": (
                    "Accepted"
                ),
            },
            metadata={
                "error": str(error),
                "registration_defaults": (
                    defaults
                ),
            },
        )

        raise RuntimeError(
            "The application was accepted and "
            "the acceptance letter was processed, "
            "but automatic registration failed. "
            "Use the registration retry action. "
            f"Reason: {error}"
        ) from error

    enrolment_form = None

    try:
        enrolment_form = (
            generate_student_enrolment_form(
                student_number
            )
        )
    except Exception as error:
        enrolment_form = {
            "generated": False,
            "error": str(error),
        }

    updated_application = (
        _application(
            student_number
        )
    )

    _audit(
        actor=actor,
        action_code=(
            "APPLICATION_ACCEPTED_AND_REGISTERED"
        ),
        entity_type="APPLICATION",
        entity_id=str(
            application["id"]
        ),
        description=(
            "Application accepted and learner "
            "registered automatically."
        ),
        before_data=application,
        after_data=updated_application,
        metadata={
            "status_result": (
                status_result
            ),
            "registration": (
                registration_result
            ),
            "enrolment_form": (
                enrolment_form
            ),
            "registration_defaults": (
                defaults
            ),
        },
    )

    return {
        "already_processed": False,
        "status": status_result,
        "registration": (
            registration_result
        ),
        "enrolment_form": (
            enrolment_form
        ),
        "application": (
            updated_application
        ),
    }


def reject_application(
    student_number: str,
    *,
    reason: str | None,
    actor: str,
) -> dict:
    application = _application(
        student_number
    )

    with engine.connect() as connection:
        registration = connection.execute(
            text(
                """
                SELECT id
                FROM public.registrations
                WHERE student_number = :student_number
                LIMIT 1
                """
            ),
            {
                "student_number": (
                    student_number
                ),
            },
        ).first()

    if registration:
        raise ValueError(
            "A registered learner cannot be "
            "rejected through the application "
            "workflow."
        )

    result = change_application_status(
        student_number,
        "Rejected",
    )

    _audit(
        actor=actor,
        action_code=(
            "APPLICATION_REJECTED"
        ),
        entity_type="APPLICATION",
        entity_id=str(
            application["id"]
        ),
        description=(
            "Application rejected."
        ),
        before_data=application,
        after_data={
            "app_status": (
                "Rejected"
            ),
        },
        metadata={
            "reason": _clean(
                reason
            ),
            "status_result": (
                result
            ),
        },
    )

    return {
        "status": result,
        "reason": _clean(
            reason
        ),
    }


def retry_registration(
    student_number: str,
    *,
    funding_type: str | None,
    cycle_code: str | None,
    program_start_date: date | None,
    expected_completion_date: date | None,
    actor: str,
) -> dict:
    application = _application(
        student_number
    )

    if application.get(
        "app_status"
    ) != "Accepted":
        raise ValueError(
            "Only Accepted applications can "
            "be registered."
        )

    existing = get_registration(
        student_number
    )

    if existing:
        return {
            "already_registered": True,
            "registration": existing,
        }

    defaults = (
        _resolve_registration_defaults(
            application,
            funding_type=funding_type,
            cycle_code=cycle_code,
            program_start_date=(
                program_start_date
            ),
            expected_completion_date=(
                expected_completion_date
            ),
        )
    )

    registration_result = (
        register_student(
            student_number=(
                student_number
            ),
            funding_type=defaults[
                "funding_type"
            ],
            cycle=defaults[
                "cycle_code"
            ],
            program_start_date=defaults[
                "program_start_date"
            ],
            expected_completion_date=(
                defaults[
                    "expected_completion_date"
                ]
            ),
        )
    )

    enrolment_form = None

    try:
        enrolment_form = (
            generate_student_enrolment_form(
                student_number
            )
        )
    except Exception as error:
        enrolment_form = {
            "generated": False,
            "error": str(error),
        }

    _audit(
        actor=actor,
        action_code=(
            "APPLICATION_REGISTRATION_RETRIED"
        ),
        entity_type="APPLICATION",
        entity_id=str(
            application["id"]
        ),
        description=(
            "Registration retried for "
            "an Accepted application."
        ),
        before_data=application,
        after_data=application,
        metadata={
            "registration": (
                registration_result
            ),
            "enrolment_form": (
                enrolment_form
            ),
        },
    )

    return {
        "already_registered": False,
        "registration": (
            registration_result
        ),
        "enrolment_form": (
            enrolment_form
        ),
    }


def registration_detail(
    student_number: str,
) -> dict:
    result = get_registration(
        student_number
    )

    if not result:
        raise ValueError(
            "Registration not found."
        )

    return result
