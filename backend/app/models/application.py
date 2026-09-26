from datetime import date

from pydantic import BaseModel, EmailStr, Field


class ApplicationCreate(BaseModel):
    sdp_code: str = Field(
        min_length=1,
        max_length=100,
    )

    qualification_id: str | None = None

    national_id: str = Field(
        min_length=13,
        max_length=13,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    middle_name: str | None = None
    title: str | None = None

    birth_date: date | None = None

    home_addr_1: str | None = None
    home_addr_2: str | None = None
    home_addr_3: str | None = None
    home_postal_code: str | None = None

    postal_addr_1: str | None = None
    postal_addr_2: str | None = None
    postal_addr_3: str | None = None
    postal_code: str | None = None

    phone_number: str | None = None
    cell_number: str | None = None

    email: EmailStr

    province_code: str | None = None
    home_language: str | None = None
    gender_code: str | None = None
    nationality_code: str | None = None
    citizen_status: str | None = None

    disability_status: str | None = None
    disability_rating: str | None = None

    highest_grade_passed: str | None = None
    school_name: str | None = None
    year_completed: int | None = None
    academic_subjects: str | None = None

    popi_agree: bool

    next_of_kin_surname: str | None = None
    next_of_kin_full_name: str | None = None
    next_of_kin_cell: str | None = None
    next_of_kin_relationship: str | None = None
    next_of_kin_email: EmailStr | None = None


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=50,
    )

    outstanding_documents: list[str] | None = None