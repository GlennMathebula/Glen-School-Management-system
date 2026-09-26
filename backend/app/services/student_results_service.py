from sqlalchemy import text

from app.database import engine

# ============================================================
# GET STUDENT RESULTS
# ============================================================

def get_student_results(
    student_number: str,
) -> dict | None:

    student_number = (
        student_number
        .strip()
        .upper()
    )

    # --------------------------------------------------------
    # GET REGISTRATION + PROGRAMME
    # --------------------------------------------------------

    registration_query = text(
        """
        SELECT
            r.id AS registration_id,
            r.student_number,
            r.course_code,
            r.registration_status,
            r.cycle,
            r.registration_date,
            r.program_start_date,
            r.expected_completion_date,

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
    # GET PUBLISHED MODULE RESULTS
    #
    # DISTINCT ON ensures that if multiple attempts exist,
    # students see only the latest published attempt for
    # each module registration.
    # --------------------------------------------------------

    results_query = text(
        """
        SELECT DISTINCT ON (
            mr.id
        )

            mr.id AS module_registration_id,
            mr.status AS module_registration_status,

            m.id AS module_id,
            m.module_code,
            m.module_name,
            m.module_type,
            m.credits,
            m.nqf_level,

            mk.id AS mark_id,
            mk.attempt_number,
            mk.mark,
            mk.grade,
            mk.semester,
            mk.academic_year,
            mk.result,
            mk.status AS mark_status,

            mk.moderated_date,
            mk.rendered_date,
            mk.updated_at AS mark_updated_at

        FROM public.module_registrations mr

        JOIN public.registrations r
            ON r.id = mr.registration_id

        JOIN public.modules m
            ON m.id = mr.module_id

        JOIN public.marks mk
            ON mk.module_registration_id = mr.id

        WHERE
            r.student_number = :student_number

            AND mk.status = 'Published'

        ORDER BY
            mr.id,
            mk.attempt_number DESC,
            mk.rendered_date DESC NULLS LAST,
            mk.updated_at DESC
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

        result_rows = (
            connection.execute(
                results_query,
                {
                    "student_number": (
                        student_number
                    ),
                },
            )
            .mappings()
            .all()
        )

    registration = dict(
        registration_row
    )

    # --------------------------------------------------------
    # FORMAT RESULTS
    # --------------------------------------------------------

    results = []

    total_mark = 0.0
    marked_modules = 0

    passed_modules = 0
    failed_modules = 0

    total_published_credits = 0
    passed_credits = 0

    for row in result_rows:

        item = dict(
            row
        )

        mark = (
            float(
                item["mark"]
            )
            if item.get("mark") is not None
            else None
        )

        credits = (
            int(
                item["credits"]
            )
            if item.get("credits") is not None
            else 0
        )

        result_value = (
            item.get(
                "result"
            )
            or ""
        )

        if mark is not None:

            total_mark += mark

            marked_modules += 1

        total_published_credits += (
            credits
        )

        if (
            result_value
            .strip()
            .lower()
            == "pass"
        ):

            passed_modules += 1

            passed_credits += (
                credits
            )

        elif (
            result_value
            .strip()
            .lower()
            == "fail"
        ):

            failed_modules += 1

        results.append(
            {
                "module_registration_id": str(
                    item[
                        "module_registration_id"
                    ]
                ),

                "module_id": str(
                    item[
                        "module_id"
                    ]
                ),

                "module_code": (
                    item[
                        "module_code"
                    ]
                ),

                "module_name": (
                    item[
                        "module_name"
                    ]
                ),

                "module_type": (
                    item[
                        "module_type"
                    ]
                ),

                "credits": (
                    credits
                ),

                "nqf_level": (
                    item[
                        "nqf_level"
                    ]
                ),

                "attempt_number": (
                    item[
                        "attempt_number"
                    ]
                ),

                "mark": (
                    mark
                ),

                "grade": (
                    item[
                        "grade"
                    ]
                ),

                "result": (
                    item[
                        "result"
                    ]
                ),

                "semester": (
                    item[
                        "semester"
                    ]
                ),

                "academic_year": (
                    item[
                        "academic_year"
                    ]
                ),

                "published": True,

                "moderated_date": (
                    item[
                        "moderated_date"
                    ]
                ),

                "rendered_date": (
                    item[
                        "rendered_date"
                    ]
                ),
            }
        )

    average_mark = None

    if marked_modules > 0:

        average_mark = round(
            total_mark
            / marked_modules,
            2,
        )

    # --------------------------------------------------------
    # GROUP BY MODULE TYPE
    # --------------------------------------------------------

    knowledge_modules = []

    practical_modules = []

    workplace_modules = []

    for result in results:

        module_type = (
            result.get(
                "module_type"
            )
            or ""
        ).upper()

        if module_type == "KM":

            knowledge_modules.append(
                result
            )

        elif module_type == "PM":

            practical_modules.append(
                result
            )

        elif module_type == "WM":

            workplace_modules.append(
                result
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

            "programme_credits": (
                registration[
                    "credits"
                ]
            ),

            "assessment_type": (
                registration[
                    "assessment_type"
                ]
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

        "summary": {
            "published_modules": (
                len(
                    results
                )
            ),

            "marked_modules": (
                marked_modules
            ),

            "passed_modules": (
                passed_modules
            ),

            "failed_modules": (
                failed_modules
            ),

            "average_mark": (
                average_mark
            ),

            "published_credits": (
                total_published_credits
            ),

            "passed_credits": (
                passed_credits
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

        "results": (
            results
        ),
    }