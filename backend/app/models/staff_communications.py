from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================
# SHARED TYPES
# ============================================================

StaffMessageCategory = Literal[
    "General",
    "Academic",
    "Assessment",
    "Timetable",
    "Finance",
    "Documents",
    "HR",
    "TechnicalSupport",
]

StaffSupportCategory = Literal[
    "SystemAccess",
    "Login",
    "PasswordPIN",
    "Portal",
    "AcademicSystem",
    "FinanceSystem",
    "HRSystem",
    "Documents",
    "TechnicalError",
    "Other",
]

PriorityType = Literal[
    "Normal",
    "High",
    "Urgent",
]

AnnouncementPriority = Literal[
    "Normal",
    "Important",
    "Urgent",
]

AnnouncementType = Literal[
    "General",
    "Academic",
    "Assessment",
    "Timetable",
    "Finance",
    "Documents",
    "Emergency",
]

AnnouncementAudience = Literal[
    "AllStudents",
    "Course",
    "Cycle",
    "Class",
    "IndividualStudent",
]


# ============================================================
# STAFF MESSAGE - CREATE THREAD
# ============================================================

class StaffMessageThreadCreate(
    BaseModel
):

    recipient_staff_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )

    subject: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    category: StaffMessageCategory = (
        "General"
    )

    message_body: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


# ============================================================
# STAFF MESSAGE - REPLY
# ============================================================

class StaffMessageReplyCreate(
    BaseModel
):

    message_body: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


# ============================================================
# STAFF MESSAGE - STATUS UPDATE
# ============================================================

class StaffMessageThreadStatusUpdate(
    BaseModel
):

    status: Literal[
        "Open",
        "Closed",
    ]


# ============================================================
# STAFF SUPPORT - CREATE TICKET
# ============================================================

class StaffSupportTicketCreate(
    BaseModel
):

    category: StaffSupportCategory

    subject: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )

    priority: PriorityType = (
        "Normal"
    )


# ============================================================
# STAFF SUPPORT - REPLY
# ============================================================

class StaffSupportReplyCreate(
    BaseModel
):

    message_body: str = Field(
        ...,
        min_length=1,
        max_length=10000,
    )


# ============================================================
# STAFF SUPPORT - STATUS UPDATE
# ============================================================

class StaffSupportStatusUpdate(
    BaseModel
):

    status: Literal[
        "Open",
        "InProgress",
        "AwaitingStaff",
        "Resolved",
        "Closed",
    ]

    resolution_notes: str | None = Field(
        default=None,
        max_length=10000,
    )


# ============================================================
# STAFF ANNOUNCEMENT - CREATE
# ============================================================

class StaffAnnouncementCreate(
    BaseModel
):

    title: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=20000,
    )

    announcement_type: AnnouncementType = (
        "General"
    )

    priority: AnnouncementPriority = (
        "Normal"
    )

    audience_type: AnnouncementAudience = (
        "AllStudents"
    )

    course_code: str | None = Field(
        default=None,
        max_length=50,
    )

    cycle_code: str | None = Field(
        default=None,
        max_length=50,
    )

    class_id: str | None = None

    student_number: str | None = Field(
        default=None,
        max_length=50,
    )

    expires_at: datetime | None = None


# ============================================================
# STAFF ANNOUNCEMENT - UPDATE DRAFT
# ============================================================

class StaffAnnouncementUpdate(
    BaseModel
):

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )

    message: str | None = Field(
        default=None,
        min_length=1,
        max_length=20000,
    )

    announcement_type: (
        AnnouncementType
        | None
    ) = None

    priority: (
        AnnouncementPriority
        | None
    ) = None

    audience_type: (
        AnnouncementAudience
        | None
    ) = None

    course_code: str | None = Field(
        default=None,
        max_length=50,
    )

    cycle_code: str | None = Field(
        default=None,
        max_length=50,
    )

    class_id: str | None = None

    student_number: str | None = Field(
        default=None,
        max_length=50,
    )

    expires_at: datetime | None = None