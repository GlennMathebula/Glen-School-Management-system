from typing import Literal

from pydantic import BaseModel, Field


AttendanceStatus = Literal[
    "Present",
    "Absent",
    "Late",
    "Excused",
]


class FacilitatorAttendanceRecord(BaseModel):

    registration_id: str

    attendance_status: AttendanceStatus

    minutes_late: int | None = Field(
        default=None,
        ge=0,
    )

    notes: str | None = Field(
        default=None,
        max_length=1000,
    )


class FacilitatorAttendanceCaptureRequest(
    BaseModel
):

    records: list[
        FacilitatorAttendanceRecord
    ]