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


    # Digital FISA is authoritative for a matching course/cycle. Never expose a
    # legacy result while a digital sitting exists but has not been published.
    with engine.connect() as digital_connection:
        digital_row = digital_connection.execute(
            text("""
                SELECT s.id AS sitting_id, s.assessment_date,
                       s.qa_report_path, s.marking_method, x.status AS script_status,
                       x.rendered_outcome, x.rendered_percentage, x.approved_at, x.published_at
                FROM public.gm_fisa_sittings s
                LEFT JOIN public.gm_fisa_scripts x
                  ON x.sitting_id = s.id AND x.student_number = :number
                WHERE s.course_code = :course AND s.cycle = :cycle
                ORDER BY s.assessment_date DESC, s.created_at DESC
                LIMIT 1
            """),
            {
                "number": student_number,
                "course": registration["course_code"],
                "cycle": registration["cycle"],
            },
        ).mappings().first()
    if digital_row is not None:
        digital_status = digital_row["script_status"]
        released = bool(
            digital_status == "Published"
            and digital_row["qa_report_path"]
            and digital_row["approved_at"]
            and digital_row["published_at"]
            and (
                (digital_row["marking_method"] == "competency" and digital_row["rendered_outcome"] in {"C", "NYC"})
                or (digital_row["marking_method"] == "percentage" and digital_row["rendered_outcome"] in {"Pass", "Fail"} and digital_row["rendered_percentage"] is not None)
            )
        )
        stage_by_status = {
            None: "Awaiting FISA Script Upload",
            "Submitted": "Awaiting Assessor Marking",
            "Assessed": "Awaiting Moderation",
            "Moderated": "Awaiting Marks Rendering",
            "Rendered": "Awaiting Internal Approval",
            "Internally Approved": "Waiting QCTO QA / Publication",
            "Returned": "Assessment Under Review",
            "Published": "Published" if released else "Results Under Review",
        }
        fisa = {
            "assessment_type": "FISA",
            "captured": digital_status is not None,
            "stage": stage_by_status.get(digital_status, "FISA Processing"),
            "published": released,
            "attempt_number": None,
            "mark": float(digital_row["rendered_percentage"]) if released and digital_row["marking_method"] == "percentage" else None,
            "result": digital_row["rendered_outcome"] if released else None,
            "assessment_date": str(digital_row["assessment_date"]) if released else None,
        }

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