from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RegistrationStatus = Literal[
    "Registered",
    "In Progress",
    "Suspended",
    "Withdrawn",
    "Cancelled",
    "Completed",
]


class AdminStudentRecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, max_length=200)
    middle_name: str | None = Field(default=None, max_length=200)
    last_name: str | None = Field(default=None, max_length=200)
    national_id: str | None = Field(default=None, max_length=50)
    alternate_id: str | None = Field(default=None, max_length=100)
    birth_date: date | None = None
    email: str | None = Field(default=None, max_length=320)
    cell_number: str | None = Field(default=None, max_length=50)
    phone_number: str | None = Field(default=None, max_length=50)
    home_addr_1: str | None = Field(default=None, max_length=300)
    home_addr_2: str | None = Field(default=None, max_length=300)
    home_addr_3: str | None = Field(default=None, max_length=300)
    home_postal_code: str | None = Field(default=None, max_length=20)
    postal_addr_1: str | None = Field(default=None, max_length=300)
    postal_addr_2: str | None = Field(default=None, max_length=300)
    postal_addr_3: str | None = Field(default=None, max_length=300)
    postal_code: str | None = Field(default=None, max_length=20)
    province_code: str | None = Field(default=None, max_length=100)
    municipality: str | None = Field(default=None, max_length=200)
    ward: str | None = Field(default=None, max_length=100)
    next_of_kin_surname: str | None = Field(default=None, max_length=200)
    next_of_kin_full_name: str | None = Field(default=None, max_length=300)
    next_of_kin_cell: str | None = Field(default=None, max_length=50)
    next_of_kin_relationship: str | None = Field(default=None, max_length=100)
    next_of_kin_email: str | None = Field(default=None, max_length=320)
    registration_status: RegistrationStatus | None = None
