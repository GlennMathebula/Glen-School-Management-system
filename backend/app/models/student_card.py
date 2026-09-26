from pydantic import BaseModel


class StudentCardAvatarResponse(
    BaseModel
):

    success: bool

    message: str

    avatar_available: bool


class StudentCardVerificationResponse(
    BaseModel
):

    valid: bool

    card_status: str | None = None

    student_number: str | None = None

    student_name: str | None = None

    course_code: str | None = None

    course_name: str | None = None

    nqf_level: int | None = None

    cycle: str | None = None

    issued_date: str | None = None

    expiry_date: str | None = None

    reason: str | None = None