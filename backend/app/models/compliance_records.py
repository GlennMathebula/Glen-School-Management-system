from __future__ import annotations

from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, Field


class AppealCreate(BaseModel):
    registration_id: str
    assessment_scope: str
    mark_id: str | None = None
    summative_assessment_id: str | None = None
    lodged_date: date | None = None
    reason: str


class AppealUpdate(BaseModel):
    status: str | None = None
    outcome: str | None = None


class PlacementCreate(BaseModel):
    registration_id: str
    employer_name: str
    employer_reg_no: str | None = None
    workplace_address: str | None = None
    supervisor_name: str
    supervisor_contact: str | None = None
    supervisor_email: str | None = None
    placement_start_date: date
    placement_end_date: date | None = None
    hours_required: Decimal | None = None
    status: str = "Planned"
    notes: str | None = None


class PlacementUpdate(BaseModel):
    employer_name: str | None = None
    employer_reg_no: str | None = None
    workplace_address: str | None = None
    supervisor_name: str | None = None
    supervisor_contact: str | None = None
    supervisor_email: str | None = None
    placement_start_date: date | None = None
    placement_end_date: date | None = None
    hours_required: Decimal | None = None
    status: str | None = None
    notes: str | None = None


class WorkplaceAttendanceCreate(BaseModel):
    attendance_date: date
    attendance_status: str
    sign_in_time: time | None = None
    sign_out_time: time | None = None
    hours_worked: Decimal | None = None
    supervisor_confirmed: bool = False
    notes: str | None = None


class WeeklySubmissionCreate(BaseModel):
    week_start: date
    week_end: date
    submission_type: str = "Weekly Evidence"
    title: str
    evidence_reference: str | None = None
    learner_comment: str | None = None
    status: str = "Submitted"


class WeeklySubmissionUpdate(BaseModel):
    status: str | None = None
    review_comment: str | None = None
    evidence_reference: str | None = None


class SupervisorReportCreate(BaseModel):
    report_date: date | None = None
    period_start: date | None = None
    period_end: date | None = None
    overall_rating: int | None = Field(default=None, ge=1, le=5)
    attendance_comment: str | None = None
    performance_comment: str | None = None
    conduct_comment: str | None = None
    competencies_comment: str | None = None
    recommendation: str | None = None
    supervisor_name: str
    status: str = "Submitted"


class SupervisorReportUpdate(BaseModel):
    status: str | None = None
    review_comment: str | None = None
    overall_rating: int | None = Field(default=None, ge=1, le=5)
    recommendation: str | None = None


class EisaSittingCreate(BaseModel):
    course_code: str
    cycle_code: str | None = None
    assessment_date: date
    reporting_time: time | None = None
    start_time: time
    end_time: time
    venue: str
    assessment_centre: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    instructions: str | None = None
    status: str = "Draft"


class EisaSittingUpdate(BaseModel):
    assessment_date: date | None = None
    reporting_time: time | None = None
    start_time: time | None = None
    end_time: time | None = None
    venue: str | None = None
    assessment_centre: str | None = None
    capacity: int | None = Field(default=None, gt=0)
    instructions: str | None = None
    status: str | None = None


class EisaCandidateCreate(BaseModel):
    registration_id: str
    seat_number: int | None = Field(default=None, gt=0)
    admission_status: str = "Admitted"
    attendance_status: str = "Pending"
    notes: str | None = None


class EisaCandidateUpdate(BaseModel):
    seat_number: int | None = Field(default=None, gt=0)
    admission_status: str | None = None
    attendance_status: str | None = None
    notes: str | None = None


class CorrectiveActionCreate(BaseModel):
    source_type: str
    source_reference: str | None = None
    cycle_code: str | None = None
    course_code: str | None = None
    class_code: str | None = None
    finding: str
    root_cause: str | None = None
    corrective_action: str
    owner_staff_code: str | None = None
    due_date: date | None = None
    status: str = "Open"
    evidence_reference: str | None = None


class CorrectiveActionUpdate(BaseModel):
    root_cause: str | None = None
    corrective_action: str | None = None
    owner_staff_code: str | None = None
    due_date: date | None = None
    status: str | None = None
    completion_notes: str | None = None
    evidence_reference: str | None = None
