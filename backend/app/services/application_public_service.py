from __future__ import annotations

from sqlalchemy import text

from app.database import engine
from app.services.student_document_service import upload_student_document


STANDARD_APPLICATION_DOCUMENTS = {
    "ID_COPY": {
        "label": "ID Copy",
        "required": True,
    },
    "SCHOOL_LEAVING_CERTIFICATE": {
        "label": "School Leaving Certificate",
        "required": True,
    },
    "CV": {
        "label": "Curriculum Vitae",
        "required": True,
    },
    "CIPC_CERTIFICATE": {
        "label": "CIPC Certificate",
        "required": False,
    },
}


def _mask_email(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None

    local, domain = email.split("@", 1)

    if len(local) <= 1:
        masked_local = "*"
    elif len(local) == 2:
        masked_local = f"{local[0]}*"
    else:
        masked_local = (
            local[0]
            + ("*" * min(len(local) - 2, 8))
            + local[-1]
        )

    return f"{masked_local}@{domain}"


def verify_public_application_identity(
    student_number: str,
    national_id: str,
) -> dict:
    student_number = (
        student_number.strip().upper()
    )
    national_id = national_id.strip()

    if not student_number:
        raise ValueError(
            "Student number is required."
        )

    if not national_id:
        raise ValueError(
            "South African ID number is required."
        )

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    id,
                    student_number,
                    national_id,
                    qualification_id,
                    application_cycle,
                    app_status,
                    first_name,
                    last_name,
                    email,
                    outstanding_documents,
                    created_at,
                    updated_at
                FROM public.applications
                WHERE
                    student_number = :student_number
                    AND TRIM(national_id) = :national_id
                LIMIT 1
                """
            ),
            {
                "student_number": student_number,
                "national_id": national_id,
            },
        ).mappings().first()

    if not row:
        raise ValueError(
            "Student number and ID number do not "
            "match our application records."
        )

    return dict(row)


def get_public_application_status(
    student_number: str,
    national_id: str,
) -> dict:
    verified = (
        verify_public_application_identity(
            student_number,
            national_id,
        )
    )

    with engine.connect() as connection:
        application = connection.execute(
            text(
                """
                SELECT
                    a.student_number,
                    a.first_name,
                    a.last_name,
                    a.email,
                    a.app_status,
                    a.qualification_id AS course_code,
                    COALESCE(
                        c.course_name,
                        a.course_name
                    ) AS course_name,
                    a.application_cycle AS cycle_code,
                    cy.cycle_name,
                    a.outstanding_documents,
                    a.created_at,
                    a.updated_at,

                    COUNT(
                        sd.id
                    ) FILTER (
                        WHERE sd.is_current = true
                    ) AS documents_uploaded,

                    COUNT(
                        sd.id
                    ) FILTER (
                        WHERE
                            sd.is_current = true
                            AND sd.review_status = 'Approved'
                    ) AS documents_approved,

                    COUNT(
                        sd.id
                    ) FILTER (
                        WHERE
                            sd.is_current = true
                            AND sd.review_status = 'Pending'
                    ) AS documents_pending_review

                FROM public.applications a

                LEFT JOIN public.courses c
                    ON c.course_code = a.qualification_id

                LEFT JOIN public.cycles cy
                    ON cy.cycle_code = a.application_cycle

                LEFT JOIN public.student_documents sd
                    ON sd.student_number = a.student_number

                WHERE a.id = :application_id

                GROUP BY
                    a.student_number,
                    a.first_name,
                    a.last_name,
                    a.email,
                    a.app_status,
                    a.qualification_id,
                    c.course_name,
                    a.course_name,
                    a.application_cycle,
                    cy.cycle_name,
                    a.outstanding_documents,
                    a.created_at,
                    a.updated_at

                LIMIT 1
                """
            ),
            {
                "application_id": (
                    verified["id"]
                ),
            },
        ).mappings().one()

        documents = connection.execute(
            text(
                """
                SELECT
                    document_type,
                    document_label,
                    original_filename,
                    review_status,
                    uploaded_at
                FROM public.student_documents
                WHERE
                    student_number = :student_number
                    AND is_current = true
                ORDER BY uploaded_at
                """
            ),
            {
                "student_number": (
                    verified["student_number"]
                ),
            },
        ).mappings().all()

    result = dict(application)

    outstanding = (
        result.get("outstanding_documents")
        or []
    )

    if not isinstance(outstanding, list):
        outstanding = []

    result["outstanding_documents"] = (
        outstanding
    )
    result["email_masked"] = _mask_email(
        result.pop("email", None)
    )
    result["documents_uploaded"] = int(
        result.get("documents_uploaded")
        or 0
    )
    result["documents_approved"] = int(
        result.get("documents_approved")
        or 0
    )
    result["documents_pending_review"] = int(
        result.get(
            "documents_pending_review"
        )
        or 0
    )
    result["documents"] = [
        dict(row)
        for row in documents
    ]

    return result


def get_public_application_catalogue() -> dict:
    query = text(
        """
        SELECT
            cy.cycle_code,
            cy.cycle_name,
            cy.application_start_date,
            cy.application_end_date,
            cy.program_start_date,
            cy.expected_completion_date,
            cy.cipc_required,

            c.course_code,
            c.course_name,
            c.qualification_type,
            c.nqf_level,
            c.credits,
            c.completion_months,
            c.entry_requirements,
            c.assessment_type,
            c.sdp_code

        FROM public.cycles cy

        JOIN public.cycle_courses cc
            ON cc.cycle_id = cy.id
            AND cc.is_active = true

        JOIN public.courses c
            ON c.course_code = cc.course_code
            AND c.status = 'Active'

        WHERE
            cy.status = 'Active'
            AND (
                cy.application_start_date IS NULL
                OR cy.application_start_date <= CURRENT_DATE
            )
            AND (
                cy.application_end_date IS NULL
                OR cy.application_end_date >= CURRENT_DATE
            )

        ORDER BY
            cy.program_start_date,
            cy.cycle_name,
            c.course_name
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query
        ).mappings().all()

    cycles_by_code: dict[str, dict] = {}

    for row in rows:
        item = dict(row)

        cycle_code = item["cycle_code"]

        cycle = cycles_by_code.setdefault(
            cycle_code,
            {
                "cycle_code": cycle_code,
                "cycle_name": item.get("cycle_name"),
                "application_start_date": item.get(
                    "application_start_date"
                ),
                "application_end_date": item.get(
                    "application_end_date"
                ),
                "program_start_date": item.get(
                    "program_start_date"
                ),
                "expected_completion_date": item.get(
                    "expected_completion_date"
                ),
                "cipc_required": bool(
                    item.get("cipc_required")
                ),
                "courses": [],
            },
        )

        cycle["courses"].append(
            {
                "course_code": item["course_code"],
                "course_name": item["course_name"],
                "qualification_type": item.get(
                    "qualification_type"
                ),
                "nqf_level": item.get("nqf_level"),
                "credits": item.get("credits"),
                "completion_months": item.get(
                    "completion_months"
                ),
                "entry_requirements": item.get(
                    "entry_requirements"
                ),
                "assessment_type": item.get(
                    "assessment_type"
                ),
                "sdp_code": item.get("sdp_code"),
            }
        )

    return {
        "cycles": list(
            cycles_by_code.values()
        ),
    }


def enrich_public_application_payload(
    application_data: dict,
) -> dict:
    payload = dict(application_data)

    course_code = (
        payload.get("qualification_id")
        or ""
    ).strip()

    cycle_code = (
        payload.get("application_cycle")
        or ""
    ).strip()

    if not course_code:
        raise ValueError(
            "A programme must be selected."
        )

    params = {
        "course_code": course_code,
    }

    cycle_filter = ""

    if cycle_code:
        cycle_filter = (
            "AND cy.cycle_code = :cycle_code"
        )
        params["cycle_code"] = cycle_code

    query = text(
        f"""
        SELECT
            c.course_code,
            c.course_name,
            c.nqf_level,
            c.credits,
            c.sdp_code,

            cy.cycle_code,
            cy.cycle_name,
            cy.expected_completion_date

        FROM public.courses c

        JOIN public.cycle_courses cc
            ON cc.course_code = c.course_code
            AND cc.is_active = true

        JOIN public.cycles cy
            ON cy.id = cc.cycle_id

        WHERE
            c.course_code = :course_code
            AND c.status = 'Active'
            AND cy.status = 'Active'
            AND (
                cy.application_start_date IS NULL
                OR cy.application_start_date <= CURRENT_DATE
            )
            AND (
                cy.application_end_date IS NULL
                OR cy.application_end_date >= CURRENT_DATE
            )
            {cycle_filter}

        ORDER BY cy.program_start_date
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(
            query,
            params,
        ).mappings().all()

    if not rows:
        raise ValueError(
            "The selected programme is not "
            "open for applications."
        )

    if not cycle_code and len(rows) > 1:
        raise ValueError(
            "More than one intake is open for "
            "this programme. Select an intake."
        )

    selected = dict(rows[0])

    payload["qualification_id"] = (
        selected["course_code"]
    )
    payload["course_name"] = (
        selected["course_name"]
    )
    payload["nqf_level"] = (
        selected["nqf_level"]
    )
    payload["credits"] = (
        selected["credits"]
    )
    payload["application_cycle"] = (
        selected["cycle_code"]
    )
    payload["expected_completion"] = (
        selected.get(
            "expected_completion_date"
        )
    )

    if selected.get("sdp_code"):
        payload["sdp_code"] = (
            selected["sdp_code"]
        )

    return payload


def _verified_application_for_upload(
    student_number: str,
    national_id: str,
) -> dict:
    application = (
        verify_public_application_identity(
            student_number,
            national_id,
        )
    )

    if application.get("app_status") not in {
        "Pending",
        "Outstanding Documents",
    }:
        raise ValueError(
            "Documents cannot be uploaded for "
            "this application status."
        )

    return application


def _cipc_required(
    application: dict,
) -> bool:
    cycle_code = application.get(
        "application_cycle"
    )

    if not cycle_code:
        return False

    with engine.connect() as connection:
        value = connection.execute(
            text(
                """
                SELECT cipc_required
                FROM public.cycles
                WHERE cycle_code = :cycle_code
                LIMIT 1
                """
            ),
            {
                "cycle_code": cycle_code,
            },
        ).scalar_one_or_none()

    return bool(value)


def _resolve_document_definition(
    application: dict,
    document_type: str,
    document_label: str | None,
) -> dict:
    document_type = (
        document_type.strip().upper()
    )

    if document_type == "ADDITIONAL_DOCUMENT":
        label = (
            document_label or ""
        ).strip()

        if not label:
            raise ValueError(
                "A label is required for an "
                "additional document."
            )

        if len(label) > 120:
            raise ValueError(
                "The additional document label "
                "is too long."
            )

        return {
            "document_type": document_type,
            "document_label": label,
            "is_required": False,
        }

    definition = (
        STANDARD_APPLICATION_DOCUMENTS.get(
            document_type
        )
    )

    if not definition:
        raise ValueError(
            "Unsupported application document type."
        )

    required = bool(
        definition["required"]
    )

    if (
        document_type
        == "CIPC_CERTIFICATE"
    ):
        required = _cipc_required(
            application
        )

    return {
        "document_type": document_type,
        "document_label": (
            definition["label"]
        ),
        "is_required": required,
    }


def _get_or_create_application_request(
    *,
    student_number: str,
    course_code: str | None,
    document_type: str,
    document_label: str,
    is_required: bool,
) -> str:
    with engine.begin() as connection:
        existing = connection.execute(
            text(
                """
                SELECT
                    id,
                    status
                FROM public.student_document_requests
                WHERE
                    student_number = :student_number
                    AND document_type = :document_type
                    AND request_source = 'System'
                ORDER BY requested_at DESC
                LIMIT 1
                """
            ),
            {
                "student_number": student_number,
                "document_type": document_type,
            },
        ).mappings().first()

        if existing:
            return str(existing["id"])

        row = connection.execute(
            text(
                """
                INSERT INTO public.student_document_requests
                (
                    student_number,
                    course_code,
                    document_type,
                    document_label,
                    reason,
                    request_source,
                    is_required,
                    status,
                    requested_by
                )
                VALUES
                (
                    :student_number,
                    :course_code,
                    :document_type,
                    :document_label,
                    'Submitted with online application',
                    'System',
                    :is_required,
                    'Requested',
                    NULL
                )
                RETURNING id
                """
            ),
            {
                "student_number": student_number,
                "course_code": course_code,
                "document_type": document_type,
                "document_label": document_label,
                "is_required": is_required,
            },
        ).mappings().one()

    return str(row["id"])


def upload_application_document(
    *,
    student_number: str,
    national_id: str,
    document_type: str,
    document_label: str | None,
    filename: str,
    mime_type: str | None,
    file_bytes: bytes,
) -> dict:
    application = (
        _verified_application_for_upload(
            student_number,
            national_id,
        )
    )

    definition = (
        _resolve_document_definition(
            application,
            document_type,
            document_label,
        )
    )

    request_id = (
        _get_or_create_application_request(
            student_number=(
                application["student_number"]
            ),
            course_code=(
                application.get(
                    "qualification_id"
                )
            ),
            document_type=(
                definition["document_type"]
            ),
            document_label=(
                definition["document_label"]
            ),
            is_required=(
                definition["is_required"]
            ),
        )
    )

    result = upload_student_document(
        student_number=(
            application["student_number"]
        ),
        request_id=request_id,
        filename=filename,
        mime_type=mime_type,
        file_bytes=file_bytes,
    )

    result["application_document"] = True
    result["is_required"] = (
        definition["is_required"]
    )

    return result
