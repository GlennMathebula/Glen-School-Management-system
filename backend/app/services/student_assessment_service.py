from sqlalchemy import text

from app.database import engine

# ============================================================
# PUBLIC ASSESSMENT STATUS MAPPING
# ============================================================

def get_student_friendly_stage(
    assessment_type: str,
    internal_status: str | None,
) -> str:

    status = (
        internal_status
        or ""
    ).strip()

    assessment_type = (
        assessment_type
        or ""
    ).strip().upper()

    if not status:

        return "Not Yet Captured"

    if status == "Draft":

        return "Assessment In Progress"

    if status == "Submitted":

        return "Pending Moderation"

    if status == "Returned":

        return "Under Review"

    if status == "Moderated":

        if assessment_type == "FISA":

            return "Waiting QCTO QA Approval"

        return "Awaiting Final Approval"

    if status == "Published":

        return "Published"

    return "Processing"


# ============================================================
# FORMAT STUDENT ASSESSMENT
# ============================================================

def format_student_assessment(
    row: dict | None,
    assessment_type: str,
) -> dict:

    if not row:

        return {
            "assessment_type": (
                assessment_type
            ),

            "captured": False,

            "stage": (
                "Not Yet Captured"
            ),

            "published": False,

            "attempt_number": None,

            "mark": None,

            "result": None,

            "assessment_date": None,
        }

    status = (
        row.get(
            "status"
        )
    )

    published = (
        status == "Published"
    )

    # --------------------------------------------------------
    # SECURITY / ACADEMIC RULE
    #
    # Students only see the actual mark and result after the
    # assessment has been formally published.
    # --------------------------------------------------------

    return {
        "assessment_type": (
            assessment_type
        ),

        "captured": True,

        "stage": (
            get_student_friendly_stage(
                assessment_type,
                status,
            )
        ),

        "published": (
            published
        ),

        "attempt_number": (
            row.get(
                "attempt_number"
            )
        ),

        "mark": (
            float(
                row["mark"]
            )
            if (
                published
                and row.get(
                    "mark"
                )
                is not None
            )
            else None
        ),

        "result": (
            row.get(
                "result"
            )
            if published
            else None
        ),

        "assessment_date": (
            row.get(
                "assessment_date"
            )
            if published
            else None
        ),
    }


# ============================================================
# GET STUDENT ASSESSMENT STATUS
# ============================================================

def get_student_assessment_status(
    student_number: str,
) -> dict | None:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # REGISTRATION + PROGRAMME
    # --------------------------------------------------------

    registration_query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.registration_status,
            r.eisa_eligible,
            r.cycle,

            c.course_name,
            c.nqf_level,
            c.credits,
            c.assessment_type

        FROM public.registrations r

        JOIN public.courses c
            ON c.course_code = r.course_code

        WHERE
            r.student_number = :student_number

        LIMIT 1
        """
    )

    # --------------------------------------------------------
    # LATEST FISA ATTEMPT
    # --------------------------------------------------------

    fisa_query = text(
        """
        SELECT
            sa.id,
            sa.assessment_type,
            sa.attempt_number,
            sa.mark,
            sa.assessment_date,
            sa.result,
            sa.status,
            sa.updated_at

        FROM public.summative_assessments sa

        WHERE
            sa.registration_id = :registration_id

            AND sa.assessment_type = 'FISA'

        ORDER BY
            sa.attempt_number DESC,
            sa.updated_at DESC

        LIMIT 1
        """
    )

    # --------------------------------------------------------
    # LATEST EISA ATTEMPT
    # --------------------------------------------------------

    eisa_query = text(
        """
        SELECT
            sa.id,
            sa.assessment_type,
            sa.attempt_number,
            sa.mark,
            sa.assessment_date,
            sa.result,
            sa.status,
            sa.updated_at

        FROM public.summative_assessments sa

        WHERE
            sa.registration_id = :registration_id

            AND sa.assessment_type = 'EISA'

        ORDER BY
            sa.attempt_number DESC,
            sa.updated_at DESC

        LIMIT 1
        """
    )

    with engine.connect() as connection:

        registration_row = (
            connection.execute(
                registration_query,
                {
                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .first()
        )

        if not registration_row:

            return None

        registration = dict(
            registration_row
        )

        registration_id = (
            registration[
                "registration_id"
            ]
        )

        fisa_row = (
            connection.execute(
                fisa_query,
                {
                    "registration_id": (
                        registration_id
                    ),
                },
            )
            .mappings()
            .first()
        )

        eisa_row = (
            connection.execute(
                eisa_query,
                {
                    "registration_id": (
                        registration_id
                    ),
                },
            )
            .mappings()
            .first()
        )

    fisa = (
        format_student_assessment(
            dict(fisa_row)
            if fisa_row
            else None,
            "FISA",
        )
    )

    requires_eisa = (
        registration[
            "assessment_type"
        ]
        == "FISA_PLUS_EISA"
    )

    if requires_eisa:

        eisa = (
            format_student_assessment(
                dict(eisa_row)
                if eisa_row
                else None,
                "EISA",
            )
        )

    else:

        eisa = {
            "assessment_type": (
                "EISA"
            ),

            "required": False,

            "eligible": False,

            "captured": False,

            "stage": (
                "Not Required"
            ),

            "published": False,

            "attempt_number": None,

            "mark": None,

            "result": None,

            "assessment_date": None,
        }

    if requires_eisa:

        eisa[
            "required"
        ] = True

        eisa[
            "eligible"
        ] = bool(
            registration[
                "eisa_eligible"
            ]
        )

    # --------------------------------------------------------
    # OVERALL STUDENT-FACING STAGE
    # --------------------------------------------------------

    if not fisa[
        "captured"
    ]:

        overall_stage = (
            "FISA Not Yet Captured"
        )

    elif not fisa[
        "published"
    ]:

        overall_stage = (
            fisa[
                "stage"
            ]
        )

    elif (
        not requires_eisa
    ):

        overall_stage = (
            "FISA Published"
        )

    elif not registration[
        "eisa_eligible"
    ]:

        overall_stage = (
            "FISA Published - "
            "EISA Eligibility Pending"
        )

    elif not eisa[
        "captured"
    ]:

        overall_stage = (
            "Eligible for EISA"
        )

    elif not eisa[
        "published"
    ]:

        overall_stage = (
            eisa[
                "stage"
            ]
        )

    else:

        overall_stage = (
            "EISA Published"
        )

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "student_number": (
            registration[
                "student_number"
            ]
        ),

        "programme": {
            "course_code": (
                registration[
                    "course_code"
                ]
            ),

            "course_name": (
                registration[
                    "course_name"
                ]
            ),

            "nqf_level": (
                registration[
                    "nqf_level"
                ]
            ),

            "credits": (
                registration[
                    "credits"
                ]
            ),

            "assessment_type": (
                registration[
                    "assessment_type"
                ]
            ),

            "requires_eisa": (
                requires_eisa
            ),

            "registration_status": (
                registration[
                    "registration_status"
                ]
            ),

            "cycle": (
                registration[
                    "cycle"
                ]
            ),
        },

        "overall_stage": (
            overall_stage
        ),

        "fisa": (
            fisa
        ),

        "eisa": (
            eisa
        ),
    }