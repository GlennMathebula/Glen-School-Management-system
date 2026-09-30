from datetime import date

from pydantic import BaseModel, Field


class CycleCreateRequest(BaseModel):
    cycle_code: str = Field(
        min_length=1,
        max_length=100,
    )
    cycle_name: str | None = None
    application_start_date: date | None = None
    application_end_date: date | None = None
    registration_start_date: date | None = None
    registration_end_date: date | None = None
    program_start_date: date
    expected_completion_date: date | None = None
    cipc_required: bool = False
    status: str = "Draft"


class CycleUpdateRequest(BaseModel):
    cycle_name: str | None = None
    application_start_date: date | None = None
    application_end_date: date | None = None
    registration_start_date: date | None = None
    registration_end_date: date | None = None
    program_start_date: date | None = None
    expected_completion_date: date | None = None
    cipc_required: bool | None = None


class CycleStatusRequest(BaseModel):
    status: str


class CycleCourseStatusRequest(BaseModel):
    is_active: bool = True


class ClassCreateRequest(BaseModel):
    class_code: str = Field(
        min_length=1,
        max_length=100,
    )
    class_name: str | None = None
    course_code: str = Field(
        min_length=1,
        max_length=100,
    )
    cycle_code: str = Field(
        min_length=1,
        max_length=100,
    )
    class_group: str | None = None
    facilitator_code: str | None = None
    assessor_code: str | None = None
    status: str = "Draft"


class ClassUpdateRequest(BaseModel):
    class_name: str | None = None
    course_code: str | None = None
    cycle_code: str | None = None
    class_group: str | None = None
    status: str | None = None


class ClassStaffAssignmentRequest(BaseModel):
    facilitator_code: str | None = None
    assessor_code: str | None = None


class ClassEnrolmentRequest(BaseModel):
    registration_id: str = Field(
        min_length=1,
    )

