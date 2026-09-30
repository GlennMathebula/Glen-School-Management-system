from pydantic import BaseModel, Field


class PrincipalStaffContactUpdate(BaseModel):
    email: str | None = Field(
        default=None,
        max_length=255,
    )
    cell_number: str | None = Field(
        default=None,
        max_length=50,
    )
    phone_number: str | None = Field(
        default=None,
        max_length=50,
    )


class PrincipalStaffCredentialReset(BaseModel):
    temporary_password: str = Field(
        min_length=8,
        max_length=255,
    )
    temporary_pin: str = Field(
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
    )


class PrincipalStaffSupportCreate(BaseModel):
    subject: str = Field(
        min_length=3,
        max_length=200,
    )
    category: str = Field(
        min_length=2,
        max_length=100,
    )
    description: str = Field(
        min_length=3,
        max_length=5000,
    )
    priority: str = Field(
        default="Normal",
        max_length=20,
    )


class PrincipalSupportTicketUpdate(BaseModel):
    status: str | None = Field(
        default=None,
        max_length=30,
    )
    priority: str | None = Field(
        default=None,
        max_length=20,
    )
    assigned_to_staff_code: str | None = Field(
        default=None,
        max_length=30,
    )
    resolution: str | None = Field(
        default=None,
        max_length=5000,
    )
