from sqlalchemy import text

from app.database import engine

# ============================================================
# GET STUDENT PROFILE
# ============================================================

def get_student_profile(
    student_number: str,
) -> dict | None:

    query = text(
        """
        SELECT
            a.student_number,

            a.title,
            a.first_name,
            a.middle_name,
            a.last_name,

            a.national_id,
            a.alternate_id,
            a.alt_id_type,

            a.birth_date,

            a.gender_code,
            a.equity_code,
            a.nationality_code,
            a.home_language,
            a.citizen_status,
            a.socioeconomic_code,

            a.disability_status,
            a.disability_rating,
            a.immigrant_status,

            a.home_addr_1,
            a.home_addr_2,
            a.home_addr_3,
            a.home_postal_code,

            a.postal_addr_1,
            a.postal_addr_2,
            a.postal_addr_3,
            a.postal_code,

            a.province_code,
            a.statssa_code,

            a.phone_number,
            a.cell_number,
            a.fax_number,
            a.email,

            a.highest_grade_passed,
            a.school_name,
            a.year_completed,
            a.academic_subjects,

            a.employment_status,
            a.rpl_admission,

            a.next_of_kin_surname,
            a.next_of_kin_full_name,
            a.next_of_kin_cell,
            a.next_of_kin_relationship,
            a.next_of_kin_email,

            a.sponsor_id,
            a.sponsor_name,

            a.popi_agree,
            a.popi_date,

            r.registration_date,
            r.registration_status,
            r.course_code,
            r.funding_type,
            r.cycle,
            r.program_start_date,
            r.expected_completion_date,

            c.course_name,
            c.qualification_type,
            c.nqf_level,
            c.credits,
            c.sdp_code,

            sa.account_status,
            sa.must_change_password,
            sa.pin_created,
            sa.last_login_at,
            sa.password_changed_at,
            sa.pin_changed_at

        FROM public.applications a

        LEFT JOIN public.registrations r
            ON r.application_id = a.id

        LEFT JOIN public.courses c
            ON c.course_code = r.course_code

        LEFT JOIN public.student_accounts sa
            ON sa.student_number = a.student_number

        WHERE a.student_number = :student_number

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        row = connection.execute(
            query,
            {
                "student_number": student_number,
            },
        ).mappings().first()

    if not row:
        return None

    return dict(row)


# ============================================================
# GET STUDENT REGISTRATION
# ============================================================

def get_student_portal_registration(
    student_number: str,
) -> dict | None:

    registration_query = text(
        """
        SELECT
            r.id,
            r.student_number,
            r.registration_date,
            r.registration_status,

            r.course_code,
            r.funding_type,
            r.cycle,

            r.program_start_date,
            r.expected_completion_date,

            r.eisa_eligible,

            c.course_name,
            c.qualification_type,
            c.nqf_level,
            c.credits,
            c.assessment_type,
            c.sdp_code,

            a.first_name,
            a.middle_name,
            a.last_name,

            a.sponsor_id,
            a.sponsor_name

        FROM public.registrations r

        JOIN public.applications a
            ON a.id = r.application_id

        JOIN public.courses c
            ON c.course_code = r.course_code

        WHERE r.student_number = :student_number

        LIMIT 1
        """
    )

    modules_query = text(
        """
        SELECT
            mr.id AS module_registration_id,

            m.module_code,
            m.module_name,
            m.module_type,
            m.nqf_level,
            m.credits,

            mr.status,
            mr.registered_at,
            mr.completed_at

        FROM public.module_registrations mr

        JOIN public.registrations r
            ON r.id = mr.registration_id

        JOIN public.modules m
            ON m.id = mr.module_id

        WHERE r.student_number = :student_number

        ORDER BY
            CASE m.module_type
                WHEN 'KM' THEN 1
                WHEN 'PM' THEN 2
                WHEN 'WM' THEN 3
                ELSE 4
            END,
            m.module_code
        """
    )

    with engine.connect() as connection:

        registration = connection.execute(
            registration_query,
            {
                "student_number": student_number,
            },
        ).mappings().first()

        if not registration:
            return None

        modules = connection.execute(
            modules_query,
            {
                "student_number": student_number,
            },
        ).mappings().all()

    return {
        "registration": dict(registration),

        "modules": [
            dict(module)
            for module in modules
        ],
    }


# ============================================================
# GET STUDENT MODULES
# ============================================================

def get_student_modules(
    student_number: str,
) -> dict | None:

    registration_query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.registration_status,

            c.course_name,
            c.qualification_type,
            c.nqf_level,
            c.credits

        FROM public.registrations r

        JOIN public.courses c
            ON c.course_code = r.course_code

        WHERE r.student_number = :student_number

        LIMIT 1
        """
    )

    modules_query = text(
        """
        SELECT
            mr.id AS module_registration_id,

            m.module_code,
            m.module_name,
            m.module_type,
            m.nqf_level,
            m.credits,

            mr.status,
            mr.registered_at,
            mr.completed_at

        FROM public.module_registrations mr

        JOIN public.registrations r
            ON r.id = mr.registration_id

        JOIN public.modules m
            ON m.id = mr.module_id

        WHERE r.student_number = :student_number

        ORDER BY
            CASE m.module_type
                WHEN 'KM' THEN 1
                WHEN 'PM' THEN 2
                WHEN 'WM' THEN 3
                ELSE 4
            END,
            m.module_code
        """
    )

    with engine.connect() as connection:

        registration = connection.execute(
            registration_query,
            {
                "student_number": student_number,
            },
        ).mappings().first()

        if not registration:
            return None

        modules = connection.execute(
            modules_query,
            {
                "student_number": student_number,
            },
        ).mappings().all()

    module_list = [
        dict(module)
        for module in modules
    ]

    knowledge_modules = [
        module
        for module in module_list
        if module.get("module_type") == "KM"
    ]

    practical_modules = [
        module
        for module in module_list
        if module.get("module_type") == "PM"
    ]

    workplace_modules = [
        module
        for module in module_list
        if module.get("module_type") == "WM"
    ]

    total_registered_credits = sum(
        module.get("credits") or 0
        for module in module_list
    )

    return {
        "programme": dict(
            registration
        ),

        "summary": {
            "total_modules": len(
                module_list
            ),
            "knowledge_modules": len(
                knowledge_modules
            ),
            "practical_modules": len(
                practical_modules
            ),
            "workplace_modules": len(
                workplace_modules
            ),
            "total_registered_credits": (
                total_registered_credits
            ),
        },

        "knowledge_modules": (
            knowledge_modules
        ),

        "practical_modules": (
            practical_modules
        ),

        "workplace_modules": (
            workplace_modules
        ),
    }


# ============================================================
# GET STUDENT DOCUMENT CENTRE
# ============================================================

def get_student_documents(
    student_number: str,
) -> dict:

    requests_query = text(
        """
        SELECT
            dr.id AS request_id,

            dr.course_code,
            dr.document_type,
            dr.document_label,

            dr.reason,
            dr.instructions,

            dr.request_source,
            dr.is_required,
            dr.due_date,

            dr.status,

            dr.requested_at,
            dr.reviewed_at,
            dr.review_notes

        FROM public.student_document_requests dr

        WHERE dr.student_number = :student_number

        ORDER BY
            CASE dr.status
                WHEN 'Requested' THEN 1
                WHEN 'Resubmission Required' THEN 2
                WHEN 'Submitted' THEN 3
                WHEN 'Rejected' THEN 4
                WHEN 'Approved' THEN 5
                WHEN 'Cancelled' THEN 6
                ELSE 7
            END,
            dr.requested_at DESC
        """
    )

    documents_query = text(
        """
        SELECT
            d.id AS document_id,
            d.request_id,

            d.document_type,
            d.document_label,

            d.original_filename,

            d.mime_type,
            d.file_size_bytes,

            d.version_number,
            d.is_current,

            d.uploaded_by_type,

            d.review_status,
            d.reviewed_at,
            d.review_notes,

            d.uploaded_at

        FROM public.student_documents d

        WHERE
            d.student_number = :student_number
            AND d.is_current = true

        ORDER BY
            d.uploaded_at DESC
        """
    )

    with engine.connect() as connection:

        request_rows = connection.execute(
            requests_query,
            {
                "student_number": student_number,
            },
        ).mappings().all()

        document_rows = connection.execute(
            documents_query,
            {
                "student_number": student_number,
            },
        ).mappings().all()

    requests = [
        dict(row)
        for row in request_rows
    ]

    documents = [
        dict(row)
        for row in document_rows
    ]

    outstanding_requests = [
        request
        for request in requests
        if request.get("status")
        in {
            "Requested",
            "Resubmission Required",
        }
    ]

    submitted_requests = [
        request
        for request in requests
        if request.get("status")
        == "Submitted"
    ]

    approved_requests = [
        request
        for request in requests
        if request.get("status")
        == "Approved"
    ]

    rejected_requests = [
        request
        for request in requests
        if request.get("status")
        == "Rejected"
    ]

    approved_documents = [
        document
        for document in documents
        if document.get("review_status")
        == "Approved"
    ]

    pending_documents = [
        document
        for document in documents
        if document.get("review_status")
        == "Pending"
    ]

    rejected_documents = [
        document
        for document in documents
        if document.get("review_status")
        == "Rejected"
    ]

    return {
        "summary": {
            "total_requests": len(
                requests
            ),
            "outstanding_requests": len(
                outstanding_requests
            ),
            "submitted_requests": len(
                submitted_requests
            ),
            "approved_requests": len(
                approved_requests
            ),
            "rejected_requests": len(
                rejected_requests
            ),
            "total_current_documents": len(
                documents
            ),
        },

        "outstanding_requests": (
            outstanding_requests
        ),

        "submitted_requests": (
            submitted_requests
        ),

        "approved_requests": (
            approved_requests
        ),

        "rejected_requests": (
            rejected_requests
        ),

        "documents": {
            "pending": (
                pending_documents
            ),
            "approved": (
                approved_documents
            ),
            "rejected": (
                rejected_documents
            ),
        },
    }