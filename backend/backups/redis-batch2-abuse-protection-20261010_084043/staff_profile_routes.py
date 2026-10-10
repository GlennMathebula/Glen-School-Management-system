from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from app.models.staff_profile import (
    StaffPasswordChange,
    StaffPinChange,
    StaffProfileContactUpdate,
)

from app.services.staff_profile_service import (
    change_staff_password,
    change_staff_pin,
    get_staff_profile,
    update_staff_contact_details,
)

from app.staff_auth_dependency import (
    get_current_staff,
)


router = APIRouter(
    prefix="/api/staff/profile",
    tags=[
        "Staff Profile",
    ],
)


@router.get("")
def staff_profile(
    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        profile = get_staff_profile(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),
        )

        return {
            "success": True,
            "data": profile,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff profile could "
            "not be loaded: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Staff profile could not "
                "be loaded."
            ),
        ) from error


@router.patch(
    "/contact"
)
def staff_update_contact(
    payload: StaffProfileContactUpdate,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        profile = (
            update_staff_contact_details(
                staff_code=(
                    current_staff[
                        "staff_code"
                    ]
                ),

                email=(
                    payload.email
                ),

                phone_number=(
                    payload.phone_number
                ),
            )
        )

        return {
            "success": True,
            "message": (
                "Contact details updated "
                "successfully."
            ),
            "data": profile,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff contact update "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Contact details could not "
                "be updated."
            ),
        ) from error


@router.post(
    "/change-password"
)
def staff_change_password(
    payload: StaffPasswordChange,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        result = change_staff_password(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),

            current_password=(
                payload.current_password
            ),

            new_password=(
                payload.new_password
            ),
        )

        return {
            "success": True,
            "message": (
                "Password changed "
                "successfully."
            ),
            "data": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff password change "
            "failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Password could not "
                "be changed."
            ),
        ) from error


@router.post(
    "/change-pin"
)
def staff_change_pin(
    payload: StaffPinChange,

    current_staff: dict = Depends(
        get_current_staff
    ),
):

    try:

        result = change_staff_pin(
            staff_code=(
                current_staff[
                    "staff_code"
                ]
            ),

            current_pin=(
                payload.current_pin
            ),

            new_pin=(
                payload.new_pin
            ),
        )

        return {
            "success": True,
            "message": (
                "PIN changed successfully."
            ),
            "data": result,
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:

        print(
            "ERROR: Staff PIN change failed: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "PIN could not be changed."
            ),
        ) from error