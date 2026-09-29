from decimal import Decimal

from pydantic import (
    BaseModel,
    Field,
)


# ============================================================
# MODULE MARKS
# ============================================================

class ModuleMarkCaptureRequest(BaseModel):

    module_registration_id: str

    attempt_number: int = Field(
        default=1,
        ge=1,
    )

    mark: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    grade: str | None = Field(
        default=None,
        max_length=30,
    )

    semester: str | None = Field(
        default=None,
        max_length=30,
    )

    academic_year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
    )

    result: str | None = Field(
        default=None,
        max_length=40,
    )


class ModuleMarkUpdateRequest(BaseModel):

    mark: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    grade: str | None = Field(
        default=None,
        max_length=30,
    )

    semester: str | None = Field(
        default=None,
        max_length=30,
    )

    academic_year: int | None = Field(
        default=None,
        ge=2000,
        le=2100,
    )

    result: str | None = Field(
        default=None,
        max_length=40,
    )


# ============================================================
# SUMMATIVE ASSESSMENTS
# ============================================================

class SummativeAssessmentCaptureRequest(BaseModel):

    registration_id: str

    assessment_type: str = Field(
        min_length=4,
        max_length=10,
    )

    attempt_number: int = Field(
        default=1,
        ge=1,
    )

    mark: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    assessment_date: str | None = None

    result: str | None = Field(
        default=None,
        max_length=40,
    )


class SummativeAssessmentUpdateRequest(BaseModel):

    mark: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    assessment_date: str | None = None

    result: str | None = Field(
        default=None,
        max_length=40,
    )


# ============================================================
# MODERATION
# ============================================================

class ModerationReturnRequest(BaseModel):

    return_reason: str = Field(
        min_length=3,
        max_length=2000,
    )