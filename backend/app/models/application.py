from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


class ApplicationCreate(BaseModel):
    sdp_code: str = Field(
        min_length=1,
        max_length=100,
    )

    qualification_id: str = Field(
        min_length=1,
        max_length=100,
    )

    # Glen Moniques current public application flow requires
    # a valid 13-digit South African ID number.
    national_id: str = Field(
        min_length=13,
        max_length=13,
        pattern=r"^\d{13}$",
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

    title: Literal[
        "Mr",
        "Mrs",
        "Ms",
        "Miss",
        "Dr",
        "Prof",
    ]

    birth_date: date

    equity_code: Literal[
        "BA",
        "BC",
        "BI",
        "Oth",
        "U",
        "Wh",
    ]

    nationality_code: Literal[
        "U",
        "SA",
        "SDC",
        "NAM",
        "BOT",
        "ZIM",
        "ANG",
        "MOZ",
        "LES",
        "SWA",
        "MAL",
        "ZAM",
        "MAU",
        "TAN",
        "SEY",
        "ZAI",
        "ROA",
        "EUR",
        "AIS",
        "NOR",
        "SOU",
        "AUS",
        "OOC",
        "NOT",
    ]

    home_language: Literal[
        "Eng",
        "Afr",
        "Oth",
        "SASL",
        "Sep",
        "Ses",
        "Set",
        "Swa",
        "Tsh",
        "Xho",
        "Xit",
        "Zul",
        "Nde",
    ]

    gender_code: Literal[
        "M",
        "F",
    ]

    citizen_status: Literal[
        "SA",
        "O",
        "D",
        "PR",
        "U",
    ]

    socioeconomic_code: Literal[
        "01",
        "02",
        "03",
        "04",
        "06",
        "07",
        "08",
        "09",
        "10",
        "97",
        "98",
        "U",
    ]

    disability_status: Literal[
        "N",
        "01",
        "02",
        "03",
        "04",
        "05",
        "06",
        "07",
        "09",
    ]

    disability_rating: Literal[
        "01",
        "02",
        "03",
        "04",
        "06",
        "60",
        "70",
        "80",
    ] | None = None

    immigrant_status: Literal[
        "01",
        "02",
        "03",
    ]

    home_addr_1: str = Field(
        min_length=1,
        max_length=255,
    )

    home_addr_2: str = Field(
        min_length=1,
        max_length=255,
    )

    home_addr_3: str | None = None

    home_postal_code: str = Field(
        pattern=r"^\d{4}$",
    )

    postal_addr_1: str = Field(
        min_length=1,
        max_length=255,
    )

    postal_addr_2: str = Field(
        min_length=1,
        max_length=255,
    )

    postal_addr_3: str | None = None

    postal_code: str = Field(
        pattern=r"^\d{4}$",
    )

    phone_number: str | None = None
    cell_number: str | None = None

    # Glen Moniques operational requirement.
    email: EmailStr

    province_code: Literal[
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "N",
        "X",
    ]

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

    @model_validator(mode="after")
    def validate_conditional_fields(self):
        if not self.popi_agree:
            raise ValueError(
                "POPIA consent is required to submit an application."
            )

        if (
            self.disability_status != "N"
            and not self.disability_rating
        ):
            raise ValueError(
                "Disability rating is required when a disability "
                "status other than None is selected."
            )

        if (
            self.disability_status == "N"
            and self.disability_rating is not None
        ):
            raise ValueError(
                "Disability rating must be left blank when "
                "disability status is None."
            )

        return self


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(
        min_length=1,
        max_length=50,
    )

    outstanding_documents: list[str] | None = None
