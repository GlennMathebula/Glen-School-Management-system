from typing import Literal

from pydantic import BaseModel, Field

AttendanceStatus = Literal[
    "Present",
    "Absent",
    "Late",
    "Excused",
]


class AttendanceRecordCapture(
    BaseModel
):

    registration_id: str

    attendance_status: (
        AttendanceStatus
    )

    minutes_late: (
        int | None
    ) = Field(
        default=None,
        ge=0,
    )

    notes: (
        str | None
    ) = Field(
        default=None,
        max_length=1000,
    )


class AttendanceBulkCapture(
    BaseModel
):

    timetable_session_id: str

    captured_by: str = Field(
        min_length=1,
        max_length=50,
    )

    records: list[
        AttendanceRecordCapture
    ]


class AttendanceSubmit(
    BaseModel
):

    submitted_by: str = Field(
        min_length=1,
        max_length=50,
    )


class AttendanceRender(
    BaseModel
):

    rendered_by: str = Field(
        min_length=1,
        max_length=50,
    )


class AttendanceReturn(
    BaseModel
):

    returned_by: str = Field(
        min_length=1,
        max_length=50,
    )

    reason: str = Field(
        min_length=1,
        max_length=2000,
    )