from typing import Literal

from pydantic import BaseModel, Field

AttendanceStatus = Literal[
    "Present",
    "Absent",
    "Late",
    "Excused",
]


class WeeklyAttendanceRecordCapture(
    BaseModel
):

    register_day_id: str

    registration_id: str

    attendance_status: AttendanceStatus

    sign_in_time: str | None = None

    sign_out_time: str | None = None

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class WeeklyAttendanceCaptureRequest(
    BaseModel
):

    control_number: str = Field(
        min_length=1,
        max_length=30,
    )

    captured_by: str = Field(
        min_length=1,
        max_length=50,
    )

    records: list[
        WeeklyAttendanceRecordCapture
    ]


class WeeklyAttendanceVerifyRequest(
    BaseModel
):

    control_number: str = Field(
        min_length=1,
        max_length=30,
    )

    verified_by: str = Field(
        min_length=1,
        max_length=50,
    )