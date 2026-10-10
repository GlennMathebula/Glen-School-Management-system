from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from app.database import engine
from app.pdfs.assessment.sor_fisa_eisa_pdf import (
    generate_sor_fisa_eisa_pdf,
)
from app.pdfs.assessment.sor_fisa_only_pdf import (
    generate_sor_fisa_only_pdf,
)

# ============================================================

# HELPERS

# ============================================================



def format_date(

    value,

) -> str:



    if value is None:

        return ""



    try:

        return value.strftime(

            "%Y-%m-%d"

        )



    except AttributeError:

        return str(

            value

        )





def clean_result(

    value,

) -> str:



    if value is None:

        return ""



    value = str(

        value

    ).strip()



    upper = value.upper()



    if upper in {

        "COMPETENT",

        "C",

        "PASS",

        "PASSED",

    }:

        return "C"



    if upper in {

        "NOT YET COMPETENT",

        "NYC",

        "FAIL",

        "FAILED",

    }:

        return "NYC"



    return value





def derive_competency(

    mark,

    result,

    pass_mark,

) -> str:



    cleaned_result = (

        clean_result(

            result

        )

    )



    if cleaned_result in {

        "C",

        "NYC",

    }:

        return cleaned_result



    if mark is None:

        return ""



    threshold = Decimal(

        str(

            pass_mark

            if pass_mark is not None

            else 50

        )

    )



    numeric_mark = Decimal(

        str(

            mark

        )

    )



    if numeric_mark >= threshold:

        return "C"



    return "NYC"





def format_percentage(

    mark,

) -> str:



    if mark is None:

        return ""



    value = Decimal(

        str(

            mark

        )

    )



    if value == value.to_integral():

        return f"{int(value)}%"



    return f"{value:.2f}%"





def get_output_directory() -> Path:



    path = (

        Path(__file__)

        .resolve()

        .parents[1]

        / "generated_pdfs"

        / "assessment"

        / "statements_of_results"

    )



    path.mkdir(

        parents=True,

        exist_ok=True,

    )



    return path





# ============================================================

# ENTRY REQUIREMENT DOCUMENT

# FISA + EISA SoR ONLY

# ============================================================



def build_entry_requirement_document(
    highest_grade_passed: str | None = None,
) -> str | None:



    # For the FISA + EISA SoR, the checklist must reflect

    # the learner's ACTUAL highest grade passed as captured

    # on the application, not the programme minimum entry requirement.



    if not highest_grade_passed:

        return None



    highest_grade = str(

        highest_grade_passed

    ).strip()



    if not highest_grade:

        return None



    return (

        f"{highest_grade} "

        f"Certificate / Statement of Results"

    )



# ============================================================

# CORE LEARNER DATA

# ============================================================



def get_student_registration(

    student_number: str,

) -> dict:



    query = text(

        """

        SELECT

            r.id AS registration_id,

            r.student_number,

            r.course_code,

            r.registration_status,

            r.eisa_eligible,



            a.first_name,

            a.middle_name,

            a.last_name,

            a.national_id,

            a.alternate_id,

            a.alt_id_type,



            a.highest_grade_passed,

            a.school_name,

            a.year_completed,

            a.academic_subjects,



            c.course_name,

            c.qualification_type,

            c.nqf_level,

            c.credits,

            c.assessment_type,

            c.sdp_code,

            c.fisa_result_format,

            c.fisa_pass_mark,

            c.aqp_name,

            c.entry_requirements



        FROM public.registrations r



        JOIN public.applications a

            ON a.id = r.application_id



        JOIN public.courses c

            ON c.course_code = r.course_code



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

            "Student registration not found."

        )



    result = dict(

        row

    )



    result[

        "student_name"

    ] = " ".join(

        value

        for value in [

            result.get(

                "first_name"

            ),

            result.get(

                "middle_name"

            ),

            result.get(

                "last_name"

            ),

        ]

        if value

    )



    result[

        "identity_number"

    ] = (

        result.get(

            "national_id"

        )

        or result.get(

            "alternate_id"

        )

        or ""

    )



    result[

        "entry_requirement_document"

    ] = (

        build_entry_requirement_document(
            result.get(
                "highest_grade_passed"
            ),
        )

    )



    return result





# ============================================================

# MODULE RESULTS

# ============================================================



def get_module_results(

    registration_id: str,

) -> list[dict]:



    query = text(

        """

        SELECT

            m.id AS module_id,

            m.module_code,

            m.module_name,

            m.module_type,

            m.credits,

            m.result_format,

            m.pass_mark,



            mr.id AS module_registration_id,



            mk.mark,

            mk.result,

            mk.status,

            mk.rendered_date



        FROM public.module_registrations mr



        JOIN public.modules m

            ON m.id = mr.module_id



        LEFT JOIN LATERAL

        (

            SELECT

                marks.mark,

                marks.result,

                marks.status,

                marks.rendered_date



            FROM public.marks marks



            WHERE

                marks.module_registration_id

                = mr.id



            ORDER BY

                marks.attempt_number DESC,

                marks.created_at DESC



            LIMIT 1

        ) mk

            ON true



        WHERE

            mr.registration_id

            = CAST(

                :registration_id

                AS uuid

            )



        ORDER BY

            CASE

                WHEN m.module_type = 'KM' THEN 1

                WHEN m.module_type = 'PM' THEN 2

                WHEN m.module_type = 'WM' THEN 3

                ELSE 4

            END,

            m.module_code

        """

    )



    with engine.connect() as connection:



        rows = (

            connection.execute(

                query,

                {

                    "registration_id": (

                        registration_id

                    ),

                },

            )

            .mappings()

            .all()

        )



    results = []



    for row in rows:



        item = dict(

            row

        )



        achievement = (

            derive_competency(

                item.get(

                    "mark"

                ),

                item.get(

                    "result"

                ),

                item.get(

                    "pass_mark"

                ),

            )

        )



        percentage = ""



        if (

            item.get(

                "module_type"

            )

            == "KM"

        ):



            percentage = (

                format_percentage(

                    item.get(

                        "mark"

                    )

                )

            )



        results.append(

            {

                "module_id": (

                    item.get(

                        "module_id"

                    )

                ),

                "module_code": (

                    item.get(

                        "module_code"

                    )

                ),

                "module_name": (

                    item.get(

                        "module_name"

                    )

                ),

                "module_type": (

                    item.get(

                        "module_type"

                    )

                ),

                "credits": (

                    item.get(

                        "credits"

                    )

                ),

                "percentage": (

                    percentage

                ),

                "achievement": (

                    achievement

                ),

                "assessment_date": (

                    format_date(

                        item.get(

                            "rendered_date"

                        )

                    )

                ),

                "status": (

                    item.get(

                        "status"

                    )

                ),

            }

        )



    return results





# ============================================================

# FISA RESULT

# ============================================================



def get_latest_fisa(

    registration_id: str,

) -> dict | None:



    query = text(

        """

        SELECT

            id,

            attempt_number,

            mark,

            assessment_date,

            result,

            status,

            assessor_code,

            moderator_code,

            updated_at



        FROM public.summative_assessments



        WHERE

            registration_id

            = CAST(

                :registration_id

                AS uuid

            )



            AND assessment_type

                = 'FISA'



        ORDER BY

            attempt_number DESC,

            created_at DESC



        LIMIT 1

        """

    )



    with engine.connect() as connection:



        row = (

            connection.execute(

                query,

                {

                    "registration_id": (

                        registration_id

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

# RELEASE RULES

# ============================================================



def all_required_modules_published(

    modules: list[dict],

) -> bool:



    if not modules:

        return False



    for module in modules:



        if (

            module.get(

                "status"

            )

            != "Published"

        ):

            return False



        if (

            module.get(

                "achievement"

            )

            != "C"

        ):

            return False



    return True





def can_release_fisa_only_sor(

    registration: dict,

    modules: list[dict],

    fisa: dict | None,

) -> bool:



    if (

        registration.get(

            "assessment_type"

        )

        != "FISA_ONLY"

    ):

        return False



    if not all_required_modules_published(

        modules

    ):

        return False



    if not fisa:

        return False



    if (

        fisa.get(

            "status"

        )

        != "Published"

    ):

        return False



    fisa_result = (

        derive_competency(

            fisa.get(

                "mark"

            ),

            fisa.get(

                "result"

            ),

            registration.get(

                "fisa_pass_mark"

            ),

        )

    )



    return (

        fisa_result

        == "C"

    )





def can_release_fisa_eisa_sor(

    registration: dict,

    modules: list[dict],

    fisa: dict | None,

) -> bool:



    if (

        registration.get(

            "assessment_type"

        )

        != "FISA_PLUS_EISA"

    ):

        return False



    if not all_required_modules_published(

        modules

    ):

        return False



    if fisa:



        if (

            fisa.get(

                "status"

            )

            != "Published"

        ):

            return False



        fisa_result = (

            derive_competency(

                fisa.get(

                    "mark"

                ),

                fisa.get(

                    "result"

                ),

                registration.get(

                    "fisa_pass_mark"

                ),

            )

        )



        if (

            fisa_result

            and fisa_result != "C"

        ):

            return False



    return bool(

        registration.get(

            "eisa_eligible"

        )

    )





# ============================================================

# BUILD FISA + EISA DATA

# ============================================================



def build_fisa_eisa_sor_data(

    registration: dict,

    modules: list[dict],

) -> dict:



    knowledge_modules = [

        module

        for module in modules

        if (

            module.get(

                "module_type"

            )

            == "KM"

        )

    ]



    practical_modules = [

        module

        for module in modules

        if (

            module.get(

                "module_type"

            )

            == "PM"

        )

    ]



    workplace_modules = [

        module

        for module in modules

        if (

            module.get(

                "module_type"

            )

            == "WM"

        )

    ]



    return {

        "qualification_name": (

            registration.get(

                "course_name"

            )

        ),



        "saqa_id": (

            registration.get(

                "course_code"

            )

        ),



        "credits": (

            registration.get(

                "credits"

            )

        ),



        "nqf_level": (

            registration.get(

                "nqf_level"

            )

        ),



        "student_name": (

            registration.get(

                "student_name"

            )

        ),



        "student_number": (

            registration.get(

                "student_number"

            )

        ),



        "identity_number": (

            registration.get(

                "identity_number"

            )

        ),



        "date_issued": (

            format_date(

                date.today()

            )

        ),



        "knowledge_modules": (

            knowledge_modules

        ),



        "practical_modules": (

            practical_modules

        ),



        "workplace_modules": (

            workplace_modules

        ),



        "eisa_admission": (

            "Yes"

            if registration.get(

                "eisa_eligible"

            )

            else "No"

        ),



        "next_eisa_date": (

            "To be confirmed"

        ),



        "aqp_name": (

            registration.get(

                "aqp_name"

            )

            or "To be confirmed"

        ),



        "sdp_code": (

            registration.get(

                "sdp_code"

            )

            or "-"

        ),



        # ====================================================

        # APPLICATION / ENTRY REQUIREMENT DATA

        # FISA + EISA ONLY

        # ====================================================



        "entry_requirements": (

            registration.get(

                "entry_requirements"

            )

        ),



        "entry_requirement_document": (

            registration.get(

                "entry_requirement_document"

            )

        ),



        "highest_grade_passed": (

            registration.get(

                "highest_grade_passed"

            )

        ),



        "school_name": (

            registration.get(

                "school_name"

            )

        ),



        "year_completed": (

            registration.get(

                "year_completed"

            )

        ),



        "academic_subjects": (

            registration.get(

                "academic_subjects"

            )

        ),



        "authorised_name": (

            "____________________________"

        ),



        "authorised_designation": (

            "Principal / Academic Manager"

        ),

    }





# ============================================================

# BUILD FISA ONLY DATA

# ============================================================



def build_fisa_only_sor_data(

    registration: dict,

    modules: list[dict],

    fisa: dict,

) -> dict:



    fisa_result = (

        derive_competency(

            fisa.get(

                "mark"

            ),

            fisa.get(

                "result"

            ),

            registration.get(

                "fisa_pass_mark"

            ),

        )

    )



    fisa_mark = ""



    if (

        registration.get(

            "fisa_result_format"

        )

        == "PERCENTAGE_COMPETENCY"

    ):



        fisa_mark = (

            format_percentage(

                fisa.get(

                    "mark"

                )

            )

        )



    return {

        "qualification_name": (

            registration.get(

                "course_name"

            )

        ),



        "credits": (

            registration.get(

                "credits"

            )

        ),



        "nqf_level": (

            registration.get(

                "nqf_level"

            )

        ),



        "student_name": (

            registration.get(

                "student_name"

            )

        ),



        "student_number": (

            registration.get(

                "student_number"

            )

        ),



        "identity_number": (

            registration.get(

                "identity_number"

            )

        ),



        "date_issued": (

            format_date(

                date.today()

            )

        ),



        "modules": (

            modules

        ),



        "fisa_result_format": (

            registration.get(

                "fisa_result_format"

            )

            or "COMPETENCY"

        ),



        "fisa_date": (

            format_date(

                fisa.get(

                    "assessment_date"

                )

            )

        ),



        "fisa_mark": (

            fisa_mark

        ),



        "fisa_result": (

            fisa_result

        ),



        "overall_result": (

            fisa_result

        ),



        "authorised_name": (

            "____________________________"

        ),



        "authorised_designation": (

            "Principal / Academic Manager"

        ),

    }





# ============================================================

# GENERATE SOR

# ============================================================



def generate_student_statement_of_results(

    student_number: str,

) -> dict:



    registration = (

        get_student_registration(

            student_number

        )

    )



    modules = (

        get_module_results(

            str(

                registration[

                    "registration_id"

                ]

            )

        )

    )



    fisa = (

        get_latest_fisa(

            str(

                registration[

                    "registration_id"

                ]

            )

        )

    )



    output_directory = (

        get_output_directory()

    )



    assessment_type = (

        registration.get(

            "assessment_type"

        )

    )



    # ========================================================

    # FISA ONLY

    # ========================================================



    if (

        assessment_type

        == "FISA_ONLY"

    ):



        if not can_release_fisa_only_sor(

            registration,

            modules,

            fisa,

        ):



            raise ValueError(

                "Statement of Results is not yet available. "

                "All modules and the FISA must be successfully "

                "completed and published."

            )



        data = (

            build_fisa_only_sor_data(

                registration,

                modules,

                fisa,

            )

        )



        output_path = (

            output_directory

            / (

                f"SOR-FISA-ONLY-"

                f"{student_number}.pdf"

            )

        )



        generate_sor_fisa_only_pdf(

            output_path,

            data,

        )



        return {

            "student_number": (

                student_number

            ),

            "assessment_type": (

                "FISA_ONLY"

            ),

            "status": (

                "Released"

            ),

            "pdf_path": (

                str(

                    output_path

                )

            ),

        }



    # ========================================================

    # FISA + EISA

    # ========================================================



    if (

        assessment_type

        == "FISA_PLUS_EISA"

    ):



        if not can_release_fisa_eisa_sor(

            registration,

            modules,

            fisa,

        ):



            raise ValueError(

                "Statement of Results is not yet available. "

                "All required Knowledge, Practical and Workplace "

                "modules must be successfully completed and the "

                "learner must be eligible for EISA."

            )



        data = (

            build_fisa_eisa_sor_data(

                registration,

                modules,

            )

        )



        output_path = (

            output_directory

            / (

                f"SOR-FISA-EISA-"

                f"{student_number}.pdf"

            )

        )



        generate_sor_fisa_eisa_pdf(

            output_path,

            data,

        )



        return {

            "student_number": (

                student_number

            ),

            "assessment_type": (

                "FISA_PLUS_EISA"

            ),

            "status": (

                "Released"

            ),

            "pdf_path": (

                str(

                    output_path

                )

            ),

        }



    raise ValueError(

        "The student's course does not have "

        "a supported assessment pathway."

    )