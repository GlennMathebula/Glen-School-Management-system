from datetime import date

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.pdfs.admin_documents import (
    generate_enrolment_form,
)
from app.pdfs.registration_documents import (
    generate_proof_of_registration,
)
from app.services.email_service import (
    send_email,
)
from app.services.student_auth_service import (
    create_student_account,
)

# ============================================================

# ALLOWED REGISTRATION STATUSES

# ============================================================



ALLOWED_REGISTRATION_STATUSES = {

    "Registered",

    "In Progress",

    "Suspended",

    "Withdrawn",

    "Cancelled",

    "Completed",

}





# ============================================================

# GET APPLICATION FOR REGISTRATION

# ============================================================



def get_application_for_registration(

    student_number: str,

) -> dict | None:



    query = text(

        """

        SELECT

            id,

            student_number,

            qualification_id,

            app_status,

            application_cycle,

            sponsor_name,



            first_name,

            middle_name,

            last_name,



            national_id,

            alternate_id,



            email,

            cell_number,



            popi_agree,

            popi_date



        FROM public.applications



        WHERE student_number = :student_number



        LIMIT 1

        """

    )



    with engine.connect() as connection:



        row = connection.execute(

            query,

            {

                "student_number": (

                    student_number

                ),

            },

        ).mappings().first()



    return (

        dict(row)

        if row

        else None

    )





# ============================================================

# GET COURSE

# ============================================================



def get_course(

    course_code: str,

) -> dict | None:



    query = text(

        """

        SELECT

            id,

            course_code,

            course_name,

            qualification_type,

            nqf_level,

            credits,

            status,

            cycle,

            completion_months,

            assessment_type,

            entry_requirements,

            sdp_code



        FROM public.courses



        WHERE course_code = :course_code



        LIMIT 1

        """

    )



    with engine.connect() as connection:



        row = connection.execute(

            query,

            {

                "course_code": (

                    course_code

                ),

            },

        ).mappings().first()



    return (

        dict(row)

        if row

        else None

    )





# ============================================================

# GET COURSE MODULES

# ============================================================



def get_course_modules(

    course_code: str,

) -> list[dict]:



    query = text(

        """

        SELECT

            id,

            course_code,

            module_code,

            module_name,

            credits,

            nqf_level,

            module_type,

            status



        FROM public.modules



        WHERE course_code = :course_code

          AND status = 'Active'



        ORDER BY

            CASE module_type

                WHEN 'KM' THEN 1

                WHEN 'PM' THEN 2

                WHEN 'WM' THEN 3

                ELSE 4

            END,

            module_code

        """

    )



    with engine.connect() as connection:



        rows = connection.execute(

            query,

            {

                "course_code": (

                    course_code

                ),

            },

        ).mappings().all()



    return [

        dict(row)

        for row in rows

    ]





# ============================================================

# CHECK EXISTING REGISTRATION

# ============================================================



def get_existing_registration(

    student_number: str,

) -> dict | None:



    query = text(

        """

        SELECT

            id,

            application_id,

            student_number,

            course_code,

            registration_date,

            registration_status,

            funding_type,

            cycle,

            program_start_date,

            expected_completion_date,

            eisa_eligible,

            created_at,

            updated_at



        FROM public.registrations



        WHERE student_number = :student_number



        LIMIT 1

        """

    )



    with engine.connect() as connection:



        row = connection.execute(

            query,

            {

                "student_number": (

                    student_number

                ),

            },

        ).mappings().first()



    return (

        dict(row)

        if row

        else None

    )





# ============================================================

# GET COMPLETE REGISTRATION

# ============================================================



def get_registration(

    student_number: str,

) -> dict | None:



    registration_query = text(

        """

        SELECT

            r.id,

            r.application_id,

            r.student_number,

            r.course_code,

            r.registration_date,

            r.registration_status,

            r.funding_type,

            r.cycle,

            r.program_start_date,

            r.expected_completion_date,

            r.eisa_eligible,

            r.created_at,

            r.updated_at,



            a.first_name,

            a.middle_name,

            a.last_name,



            a.national_id,

            a.alternate_id,



            a.email,

            a.cell_number,



            c.course_name,

            c.qualification_type,

            c.nqf_level,

            c.credits,

            c.assessment_type,

            c.sdp_code



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

            mr.id

                AS module_registration_id,



            mr.status,

            mr.registered_at,

            mr.completed_at,



            m.id

                AS module_id,



            m.module_code,

            m.module_name,

            m.credits,

            m.nqf_level,

            m.module_type



        FROM public.module_registrations mr



        JOIN public.modules m

            ON m.id = mr.module_id



        WHERE mr.registration_id = :registration_id



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



        registration_row = connection.execute(

            registration_query,

            {

                "student_number": (

                    student_number

                ),

            },

        ).mappings().first()



        if not registration_row:



            return None



        module_rows = connection.execute(

            modules_query,

            {

                "registration_id": (

                    registration_row["id"]

                ),

            },

        ).mappings().all()



    return {

        "registration": dict(

            registration_row

        ),

        "modules": [

            dict(row)

            for row in module_rows

        ],

    }





# ============================================================

# BUILD REGISTRATION EMAIL

# ============================================================



def build_registration_email_body(

    registration_data: dict,

) -> str:



    registration = registration_data.get(

        "registration",

        {},

    )



    first_name = (

        registration.get(

            "first_name"

        )

        or "Student"

    )



    student_number = (

        registration.get(

            "student_number"

        )

        or ""

    )



    course_name = (

        registration.get(

            "course_name"

        )

        or ""

    )



    program_start_date = (

        registration.get(

            "program_start_date"

        )

    )



    expected_completion_date = (

        registration.get(

            "expected_completion_date"

        )

    )



    start_text = (

        str(program_start_date)

        if program_start_date

        else "To be confirmed"

    )



    completion_text = (

        str(expected_completion_date)

        if expected_completion_date

        else "To be confirmed"

    )



    return (

        f"Dear {first_name},\n\n"



        "Your registration with Glen Moniques "

        "has been completed successfully.\n\n"



        "Registration Details:\n"

        f"Student Number: {student_number}\n"

        f"Qualification: {course_name}\n"

        f"Programme Start Date: {start_text}\n"

        f"Expected Completion Date: {completion_text}\n\n"



        "Your Proof of Registration is attached "

        "to this email.\n\n"



        "Please keep this document for your records.\n\n"



        "Regards,\n"

        "Glen Moniques (Pty) Ltd"

    )





# ============================================================

# BUILD POR RESEND EMAIL

# ============================================================



def build_por_resend_email_body(

    registration_data: dict,

) -> str:



    registration = registration_data.get(

        "registration",

        {},

    )



    first_name = (

        registration.get(

            "first_name"

        )

        or "Student"

    )



    student_number = (

        registration.get(

            "student_number"

        )

        or ""

    )



    course_name = (

        registration.get(

            "course_name"

        )

        or ""

    )



    return (

        f"Dear {first_name},\n\n"



        "As requested, a new copy of your "

        "Proof of Registration has been generated.\n\n"



        "Registration Details:\n"

        f"Student Number: {student_number}\n"

        f"Qualification: {course_name}\n\n"



        "Your updated Proof of Registration "

        "is attached to this email.\n\n"



        "You may request another copy whenever "

        "you require one.\n\n"



        "Regards,\n"

        "Glen Moniques (Pty) Ltd"

    )





# ============================================================

# REGISTER STUDENT

# ============================================================



def register_student(

    student_number: str,

    funding_type: str | None = None,

    cycle: str | None = None,

    program_start_date: date | None = None,

    expected_completion_date: date | None = None,

) -> dict:



    application = (

        get_application_for_registration(

            student_number

        )

    )



    if not application:



        raise ValueError(

            "Application not found."

        )



    if (

        application.get(

            "app_status"

        )

        != "Accepted"

    ):



        raise ValueError(

            "Only applicants with Accepted status "

            "can be registered."

        )



    qualification_id = (

        application.get(

            "qualification_id"

        )

    )



    if not qualification_id:



        raise ValueError(

            "The application does not have "

            "a qualification_id."

        )



    course = get_course(

        qualification_id

    )



    if not course:



        raise ValueError(

            f"Course {qualification_id} "

            "was not found in the courses table."

        )



    if (

        course.get(

            "status"

        )

        != "Active"

    ):



        raise ValueError(

            f"Course {qualification_id} "

            "is not currently active."

        )



    if not program_start_date:



        raise ValueError(

            "Programme start date is required."

        )



    if (

        expected_completion_date

        and expected_completion_date

        < program_start_date

    ):



        raise ValueError(

            "Expected completion date cannot be "

            "before the programme start date."

        )



    existing_registration = (

        get_existing_registration(

            student_number

        )

    )



    if existing_registration:



        raise ValueError(

            "This student already has "

            "a registration record."

        )



    modules = get_course_modules(

        qualification_id

    )



    if not modules:



        raise ValueError(

            f"No active modules were found "

            f"for course {qualification_id}."

        )



    registration_cycle = (

        cycle

        or application.get(

            "application_cycle"

        )

        or course.get(

            "cycle"

        )

    )



    try:



        with engine.begin() as connection:



            registration_row = (

                connection.execute(

                    text(

                        """

                        INSERT INTO public.registrations (

                            application_id,

                            student_number,

                            course_code,

                            registration_date,

                            registration_status,

                            funding_type,

                            cycle,

                            program_start_date,

                            expected_completion_date

                        )

                        VALUES (

                            :application_id,

                            :student_number,

                            :course_code,

                            CURRENT_DATE,

                            'Registered',

                            :funding_type,

                            :cycle,

                            :program_start_date,

                            :expected_completion_date

                        )

                        RETURNING

                            id,

                            application_id,

                            student_number,

                            course_code,

                            registration_date,

                            registration_status,

                            funding_type,

                            cycle,

                            program_start_date,

                            expected_completion_date,

                            eisa_eligible,

                            created_at,

                            updated_at

                        """

                    ),

                    {

                        "application_id": (

                            application["id"]

                        ),

                        "student_number": (

                            student_number

                        ),

                        "course_code": (

                            qualification_id

                        ),

                        "funding_type": (

                            funding_type

                        ),

                        "cycle": (

                            registration_cycle

                        ),

                        "program_start_date": (

                            program_start_date

                        ),

                        "expected_completion_date": (

                            expected_completion_date

                        ),

                    },

                ).mappings().first()

            )



            if not registration_row:



                raise RuntimeError(

                    "Registration could not "

                    "be created."

                )



            registration_id = (

                registration_row[

                    "id"

                ]

            )



            module_insert = text(

                """

                INSERT INTO public.module_registrations (

                    registration_id,

                    module_id,

                    status

                )

                VALUES (

                    :registration_id,

                    :module_id,

                    'Registered'

                )



                ON CONFLICT (

                    registration_id,

                    module_id

                )

                DO NOTHING

                """

            )



            for module in modules:



                connection.execute(

                    module_insert,

                    {

                        "registration_id": (

                            registration_id

                        ),

                        "module_id": (

                            module["id"]

                        ),

                    },

                )



            # =================================================

            # POPIA DATE = REGISTRATION DATE

            # =================================================



            connection.execute(

                text(

                    """

                    UPDATE public.applications



                    SET

                        popi_date = CURRENT_DATE,

                        updated_at = now()



                    WHERE id = :application_id

                    """

                ),

                {

                    "application_id": (

                        application["id"]

                    ),

                },

            )



    except IntegrityError as error:



        raise ValueError(

            "Registration could not be completed "

            "because of a database constraint."

        ) from error



    registration_data = (

        get_registration(

            student_number

        )

    )



    if not registration_data:



        raise RuntimeError(

            "Registration was created, but "

            "could not be retrieved."

        )



    # ========================================================

    # CREATE STUDENT ACCOUNT

    # ========================================================



    student_account_result = None

    student_account_error = None



    try:



        student_account_result = (

            create_student_account(

                student_number

            )

        )



    except Exception as error:



        student_account_error = (

            str(error)

        )



        print(

            "WARNING: Student account "

            "creation failed: "

            f"{error}"

        )



    # ========================================================

    # GENERATE PROOF OF REGISTRATION

    # ========================================================



    pdf_path = None

    pdf_generated = False

    pdf_error = None



    try:



        pdf_path = (

            generate_proof_of_registration(

                registration_data

            )

        )



        pdf_generated = True



    except Exception as error:



        pdf_error = (

            str(error)

        )



        print(

            "WARNING: Proof of Registration "

            "generation failed: "

            f"{error}"

        )



    # ========================================================

    # EMAIL PROOF OF REGISTRATION

    # ========================================================



    registration = (

        registration_data[

            "registration"

        ]

    )



    student_email = (

        registration.get(

            "email"

        )

    )



    email_sent = False

    email_error = None



    if (

        pdf_generated

        and pdf_path

        and student_email

    ):



        try:



            send_email(

                to_email=(

                    student_email

                ),

                subject=(

                    "Glen Moniques - "

                    "Proof of Registration"

                ),

                body=(

                    build_registration_email_body(

                        registration_data

                    )

                ),

                attachment_path=(

                    pdf_path

                ),

            )



            email_sent = True



        except Exception as error:



            email_error = (

                str(error)

            )



            print(

                "WARNING: Proof of Registration "

                "email failed: "

                f"{error}"

            )



    elif not student_email:



        email_error = (

            "Student email address "

            "is not available."

        )



    elif not pdf_generated:



        email_error = (

            "Email was not sent because "

            "the Proof of Registration "

            "could not be generated."

        )



    return {

        "message": (

            "Student registered successfully."

        ),



        "registration": (

            registration_data[

                "registration"

            ]

        ),



        "modules_registered": len(

            registration_data[

                "modules"

            ]

        ),



        "modules": (

            registration_data[

                "modules"

            ]

        ),



        "student_account": {

            "created": (

                student_account_result

                is not None

            ),



            "details": (

                student_account_result

            ),



            "error": (

                student_account_error

            ),

        },



        "documents": {

            "proof_of_registration": {

                "generated": (

                    pdf_generated

                ),

                "path": (

                    pdf_path

                ),

                "error": (

                    pdf_error

                ),

            }

        },



        "email": {

            "sent": (

                email_sent

            ),

            "recipient": (

                student_email

            ),

            "error": (

                email_error

            ),

        },

    }





# ============================================================

# REGENERATE / RESEND PROOF OF REGISTRATION

# ============================================================



def resend_proof_of_registration(

    student_number: str,

) -> dict:



    registration_data = (

        get_registration(

            student_number

        )

    )



    if not registration_data:



        raise ValueError(

            "Registration not found."

        )



    registration = (

        registration_data[

            "registration"

        ]

    )



    student_email = (

        registration.get(

            "email"

        )

    )



    if not student_email:



        raise ValueError(

            "The student does not have "

            "an email address."

        )



    try:



        pdf_path = (

            generate_proof_of_registration(

                registration_data

            )

        )



    except Exception as error:



        print(

            "ERROR: Proof of Registration "

            "regeneration failed: "

            f"{error}"

        )



        raise RuntimeError(

            "The Proof of Registration "

            "could not be generated."

        ) from error



    try:



        send_email(

            to_email=(

                student_email

            ),

            subject=(

                "Glen Moniques - "

                "Proof of Registration"

            ),

            body=(

                build_por_resend_email_body(

                    registration_data

                )

            ),

            attachment_path=(

                pdf_path

            ),

        )



    except Exception as error:



        print(

            "WARNING: Proof of Registration "

            "was generated but email failed: "

            f"{error}"

        )



        return {

            "student_number": (

                student_number

            ),

            "generated": True,

            "email_sent": False,

            "recipient": (

                student_email

            ),

            "pdf_path": (

                pdf_path

            ),

            "email_error": (

                str(error)

            ),

        }



    return {

        "student_number": (

            student_number

        ),

        "generated": True,

        "email_sent": True,

        "recipient": (

            student_email

        ),

        "pdf_path": (

            pdf_path

        ),

    }





# ============================================================

# GET ENROLMENT FORM DATA

# ============================================================



def get_enrolment_form_data(

    student_number: str,

) -> dict | None:



    query = text(

        """

        SELECT

            r.id

                AS registration_id,



            r.student_number,

            r.course_code,

            r.registration_date,

            r.registration_status,

            r.funding_type,

            r.cycle,

            r.program_start_date,

            r.expected_completion_date,



            a.first_name,

            a.middle_name,

            a.last_name,

            a.title,



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



            a.highest_grade_passed

                AS highest_grade,



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



            c.course_name,

            c.qualification_type,

            c.nqf_level,

            c.credits,

            c.assessment_type,

            c.sdp_code



        FROM public.registrations r



        JOIN public.applications a

            ON a.id = r.application_id



        JOIN public.courses c

            ON c.course_code = r.course_code



        WHERE r.student_number = :student_number



        LIMIT 1

        """

    )



    with engine.connect() as connection:



        row = connection.execute(

            query,

            {

                "student_number": (

                    student_number

                ),

            },

        ).mappings().first()



    return (

        dict(row)

        if row

        else None

    )





# ============================================================

# GENERATE ADMIN ENROLMENT FORM

# ============================================================



def generate_student_enrolment_form(

    student_number: str,

) -> dict:



    enrolment_data = (

        get_enrolment_form_data(

            student_number

        )

    )



    if not enrolment_data:



        raise ValueError(

            "Registration not found."

        )



    try:



        pdf_path = (

            generate_enrolment_form(

                enrolment_data

            )

        )



    except Exception as error:



        print(

            "ERROR: Enrolment Form "

            "generation failed: "

            f"{error}"

        )



        raise RuntimeError(

            "The Enrolment Form "

            "could not be generated."

        ) from error



    return {

        "student_number": (

            student_number

        ),

        "generated": True,

        "pdf_path": (

            pdf_path

        ),

        "admin_document": True,

        "emailed": False,

        "requires_learner_signature": True,

        "requires_physical_learner_signature": True,

    }





# ============================================================

# UPDATE REGISTRATION STATUS

# ============================================================



def update_registration_status(

    student_number: str,

    new_status: str,

) -> dict:



    if (

        new_status

        not in ALLOWED_REGISTRATION_STATUSES

    ):



        raise ValueError(

            f"Invalid registration status: "

            f"{new_status}"

        )



    query = text(

        """

        UPDATE public.registrations



        SET

            registration_status = :new_status,

            updated_at = now()



        WHERE student_number = :student_number



        RETURNING

            id,

            application_id,

            student_number,

            course_code,

            registration_date,

            registration_status,

            funding_type,

            cycle,

            program_start_date,

            expected_completion_date,

            eisa_eligible,

            created_at,

            updated_at

        """

    )



    with engine.begin() as connection:



        row = connection.execute(

            query,

            {

                "student_number": (

                    student_number

                ),

                "new_status": (

                    new_status

                ),

            },

        ).mappings().first()



    if not row:



        raise ValueError(

            "Registration not found."

        )



    return dict(

        row

    )