from pydantic import BaseModel, Field


class StaffLoginRequest(BaseModel):
    staff_code: str = Field(
        min_length=3,
        max_length=30,
    )

    password: str = Field(
        min_length=1,
        max_length=255,
    )

    pin: str = Field(
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )


class StaffTemporaryCredentialsChangeRequest(
    BaseModel
):
    challenge_token: str = Field(
        min_length=1,
    )

    new_password: str = Field(
        min_length=8,
        max_length=255,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=255,
    )

    new_pin: str = Field(
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )

    confirm_pin: str = Field(
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )


class StaffOtpVerifyRequest(BaseModel):
    challenge_token: str = Field(
        min_length=1,
    )

    otp: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
    )


class StaffOtpResendRequest(BaseModel):
    challenge_token: str = Field(
        min_length=1,
    )