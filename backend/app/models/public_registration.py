from datetime import date

from pydantic import BaseModel, Field


class PublicRegistrationCreate(BaseModel):

    student_number: str = Field(
        min_length=1,
        max_length=30,
    )

    id_or_passport: str = Field(
        min_length=1,
        max_length=50,
    )

    first_name: str = Field(
        min_length=1,
        max_length=100,
    )

    second_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str = Field(
        min_length=1,
        max_length=100,
    )

    birth_date: date