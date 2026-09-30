from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.application import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationIdentityRequest,
)
from app.models.registration import (
    RegistrationCreate,
    RegistrationStatusUpdate,
)
from app.models.student_auth import (
    StudentPasswordChange,
    StudentPasswordLogin,
    StudentPinLogin,
    StudentPinSetup,
)
from app.services.application_public_service import verify_public_application_identity
from app.services.application_service import (
    change_application_status,
    create_application,
    regenerate_and_resend_acknowledgement,
)
from app.services.registration_service import (
    generate_student_enrolment_form,
    get_registration,
    register_student,
    resend_proof_of_registration,
    update_registration_status,
)
from app.services.student_auth_service import (
    change_student_password,
    create_student_account,
    login_with_password,
    login_with_pin,
    reissue_temporary_password,
    setup_student_pin,
)
from app.services.student_portal_service import (
    get_student_profile,
)
from app.student_auth_dependency import (
    require_full_student_access,
)

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api",
)


# ============================================================
# APPLICATIONS
# ============================================================


@router.post(
    "/applications",
    tags=["Applications"],
)
def submit_application(
    application: ApplicationCreate,
):

    try:

        result = create_application(
            application.model_dump()
        )

        return {
            "success": True,
            "message": (
                "Application submitted successfully."
            ),
            "application": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Application submission failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The application could not "
                "be submitted."
            ),
        )


@router.post(
    "/applications/"
    "{student_number}/"
    "acknowledgement/resend",
    tags=["Applications"],
)
def resend_application_acknowledgement(
    student_number: str,
    identity: ApplicationIdentityRequest,
):

    try:

        verify_public_application_identity(
            student_number,
            identity.national_id,
        )


        result = (
            regenerate_and_resend_acknowledgement(
                student_number
            )
        )

        return {
            "success": True,
            "message": (
                "Application acknowledgement "
                "regenerated and resent successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        if (
            str(error)
            == "Application not found."
        ):

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Application acknowledgement "
            "resend failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The acknowledgement could not "
                "be regenerated or resent."
            ),
        )


@router.patch(
    "/applications/"
    "{student_number}/status",
    tags=["Applications"],
)
def update_application_status(
    student_number: str,
    status_update: ApplicationStatusUpdate,
):

    try:

        result = (
            change_application_status(
                student_number=(
                    student_number
                ),
                new_status=(
                    status_update.status
                ),
                outstanding_documents=(
                    status_update
                    .outstanding_documents
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Application status processed "
                "successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        if (
            str(error)
            == "Application not found."
        ):

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Application status "
            "update failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The application status "
                "could not be updated."
            ),
        )


# ============================================================
# REGISTRATIONS
# ============================================================


@router.post(
    "/registrations",
    tags=["Registrations"],
)
def create_registration(
    registration: RegistrationCreate,
):

    try:

        result = register_student(
            student_number=(
                registration.student_number
            ),
            funding_type=(
                registration.funding_type
            ),
            cycle=(
                registration.cycle
            ),
            program_start_date=(
                registration
                .program_start_date
            ),
            expected_completion_date=(
                registration
                .expected_completion_date
            ),
        )

        return {
            "success": True,
            "message": (
                "Student registered successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        if (
            str(error)
            == "Application not found."
        ):

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Student registration failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The student could not "
                "be registered."
            ),
        )


@router.get(
    "/registrations/"
    "{student_number}",
    tags=["Registrations"],
)
def read_registration(
    student_number: str,
):

    try:

        result = get_registration(
            student_number
        )

        if not result:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Registration not found."
                ),
            )

        return {
            "success": True,
            "registration": result,
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Registration lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The registration could not "
                "be retrieved."
            ),
        )


@router.post(
    "/registrations/"
    "{student_number}/"
    "proof-of-registration/resend",
    tags=["Registrations"],
)
def resend_registration_por(
    student_number: str,
):

    try:

        result = (
            resend_proof_of_registration(
                student_number
            )
        )

        return {
            "success": True,
            "message": (
                "Proof of Registration processed."
            ),
            "result": result,
        }

    except ValueError as error:

        if (
            str(error)
            == "Registration not found."
        ):

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Proof of Registration "
            "resend failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The Proof of Registration "
                "could not be regenerated."
            ),
        )


@router.post(
    "/registrations/"
    "{student_number}/"
    "enrolment-form/generate",
    tags=["Registrations"],
)
def generate_enrolment_document(
    student_number: str,
):

    try:

        result = (
            generate_student_enrolment_form(
                student_number
            )
        )

        return {
            "success": True,
            "message": (
                "Enrolment Form generated "
                "successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        if (
            str(error)
            == "Registration not found."
        ):

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Enrolment Form "
            "generation failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The Enrolment Form "
                "could not be generated."
            ),
        )


@router.patch(
    "/registrations/"
    "{student_number}/status",
    tags=["Registrations"],
)
def change_registration_status(
    student_number: str,
    status_update: RegistrationStatusUpdate,
):

    try:

        result = (
            update_registration_status(
                student_number=(
                    student_number
                ),
                new_status=(
                    status_update.status
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Registration status "
                "updated successfully."
            ),
            "registration": result,
        }

    except ValueError as error:

        if (
            str(error)
            == "Registration not found."
        ):

            raise HTTPException(
                status_code=404,
                detail=str(error),
            )

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Registration status "
            "update failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The registration status "
                "could not be updated."
            ),
        )


# ============================================================
# STUDENT AUTHENTICATION
# ============================================================


@router.post(
    "/student-auth/"
    "{student_number}/"
    "issue-account",
    tags=["Student Authentication"],
)
def issue_existing_student_account(
    student_number: str,
):

    try:

        result = (
            create_student_account(
                student_number
            )
        )

        return {
            "success": True,
            "message": (
                "Student account created "
                "successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Student account "
            "creation failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student account could "
                "not be created."
            ),
        )


@router.post(
    "/student-auth/"
    "{student_number}/"
    "reissue-temporary-password",
    tags=["Student Authentication"],
)
def reissue_student_password(
    student_number: str,
):

    try:

        result = (
            reissue_temporary_password(
                student_number
            )
        )

        return {
            "success": True,
            "message": (
                "Temporary password "
                "reissued successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Temporary password "
            "reissue failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Temporary password could "
                "not be reissued."
            ),
        )


@router.post(
    "/student-auth/setup-pin",
    tags=["Student Authentication"],
)
def create_student_pin(
    request: StudentPinSetup,
):

    try:

        result = (
            setup_student_pin(
                student_number=(
                    request.student_number
                ),
                password=(
                    request.password
                ),
                pin=(
                    request.pin
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Student PIN created "
                "successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Student PIN setup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student PIN could not "
                "be created."
            ),
        )


@router.post(
    "/student-auth/login/password",
    tags=["Student Authentication"],
)
def student_password_login(
    request: StudentPasswordLogin,
):

    try:

        result = (
            login_with_password(
                student_number=(
                    request.student_number
                ),
                password=(
                    request.password
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Password login successful."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=401,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Student password "
            "login failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student login could "
                "not be completed."
            ),
        )


@router.post(
    "/student-auth/login/pin",
    tags=["Student Authentication"],
)
def student_pin_login(
    request: StudentPinLogin,
):

    try:

        result = (
            login_with_pin(
                student_number=(
                    request.student_number
                ),
                pin=(
                    request.pin
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "PIN login successful."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=401,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Student PIN login failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student login could "
                "not be completed."
            ),
        )


@router.post(
    "/student-auth/change-password",
    tags=["Student Authentication"],
)
def update_student_password(
    request: StudentPasswordChange,
):

    try:

        result = (
            change_student_password(
                student_number=(
                    request.student_number
                ),
                current_password=(
                    request.current_password
                ),
                new_password=(
                    request.new_password
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Password changed successfully."
            ),
            "result": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            "ERROR: Student password "
            "change failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student password could "
                "not be changed."
            ),
        )


@router.get(
    "/student-auth/me",
    tags=["Student Authentication"],
)
def student_me(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    return {
        "success": True,
        "student": (
            current_student
        ),
    }


# ============================================================
# STUDENT PORTAL
# ============================================================


@router.get(
    "/student/profile",
    tags=["Student Portal"],
)
def student_profile(
    current_student: dict = Depends(
        require_full_student_access
    ),
):

    student_number = (
        current_student[
            "student_number"
        ]
    )

    try:

        profile = (
            get_student_profile(
                student_number
            )
        )

        if not profile:

            raise HTTPException(
                status_code=404,
                detail=(
                    "Student profile not found."
                ),
            )

        return {
            "success": True,

            "student_number": (
                student_number
            ),

            "profile": (
                profile
            ),
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "ERROR: Student profile "
            "lookup failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Student profile could "
                "not be retrieved."
            ),
        )