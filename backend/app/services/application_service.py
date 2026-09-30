import json

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.database import engine
from app.services.email_service import send_email
from app.services.pdf_service import (
    generate_acceptance_letter,
    generate_application_acknowledgement,
    generate_outstanding_documents_letter,
    generate_rejection_letter,
)
from app.services.application_public_service import enrich_public_application_payload
from app.services.student_number import generate_student_number
from app.utils.sa_id import validate_sa_id

# ============================================================
# CREATE APPLICATION
# ============================================================

def create_application(
    application_data: dict,
) -> dict:

    application_data = enrich_public_application_payload(
        dict(application_data)
    )


    id_result = validate_sa_id(
        application_data["national_id"]
    )

    if not id_result["valid"]:
        raise ValueError(
            id_result["message"]
        )

    email = (
        application_data["email"]
        .strip()
        .lower()
    )

    national_id = (
        application_data["national_id"]
        .strip()
    )

    application_data["email"] = email
    application_data["national_id"] = national_id

    # ---------------------------------------------------------
    # Check duplicate email and ID
    # ---------------------------------------------------------
    with engine.connect() as connection:

        existing_email = connection.execute(
            text("""
                SELECT id
                FROM public.applications
                WHERE LOWER(TRIM(email)) = :email
                LIMIT 1
            """),
            {
                "email": email
            },
        ).first()

        if existing_email:
            raise ValueError(
                "An application already exists for "
                "the information provided."
            )

        existing_id = connection.execute(
            text("""
                SELECT id
                FROM public.applications
                WHERE TRIM(national_id) = :national_id
                LIMIT 1
            """),
            {
                "national_id": national_id
            },
        ).first()

        if existing_id:
            raise ValueError(
                "An application already exists for "
                "the information provided."
            )

    # ---------------------------------------------------------
    # Generate student number
    # ---------------------------------------------------------
    student_number = generate_student_number()

    application_data["student_number"] = (
        student_number
    )

    application_data["app_status"] = (
        "Pending"
    )

    # ---------------------------------------------------------
    # Insert application
    # ---------------------------------------------------------
    columns = list(
        application_data.keys()
    )

    column_names = ", ".join(
        columns
    )

    parameter_names = ", ".join(
        f":{column}"
        for column in columns
    )

    insert_query = text(f"""
        INSERT INTO public.applications (
            {column_names}
        )
        VALUES (
            {parameter_names}
        )
        RETURNING id
    """)

    try:
        with engine.begin() as connection:

            result = connection.execute(
                insert_query,
                application_data,
            )

            application_id = (
                result.scalar_one()
            )

    except IntegrityError:
        raise ValueError(
            "The application could not be created "
            "because a duplicate record already exists."
        )

    # ---------------------------------------------------------
    # Fetch complete application
    # ---------------------------------------------------------
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM public.applications
                WHERE id = :application_id
                LIMIT 1
            """),
            {
                "application_id": application_id
            },
        )

        application = (
            result
            .mappings()
            .first()
        )

    if not application:
        raise ValueError(
            "Application was created but could "
            "not be retrieved."
        )

    application = dict(
        application
    )

    # ---------------------------------------------------------
    # Generate acknowledgement PDF
    # ---------------------------------------------------------
    try:
        pdf_path = (
            generate_application_acknowledgement(
                application
            )
        )

        application["pdf_path"] = pdf_path
        application["pdf_generated"] = True

    except Exception as error:
        print(
            "WARNING: Application created successfully, "
            "but acknowledgement PDF could not be generated: "
            f"{error}"
        )

        application["pdf_path"] = None
        application["pdf_generated"] = False

    # ---------------------------------------------------------
    # Prepare acknowledgement email
    # ---------------------------------------------------------
    email_subject = (
        "Glen Moniques - "
        "Application Submitted Successfully"
    )

    email_body = f"""
Dear {application["first_name"]} {application["last_name"]},

Thank you for submitting your application to Glen Moniques.

Your application has been successfully received and recorded in our Student Management System.

Student Number: {application["student_number"]}

Application Status: {application["app_status"]}

Please keep your student number safe, as it will be used to identify your application and future student records.

Your application acknowledgement is attached to this email.

Our admissions team will review your application and communicate with you regarding the next steps.

Kind regards,

Glen Moniques (Pty) Ltd

Email: admin@glenmoniques.co.za
Website: www.glenmoniques.co.za
""".strip()

    # ---------------------------------------------------------
    # Send acknowledgement email
    # ---------------------------------------------------------
    try:
        send_email(
            recipient_email=application["email"],
            subject=email_subject,
            html_body=email_body.replace("\n", "<br>"),
            text_body=email_body,
            attachment_path=application.get(
                "pdf_path"
            ),
        )

        application["email_sent"] = True

    except Exception as error:
        print(
            "WARNING: Application created successfully, "
            "but confirmation email could not be sent: "
            f"{error}"
        )

        application["email_sent"] = False

    return application


# ============================================================
# REGENERATE + RESEND ACKNOWLEDGEMENT
# ============================================================

def regenerate_and_resend_acknowledgement(
    student_number: str,
) -> dict:

    student_number = student_number.strip()

    if not student_number:
        raise ValueError(
            "Student number is required."
        )

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM public.applications
                WHERE student_number = :student_number
                LIMIT 1
            """),
            {
                "student_number": student_number
            },
        )

        application = (
            result
            .mappings()
            .first()
        )

    if not application:
        raise ValueError(
            "Application not found."
        )

    application = dict(
        application
    )

    applicant_email = application.get(
        "email"
    )

    if not applicant_email:
        raise ValueError(
            "The applicant does not have an "
            "email address recorded in the system."
        )

    # ---------------------------------------------------------
    # Generate acknowledgement
    # ---------------------------------------------------------
    try:
        pdf_path = (
            generate_application_acknowledgement(
                application
            )
        )

    except Exception as error:
        raise ValueError(
            "The acknowledgement PDF could not "
            "be generated: "
            f"{error}"
        )

    # ---------------------------------------------------------
    # Prepare resend email
    # ---------------------------------------------------------
    email_subject = (
        "Glen Moniques - "
        "Application Acknowledgement"
    )

    email_body = f"""
Dear {application["first_name"]} {application["last_name"]},

Please find attached your regenerated Glen Moniques application acknowledgement.

Student Number: {application["student_number"]}

Application Status: {application["app_status"]}

Please retain this document and your student number for future reference.

Kind regards,

Glen Moniques (Pty) Ltd

Email: admin@glenmoniques.co.za
Website: www.glenmoniques.co.za
""".strip()

    # ---------------------------------------------------------
    # Send resend email
    # ---------------------------------------------------------
    try:
        send_email(
            recipient_email=applicant_email,
            subject=email_subject,
            html_body=email_body.replace("\n", "<br>"),
            text_body=email_body,
            attachment_path=pdf_path,
        )

    except Exception as error:
        raise ValueError(
            "The acknowledgement PDF was generated, "
            "but the email could not be sent: "
            f"{error}"
        )

    return {
        "student_number": application[
            "student_number"
        ],
        "pdf_path": pdf_path,
        "pdf_generated": True,
        "email": applicant_email,
        "email_sent": True,
    }


# ============================================================
# CHANGE APPLICATION STATUS
# ============================================================

def change_application_status(
    student_number: str,
    new_status: str,
    outstanding_documents: list[str] | None = None,
) -> dict:

    student_number = (
        student_number.strip()
    )

    new_status = (
        new_status.strip()
    )

    allowed_statuses = {
        "Pending",
        "Accepted",
        "Rejected",
        "Outstanding Documents",
    }

    if new_status not in allowed_statuses:
        raise ValueError(
            "Invalid application status."
        )

    # ---------------------------------------------------------
    # Clean outstanding document list
    # ---------------------------------------------------------
    cleaned_documents = []

    if outstanding_documents:
        for item in outstanding_documents:

            item = item.strip()

            if (
                item
                and item not in cleaned_documents
            ):
                cleaned_documents.append(
                    item
                )

    if (
        new_status == "Outstanding Documents"
        and not cleaned_documents
    ):
        raise ValueError(
            "Please select at least one "
            "outstanding document."
        )

    # ---------------------------------------------------------
    # Fetch existing application
    # ---------------------------------------------------------
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM public.applications
                WHERE student_number = :student_number
                LIMIT 1
            """),
            {
                "student_number": student_number
            },
        )

        existing_application = (
            result
            .mappings()
            .first()
        )

    if not existing_application:
        raise ValueError(
            "Application not found."
        )

    existing_application = dict(
        existing_application
    )

    old_status = existing_application.get(
        "app_status"
    )

    # ---------------------------------------------------------
    # Prevent duplicate Accepted/Rejected processing
    # ---------------------------------------------------------
    if (
        old_status == new_status
        and new_status != "Outstanding Documents"
    ):
        return {
            "student_number": student_number,
            "old_status": old_status,
            "new_status": new_status,
            "status_changed": False,
            "message": (
                "Application already has this status."
            ),
        }

    status_changed = (
        old_status != new_status
    )

    # ---------------------------------------------------------
    # Update database
    # ---------------------------------------------------------
    if new_status == "Outstanding Documents":

        documents_json = json.dumps(
            cleaned_documents
        )

        with engine.begin() as connection:

            connection.execute(
                text("""
                    UPDATE public.applications
                    SET
                        app_status = :new_status,
                        outstanding_documents =
                            CAST(
                                :outstanding_documents
                                AS jsonb
                            ),
                        updated_at = now()
                    WHERE student_number = :student_number
                """),
                {
                    "new_status": new_status,
                    "outstanding_documents": (
                        documents_json
                    ),
                    "student_number": (
                        student_number
                    ),
                },
            )

    else:

        with engine.begin() as connection:

            connection.execute(
                text("""
                    UPDATE public.applications
                    SET
                        app_status = :new_status,
                        updated_at = now()
                    WHERE student_number = :student_number
                """),
                {
                    "new_status": new_status,
                    "student_number": student_number,
                },
            )

    # ---------------------------------------------------------
    # Fetch updated application
    # ---------------------------------------------------------
    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT *
                FROM public.applications
                WHERE student_number = :student_number
                LIMIT 1
            """),
            {
                "student_number": student_number
            },
        )

        application = (
            result
            .mappings()
            .first()
        )

    if not application:
        raise ValueError(
            "Application could not be retrieved "
            "after the status update."
        )

    application = dict(
        application
    )

    document_generated = False
    email_sent = False
    pdf_path = None
    document_type = None

    # ========================================================
    # ACCEPTED
    # ========================================================

    if new_status == "Accepted":

        document_type = (
            "Acceptance Letter"
        )

        try:
            pdf_path = (
                generate_acceptance_letter(
                    application
                )
            )

            document_generated = True

        except Exception as error:
            print(
                "WARNING: Acceptance letter could "
                "not be generated: "
                f"{error}"
            )

        if document_generated:

            applicant_email = (
                application.get("email")
            )

            if applicant_email:

                email_subject = (
                    "Glen Moniques - "
                    "Application Accepted"
                )

                email_body = f"""
Dear {application["first_name"]} {application["last_name"]},

We are pleased to inform you that your application to Glen Moniques has been accepted.

Student Number: {application["student_number"]}

Application Status: Accepted

Your official Letter of Acceptance is attached to this email.

Our admissions team will communicate with you regarding registration and the next steps.

Kind regards,

Glen Moniques (Pty) Ltd

Email: admin@glenmoniques.co.za
Website: www.glenmoniques.co.za
""".strip()

                try:
                    send_email(
                        recipient_email=applicant_email,
                        subject=email_subject,
                        html_body=email_body.replace("\n", "<br>"),
                        text_body=email_body,
                        attachment_path=pdf_path,
                    )

                    email_sent = True

                except Exception as error:
                    print(
                        "WARNING: Acceptance email "
                        "could not be sent: "
                        f"{error}"
                    )

    # ========================================================
    # REJECTED
    # ========================================================

    elif new_status == "Rejected":

        document_type = (
            "Rejection Letter"
        )

        try:
            pdf_path = (
                generate_rejection_letter(
                    application
                )
            )

            document_generated = True

        except Exception as error:
            print(
                "WARNING: Rejection letter could "
                "not be generated: "
                f"{error}"
            )

        if document_generated:

            applicant_email = (
                application.get("email")
            )

            if applicant_email:

                email_subject = (
                    "Glen Moniques - "
                    "Application Outcome"
                )

                email_body = f"""
Dear {application["first_name"]} {application["last_name"]},

Thank you for your application to Glen Moniques.

Your application has been reviewed and an outcome has been recorded.

Student Number: {application["student_number"]}

Application Status: Rejected

Please find your official application outcome letter attached to this email.

We appreciate your interest in Glen Moniques.

Kind regards,

Glen Moniques (Pty) Ltd

Email: admin@glenmoniques.co.za
Website: www.glenmoniques.co.za
""".strip()

                try:
                    send_email(
                        recipient_email=applicant_email,
                        subject=email_subject,
                        html_body=email_body.replace("\n", "<br>"),
                        text_body=email_body,
                        attachment_path=pdf_path,
                    )

                    email_sent = True

                except Exception as error:
                    print(
                        "WARNING: Rejection email "
                        "could not be sent: "
                        f"{error}"
                    )

    # ========================================================
    # OUTSTANDING DOCUMENTS
    # ========================================================

    elif new_status == "Outstanding Documents":

        document_type = (
            "Outstanding Documents Letter"
        )

        try:
            pdf_path = (
                generate_outstanding_documents_letter(
                    application,
                    cleaned_documents,
                )
            )

            document_generated = True

        except Exception as error:
            print(
                "WARNING: Outstanding documents "
                "letter could not be generated: "
                f"{error}"
            )

        if document_generated:

            applicant_email = (
                application.get("email")
            )

            if applicant_email:

                document_lines = "\n".join(
                    f"- {item}"
                    for item in cleaned_documents
                )

                email_subject = (
                    "Glen Moniques - "
                    "Outstanding Application Documents"
                )

                email_body = f"""
Dear {application["first_name"]} {application["last_name"]},

Your Glen Moniques application requires additional documentation before the assessment process can be completed.

Student Number: {application["student_number"]}

Application Status: Outstanding Documents

The following documents are outstanding:

{document_lines}

Please submit the required documents as soon as possible.

Your official Outstanding Documents Letter is attached to this email.

Kind regards,

Glen Moniques (Pty) Ltd

Email: admin@glenmoniques.co.za
Website: www.glenmoniques.co.za
""".strip()

                try:
                    send_email(
                        recipient_email=applicant_email,
                        subject=email_subject,
                        html_body=email_body.replace("\n", "<br>"),
                        text_body=email_body,
                        attachment_path=pdf_path,
                    )

                    email_sent = True

                except Exception as error:
                    print(
                        "WARNING: Outstanding documents "
                        "email could not be sent: "
                        f"{error}"
                    )

    # ---------------------------------------------------------
    # Return result
    # ---------------------------------------------------------
    return {
        "student_number": student_number,
        "old_status": old_status,
        "new_status": new_status,
        "status_changed": status_changed,
        "document_type": document_type,
        "document_generated": (
            document_generated
        ),
        "pdf_path": pdf_path,
        "email_sent": email_sent,
        "outstanding_documents": (
            cleaned_documents
            if new_status == "Outstanding Documents"
            else None
        ),
    }