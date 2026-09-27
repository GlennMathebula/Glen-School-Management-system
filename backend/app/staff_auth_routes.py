from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.staff_auth import (
    StaffLoginRequest,
    StaffOtpResendRequest,
    StaffOtpVerifyRequest,
    StaffTemporaryCredentialsChangeRequest,
)
from app.services.staff_auth_service import (
    change_temporary_staff_credentials,
    get_staff_profile,
    login_staff,
    resend_staff_otp,
    verify_staff_otp,
)
from app.staff_auth_dependency import (
    get_current_staff,
)

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/staff-auth",
    tags=[
        "Staff Authentication"
    ],
)


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login"
)
def staff_login(
    payload: StaffLoginRequest,
):

    try:

        return login_staff(
            staff_code=(
                payload.staff_code
            ),
            password=(
                payload.password
            ),
            pin=(
                payload.pin
            ),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff login failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff login could not "
                "be completed."
            ),
        ) from error


# ============================================================
# CHANGE TEMPORARY CREDENTIALS
# ============================================================

@router.post(
    "/change-temporary-credentials"
)
def change_staff_temporary_credentials(
    payload: (
        StaffTemporaryCredentialsChangeRequest
    ),
):

    try:

        return (
            change_temporary_staff_credentials(
                challenge_token=(
                    payload.challenge_token
                ),
                new_password=(
                    payload.new_password
                ),
                confirm_password=(
                    payload.confirm_password
                ),
                new_pin=(
                    payload.new_pin
                ),
                confirm_pin=(
                    payload.confirm_pin
                ),
            )
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff temporary credential "
            "change failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Temporary staff credentials "
                "could not be changed."
            ),
        ) from error


# ============================================================
# VERIFY OTP
# ============================================================

@router.post(
    "/verify-otp"
)
def verify_staff_login_otp(
    payload: StaffOtpVerifyRequest,
):

    try:

        return verify_staff_otp(
            challenge_token=(
                payload.challenge_token
            ),
            otp=(
                payload.otp
            ),
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff OTP verification "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff OTP verification "
                "could not be completed."
            ),
        ) from error


# ============================================================
# RESEND OTP
# ============================================================

@router.post(
    "/resend-otp"
)
def resend_staff_login_otp(
    payload: StaffOtpResendRequest,
):

    try:

        return resend_staff_otp(
            payload.challenge_token
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff OTP resend failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff OTP could not be resent."
            ),
        ) from error


# ============================================================
# CURRENT STAFF
# ============================================================

@router.get(
    "/me"
)
def current_staff_profile(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        return get_staff_profile(
            current_staff[
                "staff_account_id"
            ]
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff profile failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff profile could not "
                "be loaded."
            ),
        ) from error