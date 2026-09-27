from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)


class StaffProfileContactUpdate(
    BaseModel
):
    email: EmailStr | None = None

    phone_number: str | None = Field(
        default=None,
        max_length=50,
    )


class StaffPasswordChange(
    BaseModel
):
    current_password: str = Field(
        ...,
        min_length=1,
    )

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )


class StaffPinChange(
    BaseModel
):
    current_pin: str = Field(
        ...,
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )

    new_pin: str = Field(
        ...,
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )