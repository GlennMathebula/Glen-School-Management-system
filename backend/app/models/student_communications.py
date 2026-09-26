from typing import Literal

from pydantic import (
    BaseModel,
    Field,
)

MessageCategory = Literal[
    "Academic",
    "Finance",
    "Documents",
    "Assessment",
    "Timetable",
    "TechnicalSupport",
    "General",
]


class StudentMessageCreate(
    BaseModel
):

    subject: str = Field(
        ...,
        min_length=3,
        max_length=200,
    )

    category: MessageCategory

    message: str = Field(
        ...,
        min_length=2,
        max_length=5000,
    )


class StudentMessageReply(
    BaseModel
):

    message: str = Field(
        ...,
        min_length=2,
        max_length=5000,
    )