from datetime import datetime

from pydantic import BaseModel, Field


class StaffMessageThreadCreate(BaseModel):
    recipient_staff_code: str = Field(
        min_length=1,
        max_length=50,
    )
    subject: str = Field(
        min_length=1,
        max_length=255,
    )
    category: str = Field(
        default="General",
        min_length=1,
        max_length=50,
    )
    message_body: str = Field(
        min_length=1,
        max_length=10000,
    )


class StaffMessageReply(BaseModel):
    message_body: str = Field(
        min_length=1,
        max_length=10000,
    )


class StudentMessageStaffReply(BaseModel):
    message_body: str = Field(
        min_length=1,
        max_length=10000,
    )


class StaffAnnouncementCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )
    message: str = Field(
        min_length=1,
        max_length=20000,
    )
    announcement_type: str = "General"
    priority: str = "Normal"
    audience_type: str = "AllStudents"
    course_code: str | None = None
    cycle_code: str | None = None
    class_id: str | None = None
    student_number: str | None = None
    expires_at: datetime | None = None

