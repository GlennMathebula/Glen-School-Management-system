from datetime import date

from pydantic import BaseModel, Field


class CompletionStatusUpdate(BaseModel):
    completion_status: str = Field(min_length=2, max_length=80)
    completion_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class CertificationUpdate(BaseModel):
    certificate_status: str = Field(min_length=2, max_length=80)
    certificate_number: str | None = Field(default=None, max_length=150)
    certificate_date: date | None = None
    certificate_received_date: date | None = None
    certificate_issued_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class GraduationUpdate(BaseModel):
    graduation_status: str = Field(min_length=2, max_length=80)
    graduation_date: date | None = None
    notes: str | None = Field(default=None, max_length=4000)


class SystemSettingUpdate(BaseModel):
    value: str = Field(max_length=10000)


class StaffAccountCreate(BaseModel):
    employee_id: str
    staff_code: str = Field(min_length=3, max_length=30)
    role_code: str = Field(min_length=2, max_length=50)
    temporary_password: str = Field(min_length=8, max_length=255)
    temporary_pin: str = Field(pattern=r"^\d{5}$")


class StaffAccountStatusUpdate(BaseModel):
    is_active: bool


class RolePermissionsUpdate(BaseModel):
    permission_codes: list[str] = Field(default_factory=list, max_length=100)


class StudentSupportReply(BaseModel):
    message_body: str = Field(min_length=1, max_length=10000)


class StudentSupportStatusUpdate(BaseModel):
    status: str = Field(min_length=2, max_length=80)
