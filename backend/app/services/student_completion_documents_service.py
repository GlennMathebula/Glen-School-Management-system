from datetime import date

from sqlalchemy import text

from app.database import engine
from app.pdfs.completion.completion_letters_pdf import (
    generate_graduation_letter_pdf,
    generate_letter_of_completion_pdf,
)

# ============================================================
# CURRENT REGISTRATION / STUDENT
# ============================================================

def get_completion_student_data(
    student_number: str,
) -> dict:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        r.id AS registration_id,
                        r.student_number,
                        r.course_code,
                        r.cycle,
                        r.registration_status,
                        r.registration_date,
                        r.program_start_date,
                        r.expected_completion_date,

                        c.course_name,
                        c.qualification_type,
                        c.nqf_level,
                        c.credits,
                        c.assessment_type,
                        c.sdp_code,
                        c.aqp_name,

                        a.first_name,
                        a.middle_name,
                        a.last_name,
                        a.title

                    FROM
                        public.registrations r

                    JOIN
                        public.courses c
                        ON c.course_code =
                            r.course_code

                    JOIN
                        public.applications a
                        ON a.student_number =
                            r.student_number

                    WHERE
                        r.student_number =
                            :student_number

                    ORDER BY
                        r.registration_date DESC,
                        r.created_at DESC

                    LIMIT 1
                    """
                ),
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
            "Student registration was not found."
        )

    data = dict(row)

    full_name = " ".join(
        [
            str(
                data.get(
                    "first_name"
                )
                or ""
            ).strip(),

            str(
                data.get(
                    "middle_name"
                )
                or ""
            ).strip(),

            str(
                data.get(
                    "last_name"
                )
                or ""
            ).strip(),
        ]
    ).strip()

    data[
        "full_name"
    ] = full_name

    data[
        "document_date"
    ] = date.today().strftime(
        "%d %B %Y"
    )

    return data


# ============================================================
# MODULE COMPLETION
# ============================================================

def get_module_completion_status(
    registration_id: str,
) -> dict:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    WITH registered_modules AS (
                        SELECT
                            mr.id AS module_registration_id

                        FROM
                            public.module_registrations mr

                        WHERE
                            mr.registration_id =
                                CAST(
                                    :registration_id
                                    AS uuid
                                )
                    ),

                    latest_published_marks AS (
                        SELECT DISTINCT ON (
                            m.module_registration_id
                        )
                            m.module_registration_id,
                            m.result,
                            m.status,
                            m.attempt_number

                        FROM
                            public.marks m

                        JOIN
                            registered_modules rm
                            ON rm.module_registration_id =
                                m.module_registration_id

                        WHERE
                            m.status = 'Published'

                        ORDER BY
                            m.module_registration_id,
                            m.attempt_number DESC,
                            m.updated_at DESC
                    )

                    SELECT
                        (
                            SELECT
                                COUNT(*)

                            FROM
                                registered_modules
                        ) AS total_modules,

                        (
                            SELECT
                                COUNT(*)

                            FROM
                                registered_modules rm

                            JOIN
                                latest_published_marks lpm
                                ON lpm.module_registration_id =
                                    rm.module_registration_id

                            WHERE
                                lpm.result = 'C'
                        ) AS competent_modules
                    """
                ),
                {
                    "registration_id": (
                        registration_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    total_modules = int(
        row[
            "total_modules"
        ]
        or 0
    )

    competent_modules = int(
        row[
            "competent_modules"
        ]
        or 0
    )

    return {
        "total_modules": (
            total_modules
        ),
        "competent_modules": (
            competent_modules
        ),
        "complete": (
            total_modules > 0
            and total_modules
            == competent_modules
        ),
    }


# ============================================================
# SUMMATIVE ASSESSMENT STATUS
# ============================================================

def get_published_summative_result(
    registration_id: str,
    assessment_type: str,
) -> dict | None:

    with engine.connect() as connection:

        row = (
            connection.execute(
                text(
                    """
                    SELECT
                        id,
                        assessment_type,
                        attempt_number,
                        mark,
                        assessment_date,
                        result,
                        status

                    FROM
                        public.summative_assessments

                    WHERE
                        registration_id =
                            CAST(
                                :registration_id
                                AS uuid
                            )

                        AND assessment_type =
                            :assessment_type

                        AND status =
                            'Published'

                    ORDER BY
                        attempt_number DESC,
                        updated_at DESC

                    LIMIT 1
                    """
                ),
                {
                    "registration_id": (
                        registration_id
                    ),
                    "assessment_type": (
                        assessment_type
                    ),
                },
            )
            .mappings()
            .first()
        )

    if not row:

        return None

    return dict(
        row
    )


# ============================================================
# ELIGIBILITY
# ============================================================

def get_student_completion_documents(
    student_number: str,
) -> dict:

    student = (
        get_completion_student_data(
            student_number
        )
    )

    registration_id = str(
        student[
            "registration_id"
        ]
    )

    assessment_type = (
        student.get(
            "assessment_type"
        )
        or ""
    ).strip()

    module_status = (
        get_module_completion_status(
            registration_id
        )
    )

    fisa = (
        get_published_summative_result(
            registration_id,
            "FISA",
        )
    )

    eisa = (
        get_published_summative_result(
            registration_id,
            "EISA",
        )
    )

    fisa_competent = bool(
        fisa
        and fisa.get(
            "result"
        ) == "C"
    )

    eisa_competent = bool(
        eisa
        and eisa.get(
            "result"
        ) == "C"
    )

    registration_completed = (
        student.get(
            "registration_status"
        )
        == "Completed"
    )

    documents = []

    # ========================================================
    # FISA ONLY
    # ========================================================

    if assessment_type == "FISA_ONLY":

        sor_available = (
            module_status[
                "complete"
            ]
            and fisa_competent
        )

        completion_letter_available = (
            sor_available
            and registration_completed
        )

        documents.append(
            {
                "document_type": (
                    "StatementOfResults"
                ),
                "document_name": (
                    "Statement of Results"
                ),
                "applicable": True,
                "available": (
                    sor_available
                ),
                "reason": (
                    None
                    if sor_available
                    else (
                        "All modules and the "
                        "published FISA result must "
                        "be competent before the "
                        "Statement of Results is "
                        "available."
                    )
                ),
                "source": (
                    "Existing Statement of "
                    "Results service"
                ),
            }
        )

        documents.append(
            {
                "document_type": (
                    "LetterOfCompletion"
                ),
                "document_name": (
                    "Letter of Completion"
                ),
                "applicable": True,
                "available": (
                    completion_letter_available
                ),
                "reason": (
                    None
                    if completion_letter_available
                    else (
                        "The learner must complete "
                        "all modules, achieve a "
                        "published competent FISA "
                        "result, and the registration "
                        "must be marked Completed."
                    )
                ),
                "download_path": (
                    "/api/student/"
                    "completion-documents/"
                    "letter-of-completion"
                ),
            }
        )

        documents.append(
            {
                "document_type": (
                    "GraduationLetter"
                ),
                "document_name": (
                    "Graduation Letter"
                ),
                "applicable": False,
                "available": False,
                "reason": (
                    "Graduation Letter applies "
                    "to FISA + EISA programmes."
                ),
            }
        )

    # ========================================================
    # FISA + EISA
    # ========================================================

    elif (
        assessment_type
        == "FISA_PLUS_EISA"
    ):

        graduation_available = (
            module_status[
                "complete"
            ]
            and fisa_competent
            and eisa_competent
            and registration_completed
        )

        documents.append(
            {
                "document_type": (
                    "StatementOfResults"
                ),
                "document_name": (
                    "Statement of Results"
                ),
                "applicable": False,
                "available": False,
                "reason": (
                    "For this Completion Documents "
                    "section, FISA + EISA programmes "
                    "use the Graduation Letter."
                ),
            }
        )

        documents.append(
            {
                "document_type": (
                    "LetterOfCompletion"
                ),
                "document_name": (
                    "Letter of Completion"
                ),
                "applicable": False,
                "available": False,
                "reason": (
                    "Letter of Completion applies "
                    "to FISA-only programmes."
                ),
            }
        )

        documents.append(
            {
                "document_type": (
                    "GraduationLetter"
                ),
                "document_name": (
                    "Graduation Letter"
                ),
                "applicable": True,
                "available": (
                    graduation_available
                ),
                "reason": (
                    None
                    if graduation_available
                    else (
                        "The learner must complete "
                        "all modules, achieve a "
                        "published competent FISA "
                        "result, receive a published "
                        "official competent EISA "
                        "result, and the registration "
                        "must be marked Completed."
                    )
                ),
                "download_path": (
                    "/api/student/"
                    "completion-documents/"
                    "graduation-letter"
                ),
            }
        )

    else:

        raise ValueError(
            
                "The course assessment type is "
                "not configured correctly."
            
        )

    return {
        "student_number": (
            student_number
        ),
        "course_code": (
            student.get(
                "course_code"
            )
        ),
        "course_name": (
            student.get(
                "course_name"
            )
        ),
        "assessment_type": (
            assessment_type
        ),
        "registration_status": (
            student.get(
                "registration_status"
            )
        ),
        "module_status": (
            module_status
        ),
        "fisa": {
            "published": bool(
                fisa
            ),
            "competent": (
                fisa_competent
            ),
        },
        "eisa": {
            "required": (
                assessment_type
                == "FISA_PLUS_EISA"
            ),
            "published": bool(
                eisa
            ),
            "competent": (
                eisa_competent
            ),
        },
        "documents": (
            documents
        ),
    }


# ============================================================
# DOCUMENT ACCESS CHECK
# ============================================================

def require_available_document(
    student_number: str,
    document_type: str,
) -> dict:

    status = (
        get_student_completion_documents(
            student_number
        )
    )

    for document in status[
        "documents"
    ]:

        if (
            document[
                "document_type"
            ]
            == document_type
        ):

            if not document.get(
                "applicable"
            ):

                raise ValueError(
                    document.get(
                        "reason"
                    )
                    or (
                        "Document does not apply "
                        "to this programme."
                    )
                )

            if not document.get(
                "available"
            ):

                raise ValueError(
                    document.get(
                        "reason"
                    )
                    or (
                        "Document is not yet "
                        "available."
                    )
                )

            return (
                get_completion_student_data(
                    student_number
                )
            )

    raise ValueError(
        "Completion document was not found."
    )


# ============================================================
# LETTER OF COMPLETION
# ============================================================

def generate_student_letter_of_completion(
    student_number: str,
) -> str:

    student = (
        require_available_document(
            student_number,
            "LetterOfCompletion",
        )
    )

    return (
        generate_letter_of_completion_pdf(
            student
        )
    )


# ============================================================
# GRADUATION LETTER
# ============================================================

def generate_student_graduation_letter(
    student_number: str,
) -> str:

    student = (
        require_available_document(
            student_number,
            "GraduationLetter",
        )
    )

    return (
        generate_graduation_letter_pdf(
            student
        )
    )